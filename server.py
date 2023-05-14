import contextvars
import logging
import unittest.mock

import pydantic
import quart
import quart_trio

import smsc_api
from settings import settings
import models

app = quart_trio.QuartTrio(__name__, template_folder="frontend")
logger = logging.getLogger(__name__)


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
    except smsc_api.SmscApiError as e:
        return {"errorMessage": e.args}, 400
    except pydantic.ValidationError as e:
        return {"errorMessage": str(e.errors())}, 400
    return {'message': response}


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    smsc_login = contextvars.ContextVar('login', default=settings.smsc_login)
    smsc_password = contextvars.ContextVar('password', default=settings.smsc_password)
    app.run()
