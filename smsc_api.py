import dataclasses
import logging

import asks
import trio
import environs

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Config:
    login: str
    password: str
    phones: tuple[str]
    message: str
    lifetime: int
    cost: int
    answer_format: int


def read_config():
    login = env.str("SMSC_LOGIN")
    password = env.str("SMSC_PASSWORD")
    phones = env.list("PHONES")
    message = env.str("MESSAGE")
    lifetime = env.str("SMS_LIFETIME", 1)
    only_show_cost = env.bool("ONLY_SHOW_COST", True)
    cost = 1 if only_show_cost else None
    answer_format = env.int("ANSWER_FORMAT", 3)
    config = Config(login=login, password=password, phones=phones, message=message, lifetime=lifetime, cost=cost,
                    answer_format=answer_format)
    logger.debug("red config")
    return config


class SmscApiSms:
    def __init__(self, config):
        self.login = config.login
        self.psw = config.password
        self.phones = ",".join(config.phones)
        self.mes = config.message
        self.valid = config.lifetime
        self.cost = config.cost
        self.fmt = config.answer_format

        self.sms_sent = False
        self.sms_sent_status = None
        self.sms_id = None
        self.sms_delivery_status = None

        self.send_params = {
            "login": config.login,
            "psw": config.password,
            "phones": ','.join(config.phones),
            "mes": config.message,
            "valid": config.lifetime,
            "cost": config.cost,
            "fmt": config.answer_format,
        }

        self.status_params = {
            "login": config.login,
            "psw": config.password,
            "phone": ",".join(config.phones),
            "id": None,
            "fmt": config.answer_format
        }

    async def send(self):
        logger.debug("try to send sms")
        response = await asks.get("https://smsc.ru/sys/send.php", params=self.send_params)
        if response.status_code == 200:
            self.sms_sent_status = response.json()  # now works only with fmt=3
            if "id" in self.sms_sent_status:
                self.sms_sent = True
                self.sms_id = self.sms_sent_status["id"]
                logger.info(f"sms sent (id={self.sms_id})")
            else:
                logger.warning(f"sms not sent (answer={self.sms_sent_status})")
            return
        logger.warning(f"sms not sent (status_code={response.status_code}, answer={response.text})")

    async def get_delivery_status(self):
        logger.debug("try to get sms status")
        if not self.sms_sent:
            logger.debug("sms wasn't sent")
            return {"status": -1000}
        self.status_params["id"] = self.sms_id

        response = await asks.get("https://smsc.ru/sys/status.php", params=self.status_params)
        if response.status_code == 200:
            self.sms_delivery_status = response.json()  # now works only with fmt=3
            logger.info(f"got delivery status (answer={self.sms_delivery_status})")
            return self.sms_delivery_status
        logger.warning(f"error while getting sms status (status_code={response.status_code}, answer={response.text})")


async def main():
    config = read_config()
    sms = SmscApiSms(config)
    await sms.send()
    delivery_status = await sms.get_delivery_status()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    env = environs.Env()
    env.read_env()
    trio.run(main)
