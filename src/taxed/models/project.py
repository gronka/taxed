from sqlalchemy import BigInteger, Column, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from typing import cast

from taxed.core import (
    Base,
    NonNullString,
    Puid,
    TimesMixin,
)


class Project(Base, TimesMixin):
    __tablename__ = 'projects'
    project_id = cast(Puid, Column(UUID(as_uuid=True),
                                   nullable=False,
                                   primary_key=True,
                                   server_default=text("uuid_generate_v4()"),
                                   unique=True,
                                   ))
    creator_id = cast(Puid, Column(UUID(as_uuid=True), nullable=False))
    plan_id = cast(str, Column(NonNullString,
                               ForeignKey('plans.plan_id'),
                               nullable=False))
    plan_id_next = cast(str, Column(NonNullString,
                                    ForeignKey('plans.plan_id'),
                                    nullable=False))
    probius_id = cast(Puid, Column(UUID(as_uuid=True),
                                   nullable=False,
                                   ))

    name = cast(str, Column(NonNullString, nullable=False))
    notes = cast(str, Column(NonNullString, nullable=False))
    time_plan_expires = cast(int, Column(BigInteger, nullable=False))


    def as_dict(self):
        return {
            **self.time_dict(),
            'ProjectId': self.project_id,
            'CreatorId': self.creator_id,
            'PlanId': self.plan_id,
            'PlanIdNext': self.plan_id_next,
            'ProbiusId': self.probius_id,

            'Name': self.name,
            'Notes': self.notes,
            'TimePlanExpires': self.time_plan_expires,
        }
