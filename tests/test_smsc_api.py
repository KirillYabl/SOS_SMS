import pytest

import smsc_api
from settings import settings


@pytest.mark.asyncio
async def test_smsc_api_no_phones():
    send_payload = {
        "mes": settings.message,
        "valid": settings.lifetime,
        "cost": settings.cost,
        "fmt": settings.answer_format,
    }

    with pytest.raises(smsc_api.SmscApiError):
        await smsc_api.request_smsc(
            "POST",
            "send",
            login=settings.smsc_login,
            password=settings.smsc_password,
            payload=send_payload
        )


@pytest.mark.asyncio
async def test_smsc_api_wrong_api_method():
    send_payload = {
        "phones": settings.phones,
        "mes": settings.message,
        "valid": settings.lifetime,
        "cost": settings.cost,
        "fmt": settings.answer_format,
    }

    with pytest.raises(smsc_api.SmscApiError):
        await smsc_api.request_smsc(
            "POST",
            "notexist",
            login=settings.smsc_login,
            password=settings.smsc_password,
            payload=send_payload
        )
