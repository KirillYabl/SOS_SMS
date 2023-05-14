import pydantic


class Message(pydantic.BaseModel):
    text: pydantic.constr(min_length=1)
