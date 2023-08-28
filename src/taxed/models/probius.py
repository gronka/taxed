import json
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from typing import cast

from taxed.core import (
    Base,
    NonNullBool,
    NonNullInt,
    NonNullString,
    Puid,
    TimesMixin,
)

ITEM_TYPE_NOTIFICATION = 0

PAYMENT_PLATFORM_STRIPE = 0
PAYMENT_PLATFORM_BTCPAY = 1

SILO_ADD_CREDIT = 'add_credit'
SILO_BASKET = 'basket'
SILO_BILL_PAY = 'bill_pay'
SILO_PLAN = 'plan'

ATTEMPT_STATUS_CREATED = 5
ATTEMPT_STATUS_FAILED = 10
ATTEMPT_STATUS_WAITING_ON_STRIPE = 30
ATTEMPT_STATUS_WAITING_TO_PROCESS = 50
ATTEMPT_STATUS_PROCESSING = 60
ATTEMPT_STATUS_PROCESSED = 70

BASKET_ITEM_TYPE_ADD_CREDIT = 'add_credit'
BASKET_ITEM_TYPE_BILL_PAY = 'bill_pay'
BASKET_ITEM_TYPE_NONE = 'none'
BASKET_ITEM_TYPE_PLAN = 'plan'

CHARGE_TYPE_PLAN = 1
CHARGE_TYPE_CHALLENGES = 2


class Probius(Base, TimesMixin):
    __tablename__ = 'probii'
    probius_id = cast(Puid, Column(UUID(as_uuid=True),
                                   primary_key=True,
                                   nullable=False,
                                   unique=True,
                                   ))
    creator_id = cast(Puid, Column(UUID(as_uuid=True), nullable=False))
    default_plastic_id = cast(str, Column(NonNullString))
    project_id = cast(Puid, Column(UUID(as_uuid=True), nullable=False))
    stripe_customer_id = cast(str, Column(NonNullString))

    credit = cast(int, Column(NonNullInt, nullable=False))
    debt = cast(int, Column(NonNullInt, nullable=False))
    is_autopay_enabled = cast(bool, Column(Boolean, nullable=False))
    first_period = cast(int, Column(NonNullInt, nullable=False))
    is_bill_overdue = cast(bool, Column(NonNullBool, nullable=False))
    is_closed = cast(bool, Column(NonNullBool, nullable=False))
    is_in_arrears = cast(bool, Column(NonNullBool, nullable=False))
    notes = cast(str, Column(NonNullString))
    time_last_bill_issued = cast(int, Column(NonNullInt, nullable=False))
    time_last_paid_off = cast(int, Column(NonNullInt, nullable=False))
    tokens_bought = cast(int, Column(BigInteger, nullable=False))
    tokens_used = cast(int, Column(BigInteger, nullable=False))

    def as_dict(self):
        return {
            **self.time_dict(),
            'ProbiusId': self.probius_id,
            'CreatorId': self.creator_id,
            'DefaultPlasticId': self.default_plastic_id,
            'ProjectId': self.project_id,
            'StripeCustomerId': self.stripe_customer_id,

            'Credit': self.credit,
            'Debt': self.debt,
            'IsAutopayEnabled': self.is_autopay_enabled,
            'FirstPeriod': self.first_period,
            'IsBillOverdue': self.is_bill_overdue,
            'IsClosed': self.is_closed,
            'IsInArrears': self.is_in_arrears,
            'Notes': self.notes,
            'TimeLastBillIssued': self.time_last_bill_issued,
            'TimeLastPaidOff': self.time_last_paid_off,
            'TokensBought': self.tokens_bought,
            'TokensUsed': self.tokens_used,
        }

    # def is_in_arrears(self) -> bool:
        # # only check if marked overdue
        # if self.is_bill_overdue:
            # # only check if a payoff has not been attempted
            # if self.time_last_bill_issued > self.time_last_paid_off: #type:ignore
                # # give seven days grace period
                # seven_days = 1000 * 60 * 60 * 24 * 7
                # if (nowstamp() - self.time_last_bill_issued) > seven_days: #type:ignore
                    # return True
        # return False

    def tokens_remaining(self) -> int:
        return self.tokens_bought - self.tokens_used

    def max_credit_to_apply(self, price: int) -> int:
        if self.credit > price:
            return price
        else:
            return self.credit


