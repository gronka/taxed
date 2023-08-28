from sqlalchemy import BigInteger, Boolean, Column
from sqlalchemy.dialects.postgresql import UUID
from typing import cast

from taxed.core.model_generics import Base, NonNullString, TimesMixin
from taxed.core import (
    # Base,
    in_x_days,
    # NonNullString,
    nowstamp,
    Puid,
    # TimesMixin,
)


class SurferSession(Base, TimesMixin):
    __tablename__ = 'surfer_sessions'
    instance_id = cast(str, Column(NonNullString,
                                   nullable=False,
                                   primary_key=True))
    surfer_id = cast(Puid, Column(UUID(as_uuid=True),
                                  nullable=False,
                                  ))
    is_apple_session = cast(bool, Column(Boolean, nullable=False))
    is_google_session = cast(bool, Column(Boolean, nullable=False))
    jwt_long = cast(str, Column(NonNullString, nullable=False))
    platform = cast(str, Column(NonNullString, nullable=False))
    refresh_token_apple = cast(str, Column(NonNullString, nullable=False))

    time_expires = cast(int, Column(BigInteger,
                                    nullable=False,
                                    default=nowstamp,
                                    ))
    time_last_used = cast(int, Column(BigInteger,
                                      nullable=False,
                                      default=nowstamp,
                                      ))
    time_next_24h_check = cast(int, Column(BigInteger,
                                           nullable=False,
                                           default=nowstamp,
                                           ))

    def as_dict(self):
        return {
            **self.time_dict(),
            'instance_id': self.instance_id,
            'surfer_id': self.surfer_id,
            'platform': self.platform,
            'time_expires': self.time_expires,
            'time_last_used': self.time_last_used,
        }

    def needs_24_check(self):
        if (nowstamp() - self.time_next_24h_check) > 0:
            return True
        return False

    def set_next_24h_check(self):
        self.time_next_24h_check = in_x_days(1).timestamp()

    def get_client_id(self):
        if self.is_google_session == 'io.fairlytaxed.and':
            return 'io.fairlytaxed.and'
        elif self.is_apple_session == 'io.fairlytaxed.ios':
            return 'io.fairlytaxed.ios'
        else:
            return ''
