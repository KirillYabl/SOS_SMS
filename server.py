import asyncio
import contextvars
import logging
import unittest.mock
import time

import pydantic
import quart
import redis.asyncio

import smsc_api
from settings import settings
import models
import db

# app = quart_trio.QuartTrio(__name__, template_folder="frontend")
app = quart.Quart(__name__, template_folder="frontend")
logger = logging.getLogger(__name__)


@app.before_serving
async def create_db():
    app.db = db.Database(redis_connection)


@app.route("/")
async def index():
    return await quart.render_template("index.html")


@app.route("/send/", methods=["POST"])
async def create():
    try:
        form = await quart.request.form
        message = models.Message(**form)
        with unittest.mock.patch('smsc_api.request_smsc') as mock:
            mock.return_value = {
                'id': 302,
                'cnt': 1
            }
            send_payload = {
                "phones": settings.phones,
                "mes": message.text,
                "valid": settings.lifetime,
                "cost": settings.cost,
                "fmt": settings.answer_format,
            }
            response = await smsc_api.request_smsc(
                "POST",
                "send",
                payload=send_payload
            )
            sms_id = response['id']

            await app.db.add_sms_mailing(
                sms_id,
                settings.phones.split(),
                message.text
            )
    except smsc_api.SmscApiError as e:
        return {"errorMessage": e.args}, 400
    except pydantic.ValidationError as e:
        return {"errorMessage": str(e.errors())}, 400

    return {'message': response}


@app.websocket("/ws")
async def ws():
    while True:
        sms_mailing_ids = await app.db.list_sms_mailings()
        sms_mailings = await app.db.get_sms_mailings(*sms_mailing_ids)
        answer = {
            "msgType": "SMSMailingStatus",
            "SMSMailings": [
                {
                    "timestamp": time.time(),
                    "SMSText": sms_mailing["text"],
                    "mailingId": str(sms_mailing["sms_id"]),
                    "totalSMSAmount": sms_mailing["phones_count"],
                    "deliveredSMSAmount": len({
                        phone: status
                        for phone, status
                        in sms_mailing["phones"].items()
                        if status == "delivered"
                    }),
                    "failedSMSAmount": len({
                        phone: status
                        for phone, status
                        in sms_mailing["phones"].items()
                        if status == "failed"
                    }),
                }
                for sms_mailing
                in sms_mailings
            ]
        }
        await quart.websocket.send_json(answer)
        await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    smsc_login = contextvars.ContextVar('login', default=settings.smsc_login)
    smsc_password = contextvars.ContextVar('password', default=settings.smsc_password)
    redis_connection = redis.asyncio.from_url(settings.redis_url, decode_responses=True)
    app.run()
