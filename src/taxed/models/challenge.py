from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID
from typing import cast

from taxed.core import (
    Base,
    # NonNullString,
    Puid,
    TimesMixin,
)


class Challenge(Base, TimesMixin):
    __tablename__ = 'challenges'
    challenge_id = cast(Puid,
                        Column(UUID(as_uuid=True),
                               nullable=False,
                               primary_key=True,
                               server_default=text('uuid_generate_v4()'),
                               unique=True,
                               ))
    surfer_id = cast(Puid,
                     Column(UUID(as_uuid=True),
                            nullable=False,
                            ))
    target_property_id = cast(Puid,
                              Column(UUID(as_uuid=True),
                                     nullable=False,
                                     ))

    # TODO: these values are placeholder until better implementation is found
    reason_purchase_price = False
    reason_description = False
    reason_appraised = False
    reason_recent_offer = False
    hearing = False

    def as_dict(self):
        return {
            **self.time_dict(),
            'ChallengeId': self.challenge_id,
            'SurferId': self.surfer_id,
            'TargetPropertyId': self.target_property_id,
        }
