import pytest
import unittest.mock

import smsc_api


@pytest.mark.trio
async def test_smsc_api_no_phones(config):
    send_payload = {
        "mes": config["message"],
        "valid": config["lifetime"],
        "cost": config["cost"],
        "fmt": config["answer_format"],
    }

    with pytest.raises(smsc_api.SmscApiError):
        await smsc_api.request_smsc(
            "POST",
            "send",
            login=config["smsc_login"],
            password=config["smsc_password"],
            payload=send_payload
        )


@pytest.mark.trio
async def test_smsc_api_wrong_api_method(config):
    send_payload = {
        "phones": config["phones"],
        "mes": config["message"],
        "valid": config["lifetime"],
        "cost": config["cost"],
        "fmt": config["answer_format"],
    }

    with pytest.raises(smsc_api.SmscApiError):
        await smsc_api.request_smsc(
            "POST",
            "notexist",
            login=config["smsc_login"],
            password=config["smsc_password"],
            payload=send_payload
        )
