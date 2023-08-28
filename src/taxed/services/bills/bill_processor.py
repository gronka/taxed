from sqlalchemy.orm import Session
from stripe.error import CardError
import uuid

from taxed.services.bills.bill_alerter import BillAlerter
from taxed.core import (
    plog,
)
from taxed.models import (
    ATTEMPT_STATUS_FAILED,
    ATTEMPT_STATUS_WAITING_ON_STRIPE,
    ATTEMPT_STATUS_PROCESSED,
    Bill,
    BILL_STATUS_PAID,
    BILL_STATUS_PROCESSING,
    BILL_STATUS_TRY_AGAIN,
    Probius,
    SILO_BILL_PAY,
    StripePaymentAttempt,
)
from taxed.payments import stripe


class BillProcessor:
    def __init__(self, bill: Bill, db: Session, ba: BillAlerter):
        self.bill = bill
        self.db = db
        self.ba = ba
        self.probius: Probius = db.query(Probius).filter(
             Probius.probius_id == bill.probius_id).first() #type:ignore

    def try_to_pay_bill(self):
        payment_attempt = StripePaymentAttempt()
        payment_attempt.attempt_id = str(uuid.uuid4())
        payment_attempt.probius_id = self.bill.probius_id
        payment_attempt.is_autopay_selected = self.probius.is_autopay_enabled
        payment_attempt.plastic_id = self.probius.default_plastic_id
        payment_attempt.terms_accepted_version = self.bill.terms_accepted_version
        payment_attempt.silo = SILO_BILL_PAY
        payment_attempt.basket = '[]'

        credit_to_apply = self.probius.max_credit_to_apply(self.bill.price) #type:ignore
        self.bill.credit_applied = credit_to_apply
        payment_attempt.credit_applied = self.bill.credit_applied
        payment_attempt.total_price = self.bill.price

        payment_attempt.total_price_after_credit = \
            self.bill.price - self.bill.credit_applied #type:ignore

        total_sans_credit = self.bill.price - credit_to_apply #type:ignore
        if total_sans_credit < 50:
            #NOTE: stripe does not allow transactions less than 50 cents, so
            # let's just give the user more credit
            self.bill.credit_overflow = total_sans_credit
        else:
            self.bill.credit_overflow = 0

        if (self.probius.credit + self.bill.credit_overflow) >= self.bill.price: #type:ignore
            payment_attempt.status = ATTEMPT_STATUS_PROCESSED
            self.bill.status = BILL_STATUS_PAID

        if self.probius.is_autopay_enabled:
            self.bill.was_autopay_used = True

            try:
                pi = stripe.PaymentIntent.create(
                    amount=(self.bill.price - self.bill.credit_applied), #type:ignore
                    confirm=True,
                    currency='usd',
                    payment_method=self.probius.default_plastic_id,
                )
                payment_attempt.payment_intent_id = pi.id

                if pi.status == 'succeeded':
                    payment_attempt.status = ATTEMPT_STATUS_PROCESSED
                    self.bill.status = BILL_STATUS_PAID

                elif pi.status == 'canceled' or \
                    pi.status == 'requires_payment_method' or \
                    pi.status == 'requires_confirmation' or \
                    pi.status == 'requires_action' or \
                    pi.status == 'requires_capture':
                    payment_attempt.status = ATTEMPT_STATUS_FAILED
                    self.bill.status = BILL_STATUS_TRY_AGAIN

                    #TODO: look for and process a bill after a user adds credit
                elif pi.status == 'processing':
                    payment_attempt.status = ATTEMPT_STATUS_WAITING_ON_STRIPE
                    self.bill.status = BILL_STATUS_PROCESSING

                else:
                    plog.critical(
                        f'unknown stripe PaymentIntent status for attempt_id = '\
                        '{payment_attempt.attempt_id}')
                    payment_attempt.status = ATTEMPT_STATUS_FAILED
                    self.bill.status = BILL_STATUS_TRY_AGAIN

            except CardError as e:
                err = e.error
                # Error code will be authentication_required if authentication is needed
                print("Code is: %s" % err.code)
                #TODO: do I need to set this id again?
                payment_attempt.payment_intent_id = err.payment_intent['id']
                payment_attempt.status = ATTEMPT_STATUS_FAILED
                self.bill.status = BILL_STATUS_TRY_AGAIN

        else:
            self.ba.alert_bill_due_now()

        if self.bill.status == BILL_STATUS_PAID:
            self.probius.credit -= self.bill.credit_applied #type:ignore
            self.ba.alert_bill_paid()
        else:
            if not self.probius.is_autopay_enabled:
                self.ba.alert_bill_due_now()
            else:
                self.ba.alert_bill_payment_failed()

        self.db.add(self.bill)
        self.db.add(self.probius)
        self.db.add(payment_attempt)
        self.db.commit()
