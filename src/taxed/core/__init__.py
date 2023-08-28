from .auth import (
    create_developer_jwt_short,
    create_jwt_long,
    create_jwt_short,
    decode_jwt_long,
    decode_jwt_short,
    create_surfer_jwt_long,
    create_surfer_jwt_short,
    random_token,
)
from .database import db_commit, get_db, SessionLocal

from .dates import (
    date_from_period,
    get_period_now,
    in_x_days,
    in_x_hours,
    in_x_minutes,
    in_x_months,
    make_next_period,
    make_previous_period,
    now,
    nowstamp,
    period_from_date,
    period_from_ym,
    timestamps_from_period,
    timestamps_from_ym,
)

from .etl import set_optional

from .generics import (
    ApiSchema,
    ApiError,
    CollectionSchema,
    EmptySchema,
    JwtRefreshOut,
    Puid,
    RequestChangeSchema,
    SessionJwtIn,
    StatusSchema,
    SurferIdIn,
    ZEROS_UUID_STR,
    TWOS_UUID_STR,
    NINES_UUID_STR,
)

from .gibs import Gibs
from .math import ceildiv
from .mailer import (
    make_mailer, 
    Mailer, 
    send_email_simple, 
    send_email_with_attachments,
)
from .model_generics import (
    Base,
    NonNullBigInt,
    NonNullBool,
    NonNullInt,
    NonNullString,
    TimesMixin,
)
from .plogger import plog
from .policy import Policies, PolicyChain, policy_fails
from .response_builder import ResponseBuilder
from .surfer_session import SurferSession


class ChallengeIdIn(ApiSchema):
    ChallengeId: Puid

class ComparableIdIn(ApiSchema):
    ComparableId: Puid

class EmailIn(ApiSchema):
    Email: str

class PaymentIdIn(ApiSchema):
    PaymentId: Puid

class ProbiusIdIn(ApiSchema):
    ProbiusId: Puid

class ProjectIdIn(ApiSchema):
    ProjectId: Puid

class PropertyIdIn(ApiSchema):
    PropertyId: Puid

def puid_equals(a, b):
    return str(a) == str(b)

class RequestChangeSchema(ApiSchema):
    IsConsumed: bool
    SurferId: Puid
    TimeExpires: int

class SuccessOut(EmptySchema):
    Success: bool

class TokenIn(EmptySchema):
    Token: str
