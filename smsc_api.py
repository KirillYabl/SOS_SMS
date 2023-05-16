import asyncio
import contextvars
import logging
import typing
import unittest.mock

import asks

from settings import settings

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


async def main():
    logger.debug("red config")

    send_payload = {
        "phones": settings.phones,
        "mes": settings.message,
        "valid": settings.lifetime,
        "cost": settings.cost,
        "fmt": settings.answer_format,
    }
    with unittest.mock.patch("__main__.request_smsc") as mock:
        mock.return_value = {
            "id": 302,
            "cnt": 1,
        }
        send_status = await request_smsc("POST", "send", payload=send_payload)

    status_payload = {
        "phone": settings.phones,
        "fmt": settings.answer_format
    }
    if send_status and "id" in send_status:
        status_payload["id"] = send_status["id"]

    with unittest.mock.patch("__main__.request_smsc") as mock:
        mock.return_value = {
            "status": 1,
            "last_date": "12.05.2023 14:19:10",
            "last_timestamp": 1683911950,
        }
        delivery_status = await request_smsc("GET", "status", payload=status_payload)
        logger.debug(delivery_status)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    smsc_login = contextvars.ContextVar('login', default=settings.smsc_login)
    smsc_password = contextvars.ContextVar('password', default=settings.smsc_password)
    asyncio.run(main())
