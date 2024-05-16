from typing import Optional, Union
from pydantic import BaseModel, field_validator


class ClientData(BaseModel):
    id: Union[str, int]
    full_name: Optional[Union[str, None]] = None
    profile_image: Optional[Union[str, None]] = None

    @field_validator('id')
    def convert_to_string(cls, value):
        if not isinstance(value, str):
            return str(value)
