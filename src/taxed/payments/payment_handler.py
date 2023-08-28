from fastapi import Request
from sqlalchemy.orm import Session
from stripe.error import CardError
from typing import List
import uuid

from taxed.core import (
    ApiSchema,
    db_commit,
    plog,
    ResponseBuilder,
)
from taxed.models import (
    ATTEMPT_STATUS_CREATED,
    ATTEMPT_STATUS_FAILED,
    ATTEMPT_STATUS_WAITING_ON_STRIPE,
    ATTEMPT_STATUS_WAITING_TO_PROCESS,
    Plan,
    Probius,
    SILO_ADD_CREDIT,
    SILO_BILL_PAY,
    SILO_BASKET,
    SILO_PLAN,
    StripePaymentAttempt,
)
from taxed.payments import stripe
from taxed.payments.basket_item import BasketItem
from taxed.validation.stripe_payment_attempt import ValidateStripePaymentAttempt


class PaymentDetailsIn(ApiSchema):
    BillId: str
    PlanId: str
    PlasticId: str
    ProbiusId: str
    ProjectId: str
    
    CreditApplied: int
    IsAutopaySelected: bool
    IsSaveCardSelected: bool
    IsPlasticIdUnlisted: bool
    Silo: str
    TermsAcceptedVersion: str
    TotalPrice: int
    TotalPriceAfterCredit: int
    BasketString: str
    Basket: List[BasketItem]


class PaymentDetailsHandler:
    def __init__(self, 
                 jin: PaymentDetailsIn,
                 db: Session,
                 rb: ResponseBuilder):
        self.db = db
        self.rb = rb

        self.spa = StripePaymentAttempt()
        self.spa.attempt_id = uuid.uuid4()
        self.spa.plan_id = jin.PlanId
        self.spa.plastic_id = jin.PlasticId
        self.spa.probius_id = jin.ProbiusId
        self.spa.project_id = jin.ProjectId

        print('777777777777777777777777777777777777')
        print(jin.ProbiusId)
        print(self.spa.probius_id)
        print(jin.ProjectId)

        self.spa.credit_applied = jin.CreditApplied
        self.spa.silo = jin.Silo
        self.spa.is_autopay_selected = jin.IsAutopaySelected
        self.spa.terms_accepted_version = jin.TermsAcceptedVersion
        self.spa.status = ATTEMPT_STATUS_CREATED
        self.spa.basket_string = jin.BasketString
        # self.basket = jin.Basket

        if jin.Silo == SILO_BILL_PAY:
            self.spa.bill_id = jin.BillId

        plog.v('payment_attempt created')

        self.jin = jin

        self.probius = db.query(Probius).filter(
            Probius.probius_id == self.spa.probius_id).first() or Probius() #type:ignore

        if self.probius is None:
            print(self.spa.probius_id)
            msg = 'No probius found for payment attempt: {pa.probius_id}'
            plog.wtf(msg)
            raise RuntimeError(msg)

        self.spa.total_price = jin.TotalPrice
        self.spa.total_price_after_credit = jin.TotalPriceAfterCredit
        self.recompute_price()
        plog.verbose(self.jin)

    def commit_changes(self):
        self.db.add(self.spa)
        db_commit(self.db, self.rb)

    def step1_validate(self):
        if (not ValidateStripePaymentAttempt.all_fields(self.spa, self.db)):
            plog.warning('payment_attempt validation failed')
            self.spa.admin_notes = 'Failed validation'
            self.spa.status = ATTEMPT_STATUS_FAILED
            self.spa.payment_intent_id = 'neverReached'
            self.commit_changes()

    # def step2_attempt_payment_unlisted_card(self):
    def step2_make_stripe_session_with_unlisted_card(self, request: Request):
        success_url = (f'{request.base_url}payment/result'
                       f'?payment_attempt_id={self.spa.attempt_id}')
        cancel_url = success_url

        kargs = {
                'customer': self.probius.stripe_customer_id,
                'line_items': [{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Subscription price after credit',
                            },
                        'unit_amount': self.spa.total_price_after_credit,
                        },
                    'quantity': 1,
                    }],
                'mode': 'payment',
                'payment_method_types': ['card'],
                'success_url': success_url,
                'cancel_url': cancel_url,
                }

        if self.jin.IsSaveCardSelected:
            plog.v('save_card_selected == True')
            session = stripe.checkout.Session.create(
                **kargs,
                payment_intent_data={
                    'setup_future_usage': 'off_session',
                },
            )

        else:
            plog.v('save_card_selected == False')
            session = stripe.checkout.Session.create(
                **kargs,
            )

        self.spa.payment_intent_id = session.payment_intent

        print(self.spa.payment_intent_id)
        print(success_url)
        print(cancel_url)
        self.commit_changes()
        return session


    def step2_make_stripe_session_with_saved_card(self):
        try:
            pi = stripe.PaymentIntent.create(
                amount=self.spa.total_price_after_credit,
                currency='usd',
                customer=self.probius.stripe_customer_id,
                payment_method=self.spa.plastic_id,
                off_session=True,
                confirm=True,
            )
            payment_intent_id = pi.id

            if pi.status == 'succeeded':
                self.spa.status = ATTEMPT_STATUS_WAITING_TO_PROCESS
            elif pi.status == 'canceled':
                self.spa.status = ATTEMPT_STATUS_FAILED
            elif pi.status == 'requires_payment_method' or \
                pi.status == 'requires_confirmation' or \
                pi.status == 'requires_action' or \
                pi.status == 'processing' or \
                pi.status == 'requires_capture':
                self.spa.status = ATTEMPT_STATUS_WAITING_ON_STRIPE
            else:
                plog.critical(
                    f'unknown stripe PaymentIntent status for attempt_id = '\
                    f'{self.spa.attempt_id}')
                self.spa.status = ATTEMPT_STATUS_FAILED

        except CardError as e:
            err = e.error
            # Error code will be authentication_required if authentication 
            # is needed
            msg = f'Code is {err.code} for spa {self.spa.attempt_id}'
            plog.critical(msg)
            payment_intent_id = err.payment_intent['id']
            self.spa.status = ATTEMPT_STATUS_FAILED

        self.spa.payment_intent_id = payment_intent_id
        self.commit_changes()

    def recompute_price(self):
        if self.spa.silo == SILO_ADD_CREDIT:
            #NOTE: nothing to do; use price from user session
            pass

        elif self.spa.silo == SILO_PLAN:
            plan: Plan = self.db.query(Plan).filter(
                Plan.plan_id == self.spa.plan_id).first()  # type: ignore
            if plan is None:
                plog.wtf(f'plan not found: {self.spa.plan_id}')
                return

            self.spa.total_price = plan.price
            self.spa.total_price_after_credit = plan.price - self.probius.credit

        elif self.spa.silo == SILO_BASKET:
            #TODO: prob not needed for FairlyTaxed
            pass

        elif self.spa.silo == SILO_BILL_PAY:
            #TODO: prob pass BillId from user to calc
            pass
