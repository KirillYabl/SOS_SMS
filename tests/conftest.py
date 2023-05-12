import environs

import pytest

env = environs.Env()
env.read_env()


@pytest.fixture
def config():
    return {
        "smsc_login": env.str("SMSC_LOGIN"),
        "smsc_password": env.str("SMSC_PASSWORD"),
        "phones": ','.join(env.list("PHONES")),
        "message": env.str("MESSAGE"),
        "lifetime": env.str("SMS_LIFETIME", 1),
        "cost": 1 if env.bool("ONLY_SHOW_COST", True) else None,
        "answer_format": env.int("ANSWER_FORMAT", 3),
    }
