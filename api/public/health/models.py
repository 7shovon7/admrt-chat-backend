from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel


class Status(str, Enum):
    OK = "OK"
    KO = "KO"


class Health(BaseModel):
    app_status: Union[Status, None] = None
    db_status: Union[Status, None] = None
    environment: Union[Literal["development", "staging", "production"], None] = None


class Stats(BaseModel):
    heroes: Union[int, None] = None
    teams: Union[int, None] = None
