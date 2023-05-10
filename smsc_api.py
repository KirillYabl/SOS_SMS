import dataclasses

import asks
import trio
import environs


@dataclasses.dataclass
class Config:
    login: str
    password: str
    phones: tuple[str]
    message: str
    lifetime: int
    cost: int


# @click.command()
# @click.option("--login", envvar="SMSC_LOGIN", required=True)
# @click.option("--password", envvar="SMSC_PASSWORD", required=True)
# @click.option("--phones", envvar="PHONES", multiple=True, required=True)
# @click.option("--message", envvar="MESSAGE", required=True)
# @click.option("--lifetime", envvar="SMS_LIFETIME", default=1)
def read_config():
    login = env.str('SMSC_LOGIN')
    password = env.str('SMSC_PASSWORD')
    phones = env.list('PHONES')
    message = env.str('MESSAGE')
    lifetime = env.str('SMS_LIFETIME', 1)
    only_show_cost = env.bool('ONLY_SHOW_COST', True)
    cost = 1 if only_show_cost else None
    config = Config(login=login, password=password, phones=phones, message=message, lifetime=lifetime, cost=cost)
    return config


async def send_sms(config):
    params = {
        "login": config.login,
        "psw": config.password,
        "phones": ','.join(config.phones),
        "mes": config.message,
        "valid": config.lifetime,
        "cost": config.cost,
    }
    response = await asks.get("https://smsc.ru/sys/send.php", params=params)
    return response.status_code


async def main():
    config = read_config()
    status_code = await send_sms(config)


if __name__ == '__main__':
    env = environs.Env()
    env.read_env()
    trio.run(main)
