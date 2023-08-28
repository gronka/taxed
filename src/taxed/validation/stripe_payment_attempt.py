import json
from sqlalchemy.orm import Session

from taxed.core import plog
from taxed.models import (
    BASKET_ITEM_TYPE_PLAN,
    Plan,
    Probius,
    SILO_ADD_CREDIT,
    SILO_BASKET,
    SILO_BILL_PAY,
    SILO_PLAN,
    StripePaymentAttempt)
from taxed.payments.basket_item import BasketItem
from taxed.validation.validation import Validation


class ValidateStripePaymentAttempt:
    @staticmethod
    def all_fields(
            pa: StripePaymentAttempt, db: Session) -> bool:
        if pa.silo == SILO_ADD_CREDIT or \
                pa.silo == SILO_BILL_PAY or \
                pa.silo == SILO_PLAN:
            return ValidateStripePaymentAttempt.is_agreement_accepted(
                pa).is_valid

        elif pa.silo == SILO_BASKET:
            return ValidateStripePaymentAttempt.\
                total_price_and_basket_items(pa, db).is_valid and \
            ValidateStripePaymentAttempt.is_agreement_accepted(pa).is_valid

        else:
            msg = f'invalid silo for {pa.attempt_id}'
            plog.critical(msg)
            raise RuntimeError(msg)

    @staticmethod
    def is_agreement_accepted(
            pa: StripePaymentAttempt) -> Validation:
        validation = Validation()
        if not pa.terms_accepted_version:
            msg = f'terms not accepted for payment_attempt {pa.as_dict()}'
            plog.critical(msg)
            validation.add_error(msg)
        return validation

    @staticmethod
    def total_price_and_basket_items(
            pa: StripePaymentAttempt, db: Session) -> Validation:
        validation = Validation()

        probius: Probius = db.query(Probius).filter(
            Probius.probius_id == pa.probius_id).first() or Probius()  #type:ignore
        if probius is None:
            msg = 'No probius found for payment attempt: {pa.probius_id}'
            plog.wtf(msg)
            raise RuntimeError(msg)

        if probius.credit < pa.credit_applied:
            msg = f'invalid credit applied for payment_attempt {pa.as_dict()}'
            plog.critical(msg)
            validation.add_error(msg)

        basket = json.loads(str(pa.basket_string))
        basket_total_price = 0
        for item_raw in basket:
            item = BasketItem(**item_raw)
            basket_total_price += item.Price

            if item.ItemType == BASKET_ITEM_TYPE_PLAN:
                plan = db.query(Plan).filter(
                    Plan.plan_id == item.plan_id).first() or Plan() #type:ignore

                if item.Price != plan.price:
                    msg = f'invalid item price in payment_attempt {pa.as_dict()}'
                    plog.critical(msg)
                    validation.add_error(msg)

        if basket_total_price != pa.total_price:
            msg = f'invalid total price for payment_attempt {pa.as_dict()}'
            plog.critical(msg)
            validation.add_error(msg)

        return validation
