from sqlalchemy import BigInteger, Boolean, Column
from sqlalchemy.dialects.postgresql import UUID
from typing import cast

from taxed.core import Puid
from taxed.core import (
    Base,
    NonNullString,
    Puid,
    TimesMixin,
)


class Surfer(Base, TimesMixin):
    __tablename__ = 'surfers'
    surfer_id = cast(Puid, Column(UUID(as_uuid=True),
                                  primary_key=True,
                                  nullable=False,
                                  unique=True,
                                  ))
    project_id = cast(Puid, Column(UUID(as_uuid=True)))
    email = cast(str, Column(NonNullString, nullable=False))
    google_id = cast(str, Column(NonNullString, default=''))
    is_admin = cast(bool, Column(Boolean, nullable=False))
    is_email_verified = cast(bool, Column(Boolean, nullable=False))
    is_phone_verified = cast(bool, Column(Boolean, nullable=False))
    password = cast(str, Column(NonNullString, nullable=False))

    email_confirm_token = cast(str, Column(NonNullString))
    first_name = cast(str, Column(NonNullString))
    last_name = cast(str, Column(NonNullString))
    phone = cast(str, Column(NonNullString))

    def full_name(self):
        # .lower().title() might be good
        return f'{self.first_name} {self.last_name}'

    def as_dict(self):
        return {
            **self.time_dict(),
            'SurferId': self.surfer_id,
            'ProjectId': self.project_id,
            'Email': self.email,
            'Phone': self.phone,
            
            'FirstName': self.first_name,
            'LastName': self.last_name,

            'IsEmailVerified': self.is_email_verified,
            'IsPhoneVerified': self.is_phone_verified,
        }


class SurferChangeEmailRequest(Base, TimesMixin):
    __tablename__ = 'surfer_change_email_requests'
    token = cast(str, Column(NonNullString,
                             nullable=False,
                             primary_key=True,
                             ))
    surfer_id = cast(Puid, Column(UUID(as_uuid=True), nullable=False))
    is_applied = cast(bool, Column(Boolean, nullable=False))
    is_consumed = cast(bool, Column(Boolean, nullable=False))
    new_email = cast(str, Column(NonNullString))
    old_email = cast(str, Column(NonNullString))
    time_expires = cast(int, Column(BigInteger, nullable=False))

    def as_dict(self):
        return {
            **self.time_dict(),
            'SurferId': self.surfer_id,
            'IsApplied': self.is_applied,
            'IsConsumed': self.is_consumed,
            'NewEmail': self.new_email,
            'OldEmail': self.old_email,
            'Token': self.token,
            'TimeExpires': self.time_expires,
        }


class SurferChangePasswordRequest(Base, TimesMixin):
    __tablename__ = 'surfer_change_password_requests'
    token = cast(str, Column(NonNullString,
                             nullable=False,
                             primary_key=True,
                             ))
    surfer_id = cast(Puid, Column(UUID(as_uuid=True), nullable=False))
    is_consumed = cast(bool, Column(Boolean, nullable=False))
    time_expires = cast(int, Column(BigInteger, nullable=False))

    def as_dict(self):
        return {
            **self.time_dict(),
            'SurferId': self.surfer_id,
            'IsConsumed': self.is_consumed,
            'Token': self.token,
            'TimeExpires': self.time_expires,
        }
