import typing

import pydantic


class Settings(pydantic.BaseSettings):
    smsc_login: str
    smsc_password: str
    phones: str
    message: str
    lifetime: typing.Optional[int] = 1
    only_show_cost: typing.Optional[bool] = True
    cost: typing.Optional[int] = None
    answer_format: typing.Optional[int] = 3

    @pydantic.validator("cost", always=True)
    def calculate_cost(cls, value, values):
        if values["only_show_cost"]:
            return 1
        return None

    class Config:
        env_file = '.env'


settings = Settings()
