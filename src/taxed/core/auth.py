from datetime import datetime, timedelta, timezone
from jose import jwt
from random import choices
from string import ascii_letters, digits
from typing import Optional, Union
import uuid

from taxed.core.dates import nowstamp
from taxed.state import conf

Puid = Union[str, uuid.UUID]  # redefined due to collisions

def random_token(length = 24) -> str:
    return ''.join(choices(ascii_letters + digits, k=length))

def create_jwt_short(to_encode: dict, expires_delta: Optional[timedelta] = None):
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + \
            timedelta(minutes=conf.jwt_short_lifetime_minutes,
                      seconds=conf.jwt_short_lifetime_seconds)
    to_encode.update({'exp': expire.timestamp()})
    return jwt.encode(to_encode,
                      conf.jwt_short_secret_key,
                      algorithm=conf.jwt_algorithm)


def create_jwt_long(to_encode: dict):
    expire = datetime.now(timezone.utc) + \
        timedelta(days=conf.jwt_long_lifetime_days)
    to_encode.update({'exp': expire.timestamp()})
    return jwt.encode(to_encode,
                      conf.jwt_long_secret_key,
                      algorithm=conf.jwt_algorithm)


def decode_jwt_short(jwt_short: str) -> dict:
    decoded = ''
    try:
        decoded = jwt.decode(jwt_short,
                             conf.jwt_short_secret_key,
                             algorithms=conf.jwt_algorithms)
    except Exception as err:
        print(err)
    return decoded if decoded else {}


def decode_jwt_long(jwt_long: str) -> dict:
    decoded = ''
    try:
        decoded = jwt.decode(jwt_long,
                             conf.jwt_long_secret_key,
                             algorithms=conf.jwt_algorithms)
    except Exception as err:
        print(err)
    return decoded if decoded else {}


def is_jwt_expired(exp: int) -> bool:
    return nowstamp() > exp


def create_developer_jwt_short(developer_id: Puid) -> str:
    to_encode = { 'DeveloperId': str(developer_id) }
    return create_jwt_short(to_encode, expires_delta=timedelta(days=1))


def create_surfer_jwt_short(surfer_id: Puid) -> str:
    to_encode = { 'SurferId': str(surfer_id) }
    return create_jwt_short(to_encode)


def create_surfer_jwt_long(surfer_id: Puid, instance_id: str) -> str:
    to_encode = {
        'SurferId': str(surfer_id),
        'InstanceId': instance_id,
    }
    return create_jwt_long(to_encode)
