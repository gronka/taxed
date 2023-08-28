from pydantic import BaseModel
from typing import List, Optional, Union
import uuid


Puid = Union[str, uuid.UUID]

ZEROS_UUID_STR = '00000000-0000-0000-0000-000000000000'
TWOS_UUID_STR =  '22222222-2222-2222-2222-222222222222'
NINES_UUID_STR = '99999999-9999-9999-9999-999999999999'

def to_go_case(x: str) -> str:
    return x.capitalize()

class ApiSchema(BaseModel):
    NewJwtShort: Optional[str] = None

    class Config:
        pass
        # case_sensitive = False
        # allow_population_by_field_name = True
        # alias_generator = to_go_case
        # orm_mode = True

class EmptySchema(BaseModel): pass

class StatusSchema(ApiSchema):
    Status: str
    StatusCode: int

class CollectionSchema(ApiSchema):
    collection: List[Optional[str]]

class ApiError:
    def __init__(self, code: str, msg: str):
        self._code = code
        self._msg = msg

    def append_to_msg(self, more: str):
        self._msg = f'{self._msg} {more}'

    def to_dict(self):
        return {'code': self._code, 'msg': self._msg}

    def copy(self):
        return ApiError(self._code, self._msg)

class JwtRefreshOut(ApiSchema):
    NewJwt: str

class SessionJwtIn(ApiSchema):
    SessionJwt: str

class SurferIdIn(ApiSchema):
    SurferId: Puid

class RequestChangeSchema(ApiSchema):
    SurferId: Puid = ''
    IsConsumed: bool
    TimeExpires: int
