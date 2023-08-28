from sqlalchemy import Boolean, Column, ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session
from typing import cast

from taxed.core import (
    Base,
    NonNullString,
    Puid,
    TimesMixin,
)


PLAN_FREE = 'free'
PLAN_SMALL = 'small'
PLAN_MEDIUM = 'medium'
PLAN_LARGE = 'large'


def get_plan_by_id(db: Session, plan_id: Puid):
    plan: Plan = db.query(Plan).filter(Plan.plan_id == plan_id).first() #type:ignore
    if plan is None:
        return Plan()
    return plan



class Plan(Base, TimesMixin):
    __tablename__ = 'plans'
    plan_id = cast(str, Column(NonNullString,
                               primary_key=True,
                               nullable=False,
                               unique=True,
                               ))
    sort_id = cast(int, Column(Integer,
                               nullable=False,
                               unique=True,
                               ))

    bundled_tokens = cast(int, Column(Integer, nullable=False))
    months= cast(int, Column(Integer, nullable=False))
    price = cast(int, Column(Integer, nullable=False))
    price_currency = cast(str, Column(NonNullString, nullable=False))

    admin_notes = cast(str, Column(NonNullString, nullable=False))
    description = cast(str, Column(NonNullString, nullable=False))
    is_available = cast(bool, Column(Boolean, nullable=False))
    is_tailored = cast(bool, Column(Boolean, nullable=False))
    rules = cast(str, Column(NonNullString, nullable=False))
    title = cast(str, Column(NonNullString, nullable=False))

    def as_dict(self):
        return {
            **self.time_dict(),
            'PlanId': self.plan_id,
            'SortId': self.sort_id,

            'BundledTokens': self.bundled_tokens,
            'Months': self.months,
            'Price': self.price,
            'PriceCurrency': self.price_currency,

            'AdminNotes': self.admin_notes,
            'Description': self.description,
            'IsAvailable': self.is_available,
            'IsTailored': self.is_tailored,
            'Rules': self.rules,
            'Title': self.title,
        }


class PlanChangeRequest(Base, TimesMixin):
    __tablename__ = 'plan_change_requests'
    plan_change_id = cast(Puid, Column(UUID(as_uuid=True),
                                       nullable=False,
                                       primary_key=True,
                                       server_default=text("uuid_generate_v4()"),
                                       unique=True,
                                       ))
    surfer_id = cast(Puid, Column(UUID(as_uuid=True),
                                  ForeignKey('surfers.surfer_id'),
                                  nullable=False,
                                  primary_key=True,
                                  server_default=text("uuid_generate_v4()"),
                                  ))
    plan_id_next = cast(str, Column(NonNullString,
                                    ForeignKey('plans.plan_id'),
                                    nullable=False))
    project_id = cast(Puid, Column(UUID(as_uuid=True),
                                   ForeignKey('projects.project_id'),
                                   nullable=False,
                                   primary_key=True,
                                   server_default=text("uuid_generate_v4()"),
                                   ))
    terms_accepted_version = cast(str, Column(NonNullString))

    def is_agreement_accepted(self):
        return len(self.terms_accepted_version) > 0

    def as_dict(self):
        return {
            'PlanChangeId': self.plan_change_id,
            'SurferId': self.surfer_id,
            'PlanId_next': self.plan_id_next,
            'ProjectId': self.project_id,
            'TermsAcceptedVersion': self.terms_accepted_version,
        }