class Charge(Base, TimesMixin):
    __tablename__ = 'charges'
    charge_id = cast(Puid, Column(UUID(as_uuid=True),
                                  nullable=False,
                                  primary_key=True,
                                  server_default=text("uuid_generate_v4()"),
                                  unique=True,
                                  ))
    plan_id = cast(str, Column(NonNullString,
                               ForeignKey('plans.plan_id'),
                               nullable=False))
    probius_id = cast(Puid, Column(UUID(as_uuid=True),
                                   nullable=False,
                                   ))
    charge_type = cast(int, Column(Integer, nullable=False))
    currency = cast(str, Column(NonNullString))
    description = cast(str, Column(NonNullString))
    meta = cast(str, Column(NonNullString))
    period = cast(int, Column(Integer, nullable=False))
    price = cast(int, Column(Integer, nullable=False))
    units = cast(int, Column(Integer, nullable=False))

    def as_dict(self):
        return {
            **self.time_dict(),
            'ChargeId': self.charge_id,
            'ChargeType': self.charge_type,
            'Currency': self.currency,
            'Description': self.description,
            'Meta': self.meta,
            'Period': self.period,
            'PlanId': self.plan_id,
            'Price': self.price,
            'ProbiusId': self.probius_id,
            'Units': self.units,
        }


class Payment(Base, TimesMixin):
    __tablename__ = 'payments'
    payment_id = cast(Puid, Column(UUID(as_uuid=True),
                                   nullable=False,
                                   primary_key=True,
                                   server_default=text("uuid_generate_v4()"),
                                   unique=True,
                                   ))
    probius_id = cast(Puid, Column(UUID(as_uuid=True),
                                   ForeignKey('probii.probius_id'),
                                   nullable=False,
                                   ))
    bill_id = cast(Puid, Column(UUID(as_uuid=True)))

    btcpay_invoice_id = cast(str, Column(NonNullString))
    payment_intent_id = cast(str, Column(NonNullString))
    payment_platform = cast(int, Column(Integer, nullable=False))
    stripe_invoice_id = cast(str, Column(NonNullString))

    admin_notes = cast(str, Column(NonNullString))
    basket_string = cast(str, Column(NonNullString, nullable=False))
    credit_applied = cast(int, Column(Integer, nullable=False))
    currency = cast(str, Column(NonNullString, nullable=False))
    is_autopay_selected = cast(bool, Column(Boolean, nullable=False))
    notes = cast(str, Column(NonNullString))
    plastic_id = cast(str, Column(NonNullString))
    silo = cast(str, Column(NonNullString, nullable=False))
    status = cast(int, Column(Integer, nullable=False))
    terms_accepted_version = cast(str, Column(NonNullString))
    total_price = cast(int, Column(Integer, nullable=False))
    total_price_after_credit = cast(int, Column(Integer, nullable=False))

    def is_agreement_accepted(self):
        return len(self.terms_accepted_version) > 0

    def as_dict(self):
        return {
            **self.time_dict(),
            'PaymentId': self.payment_id,
            'ProbiusId': self.probius_id,
            'BillId': self.bill_id or '',
            'BtcpayInvoiceId': self.btcpay_invoice_id,
            'PaymentIntentId': self.payment_intent_id,
            'PaymentPlatform': self.payment_platform,
            'StripeInvoiceId': self.stripe_invoice_id,

            'AdminNotes': self.admin_notes,
            'BasketString': self.basket_string,
            'CreditApplied': self.credit_applied,
            'Currency': self.currency,
            'Notes': self.notes,
            'IsAutopaySelected': self.is_autopay_selected,
            'PlasticId': self.plastic_id,
            'Silo': self.silo,
            'Status': self.status,
            'TermsAcceptedVersion': self.terms_accepted_version,
            'TotalPrice': self.total_price,
            'TotalPriceAfterCredit': self.total_price_after_credit,
        }


