import contextvars
import logging
import typing

import asks
import trio
import environs

logger = logging.getLogger(__name__)


class SmscApiError(KeyError):
    """Error while working with SMSC API."""
    pass


async def request_smsc(
        http_method: str,
        api_method: str,
        *,
        login: typing.Optional[str] = None,
        password: typing.Optional[str] = None,
        payload: typing.Optional[dict] = None,
) -> dict:
    """Send request to SMSC.ru service.

    Args:
        http_method (str): E.g. 'GET' or 'POST'.
        api_method (str): E.g. 'send' or 'status'.
        login (str): Login for account on smsc.ru.
        password (str): Password for account on smsc.ru.
        payload (dict): Additional request params, override default ones.
    Returns:
        dict: Response from smsc.ru API.
    Raises:
        SmscApiError: If smsc.ru API response status is not 200 or JSON response
        has "error_code" inside.

    Examples:
        await request_smsc(
        ...   'POST',
        ...   'send',
        ...   login='smsc_login',
        ...   password='smsc_password',
        ...   payload={'phones': '+79123456789'}
        ... )
        {'cnt': 1, 'id': 24}

        await request_smsc(
        ...   'GET',
        ...   'status',
        ...   login='smsc_login',
        ...   password='smsc_password',
        ...   payload={
        ...     'phone': '+79123456789',
        ...     'id': '24',
        ...   }
        ... )
        {'status': 1, 'last_date': '28.12.2019 19:20:22', 'last_timestamp': 1577550022}
    """
    logger.debug(f"try to request {api_method} method")

    if not payload:
        payload = {}

    login = login or smsc_login.get()
    password = password or smsc_password.get()
    payload["login"] = login
    payload["psw"] = password

    response = await asks.request(http_method, f"https://smsc.ru/sys/{api_method}.php", params=payload)

    if response.status_code != 200:
        raise SmscApiError(f"got status_code={response.status_code} ({response.text})")
    serialized_response = response.json()
    if "error_code" in serialized_response:
        raise SmscApiError(f"get error_code in response ({serialized_response})")

    logger.debug(f"method completed, result - {serialized_response}")
    return serialized_response


async def main(env):
    phones = ','.join(env.list("PHONES"))
    message = env.str("MESSAGE")
    lifetime = env.str("SMS_LIFETIME", 1)
    only_show_cost = env.bool("ONLY_SHOW_COST", True)
    cost = 1 if only_show_cost else None
    answer_format = env.int("ANSWER_FORMAT", 3)
    logger.debug("red config")

    send_payload = {
        "phones": phones,
        "mes": message,
        "valid": lifetime,
        "cost": cost,
        "fmt": answer_format,
    }
    send_status = await request_smsc("POST", "send", payload=send_payload)

    status_payload = {
        "phone": phones,
        "fmt": answer_format
    }
    if send_status and "id" in send_status:
        status_payload["id"] = send_status["id"]
    delivery_status = await request_smsc("GET", "status", payload=status_payload)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    env = environs.Env()
    env.read_env()
    smsc_login = contextvars.ContextVar('login', default=env.str("SMSC_LOGIN"))
    smsc_password = contextvars.ContextVar('password', default=env.str("SMSC_PASSWORD"))
    trio.run(main, env)
