from typing import Optional, Union
from pydantic import BaseModel, field_validator


# UserModel
class UserBase(BaseModel):
    id: Union[str, int]
    full_name: Optional[Union[str, None]] = None
    profile_image: Optional[Union[str, None]] = None

    @field_validator('id')
    def convert_to_string(cls, value):
        return str(value)
    
    # def update(self, **new_data):
    #     for field, value in new_data.items():
    #         setattr(self, field, value)


class UserDBModel(UserBase):

    # class Config:
    #     from_attributes: bool = True
    pass


class UserCreate(UserBase):
    pass


class UserUpdate(UserBase):
    pass


class UserRead(UserBase):
    pass