class StripePaymentAttempt(Base, TimesMixin):
    __tablename__ = 'stripe_payment_attempts'
    attempt_id = cast(Puid,
                      Column(UUID(as_uuid=True),
                             nullable=False,
                             primary_key=True,
                             server_default=text("uuid_generate_v4()"),
                             unique=True,
                             ))
    payment_intent_id = cast(str, Column(NonNullString))
    plan_id = cast(str, Column(NonNullString, nullable=False))
    probius_id = cast(Puid, Column(UUID(as_uuid=True)))
    project_id = cast(Puid, Column(UUID(as_uuid=True)))

    admin_notes = cast(str, Column(NonNullString))
    basket_string = cast(str, Column(NonNullString, nullable=False))
    bill_id = cast(Puid, Column(UUID(as_uuid=True)))
    credit_applied = cast(int, Column(Integer, nullable=False))
    currency = cast(str, Column(NonNullString, nullable=False))
    is_autopay_selected = cast(bool, Column(Boolean, nullable=False))
    plastic_id = cast(str, Column(NonNullString, nullable=False))
    silo = cast(str, Column(NonNullString, nullable=False))
    status = cast(int, Column(Integer, nullable=False))
    terms_accepted_version = cast(str, Column(NonNullString))
    total_price = cast(int, Column(Integer, nullable=False))
    total_price_after_credit = cast(int, Column(Integer, nullable=False))

    def is_agreement_accepted(self):
        return len(self.terms_accepted_version) > 0

    def as_dict(self):
        return {
            **self.time_dict(),
            'AttemptId': self.attempt_id,
            'BillId': self.bill_id or '',
            'PlanId': self.plan_id,
            'PlasticId': self.plastic_id,
            'ProbiusId': self.probius_id,
            'ProjectId': self.project_id,

            'PaymentAttemptId': self.payment_intent_id,
            'ProbiusId': self.probius_id,
            'AdminNotes': self.admin_notes,
            'BasketString': self.basket_string,
            'CreditApplied': self.credit_applied,
            'Currency': self.currency,
            'IsAutopaySelected': self.is_autopay_selected,
            'Silo': self.silo,
            'Status': self.status,
            'TermsAcceptedVersion': self.terms_accepted_version,
            'TotalPrice': self.total_price,
            'TotalPriceAfterCredit': self.total_price_after_credit,
        }


class AgreementAcceptedLogs(Base, TimesMixin):
    __tablename__ = 'agreement_accepted_logs'
    surfer_id = cast(Puid, Column(UUID(as_uuid=True),
                                  nullable=False,
                                  primary_key=True,
                                  server_default=text("uuid_generate_v4()"),
                                  ))
    probius_id = cast(Puid, Column(UUID(as_uuid=True),
                                   ForeignKey('probii.probius_id'),
                                   nullable=False,
                                   ))
    is_accepted = cast(bool, Column(Boolean, nullable=False))

    def as_dict(self):
        return {
            **self.time_dict(),
            'SurferId': self.surfer_id,
            'ProbiusId': self.probius_id,
            'IsAccepted': self.is_accepted,
        }


BILL_TYPE_MONTHLY = 'monthly'

BILL_STATUS_CREATED = 'created'
BILL_STATUS_PAID = 'paid'
BILL_STATUS_PROCESSING = 'processing'
BILL_STATUS_TRY_AGAIN = 'try_again'


class Bill(Base, TimesMixin):
    __tablename__ = 'bills'
    bill_id = cast(Puid, Column(UUID(as_uuid=True),
                                nullable=False,
                                primary_key=True,
                                server_default=text("uuid_generate_v4()"),
                                unique=True,
                                ))
    probius_id = cast(Puid, Column(UUID(as_uuid=True),
                                   ForeignKey('probii.probius_id'),
                                   nullable=False))
    charge_ids = cast(str, Column(NonNullString, nullable=False))

    admin_notes = cast(str, Column(NonNullString))
    bill_type = cast(str, Column(NonNullString, nullable=False))
    credit_applied = cast(int, Column(Integer, default=0))
    credit_overflow = cast(int, Column(Integer, default=0))
    currency = cast(str, Column(NonNullString, nullable=False))
    notes = cast(str, Column(NonNullString, nullable=False))
    period = cast(int, Column(Integer, nullable=False))
    price = cast(int, Column(Integer, nullable=False))
    status = cast(str, Column(NonNullString, nullable=False))
    was_autopay_used = cast(bool, Column(Boolean, nullable=False))

    def as_dict(self):
        return {
            **self.time_dict(),
            'BillId': self.bill_id,
            'ProbiusId': self.probius_id,
            'ChargeIds': json.loads(self.charge_ids),
            'BillType': self.bill_type,
            'CreditApplied': self.credit_applied,
            'CreditOverflow': self.credit_overflow,
            'Currency': self.currency,
            'Notes': self.notes,
            'Period': self.period,
            'Price': self.price,
            'Status': self.status,
            'WasAutopayUsed': self.was_autopay_used,
        }
