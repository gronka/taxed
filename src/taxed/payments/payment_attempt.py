import asyncio
from dateutil.relativedelta import relativedelta
from fastapi import Depends
import json
import pprint
from sqlalchemy.orm import Session
import uuid

from taxed.core import (
    db_commit,
    get_db,
    nowstamp,
    now,
    plog,
    Puid,
    ResponseBuilder,
)
from taxed.models import (
    ATTEMPT_STATUS_FAILED,
    ATTEMPT_STATUS_WAITING_ON_STRIPE,
    ATTEMPT_STATUS_WAITING_TO_PROCESS,
    ATTEMPT_STATUS_PROCESSING,
    ATTEMPT_STATUS_PROCESSED,
    Bill,
    BILL_STATUS_PAID,
    BILL_STATUS_PROCESSING,
    BILL_STATUS_TRY_AGAIN,
    Payment,
    PAYMENT_PLATFORM_STRIPE,
    # PAYMENT_PLATFORM_BTCPAY,
    Plan,
    Probius,
    Project,
    SILO_ADD_CREDIT,
    SILO_BASKET,
    SILO_BILL_PAY,
    SILO_PLAN,
    StripePaymentAttempt,
)

from taxed.payments import stripe
from taxed.payments.basket_item import BasketItem
from taxed.services.bills.run_biller import try_to_pay_failed_bills
from taxed.validation.stripe_payment_attempt import ValidateStripePaymentAttempt


def get_and_update_payment_attempt_status_from_intent(
    attempt_id: str,
    rb: ResponseBuilder,
    db: Session,
) -> int:
    payment_attempt = db.query(StripePaymentAttempt).filter( 
        StripePaymentAttempt.attempt_id == attempt_id).first() or StripePaymentAttempt() #type:ignore

    print('2222222222222222222222222222222222')
    print(payment_attempt.as_dict())

    payment_intent = stripe.PaymentIntent.retrieve(
        payment_attempt.payment_intent_id)

    # list of statuses:
    # https://stripe.com/docs/payments/payment-intents/verifying-status
    # requires_payment_method,
    # requires_confirmation
    # requires_action
    # processing
    # requires_capture
    # canceled
    # succeeded

    new_status = ATTEMPT_STATUS_WAITING_ON_STRIPE

    if payment_intent.status == 'succeeded':
        new_status = ATTEMPT_STATUS_PROCESSED
    elif payment_intent.status == 'canceled':
        new_status = ATTEMPT_STATUS_FAILED
    elif payment_intent.status == 'requires_payment_method' or \
        payment_intent.status == 'requires_confirmation' or \
        payment_intent.status == 'requires_action' or \
        payment_intent.status == 'processing' or \
        payment_intent.status == 'requires_capture':
        new_status = ATTEMPT_STATUS_WAITING_ON_STRIPE
    else:
        plog.critical(
            f'unknown stripe PaymentIntent status for attempt_id = {attempt_id}')

    payment_attempt.status = new_status
    db.add(payment_attempt)
    db_commit(db, rb)

    return new_status

async def process_payment_attempt(attempt_id: Puid,
                                  rb: ResponseBuilder,
                                  db: Session = Depends(get_db)):
    await asyncio.sleep(2)
    print(f'processing payment {attempt_id}')

    payment_attempt = db.query(StripePaymentAttempt).filter(
        StripePaymentAttempt.attempt_id == attempt_id).first() or StripePaymentAttempt() #type:ignore

    if payment_attempt.status != ATTEMPT_STATUS_WAITING_TO_PROCESS:
        return

    if (not ValidateStripePaymentAttempt.all_fields(payment_attempt, db)):
        payment_attempt.status = ATTEMPT_STATUS_FAILED
        payment_attempt.admin_notes += '; failed validation'
        db.add(payment_attempt)
        db_commit(db, rb)
        return

    print(f'attempt status {payment_attempt.status}')

    age = nowstamp() - payment_attempt.time_created

    # TODO: decide a good timeout value here. we can start with 1 hour
    print(f'age: {age}')
    if age > 3600:
        print(f'age > 3600')
        print('payment older than 1 hour - mark it as dead')
        payment_attempt.status = ATTEMPT_STATUS_FAILED
        payment_attempt.admin_notes += '; payment was not made in 1 hour'
        db.add(payment_attempt)
        db_commit(db, rb)
        return

    #TODO: fix this function
    should_process = _should_process_payment_attempt(payment_attempt)
    should_process = True
    print(f'should_process: {should_process}')

    payment_attempt.time_updated = nowstamp()
    if not should_process:
        return

    payment_attempt.status = ATTEMPT_STATUS_PROCESSING
    db.add(payment_attempt)
    db_commit(db, rb)

    print(payment_attempt.basket_string)
    pp = pprint.PrettyPrinter(indent=4)
    basket = json.loads(payment_attempt.basket_string)
    pp.pprint(basket)

    if payment_attempt.silo == SILO_ADD_CREDIT:
        _process_silo_add_credit(payment_attempt)

    elif payment_attempt.silo == SILO_BILL_PAY:
        _process_silo_bill_pay(payment_attempt, rb, db)

    elif payment_attempt.silo == SILO_BASKET:
        for item_raw in basket:
            item = BasketItem(**item_raw)
            _process_basket_item(item)

    elif payment_attempt.silo == SILO_PLAN:
        _process_silo_plan(payment_attempt, rb, db)

    else:
        msg = f'Invalid payment_attempt.silo+{payment_attempt.silo}'
        plog.critical(msg)
        raise RuntimeError(msg)

    probius = db.query(Probius).filter(
        Probius.probius_id == payment_attempt.probius_id).first() or Probius()  #type:ignore
    if probius.not_found():
        plog.wtf('probius not found: {payment_attempt.probius_id}')

    if payment_attempt.is_autopay_selected:
        #NOTE: do nothing when false, since we don't want to disable previous
        # autopay method
        probius.is_autopay_selected = True

    _adjust_probius_credit(payment_attempt, probius)
    db.add(probius)
    db_commit(db, rb)

    payment_attempt.status = ATTEMPT_STATUS_PROCESSED
    db.add(payment_attempt)
    db_commit(db, rb)

    pa = payment_attempt
    # payment is created for successful payment attempt
    payment = Payment()
    payment.payment_id = str(uuid.uuid4())
    payment.probius_id = pa.probius_id
    payment.project_id = pa.project_id
    payment.payment_intent_id = pa.payment_intent_id
    payment.payment_platform = PAYMENT_PLATFORM_STRIPE

    payment.admin_notes = pa.admin_notes
    payment.basket_string = pa.basket_string
    payment.bill_id = pa.bill_id
    payment.credit_applied = pa.credit_applied
    payment.currency = pa.currency
    payment.is_autopay_selected = pa.is_autopay_selected
    payment.silo = pa.silo
    payment.plastic_id = pa.plastic_id
    payment.status = pa.status
    payment.terms_accepted_version = pa.terms_accepted_version
    payment.total_price = pa.total_price
    payment.total_price_after_credit = pa.total_price_after_credit

    db.add(payment)
    db_commit(db, rb)


def _process_silo_plan(pa: StripePaymentAttempt,
                       rb: ResponseBuilder,
                       db: Session):
    print('++++++++++++++++++++++++++++++++++')
    print('processing silo plan')
    project = db.query(Project).filter(  
           Project.project_id == pa.project_id).first() or Project() #type:ignore

    plan: Plan = db.query(Plan).filter(  #type:ignore
         Plan.plan_id == pa.plan_id).first() or Plan() #type:ignore
    if plan.not_found():
        plog.wtf(f'plan not found: {pa.plan_id}')
        return

    probius: Probius = db.query(Probius).filter(  #type:ignore
         Probius.probius_id == pa.probius_id).first() or Probius() #type:ignore
    if probius.not_found():
        plog.wtf(f'probius not found: {pa.probius_id}')
        return

    project.time_plan_expires = int((now() + 
        relativedelta(months=+plan.months)).timestamp())

    print('======================')
    print(plan.bundled_tokens)
    print(probius.tokens_bought)
    print(probius.tokens_used)
    print('+++++++++++++++++++++++++++++')
    probius.tokens_bought += plan.bundled_tokens
    db.add(probius)
    db_commit(db, rb)

    #TODO: am I using plan_id_next correctly here?
    project.plan_id = pa.plan_id
    project.plan_id_next = project.plan_id
    db.add(project)
    db_commit(db, rb)


def _process_silo_add_credit(pa: StripePaymentAttempt):
    print('++++++++++++++++++++++++++++++++++')
    print('processing silo add credit: checking unpaid bills')
    try_to_pay_failed_bills(pa.project_id)


def _process_silo_bill_pay(pa: StripePaymentAttempt,
                           rb: ResponseBuilder,
                           db: Session):
    print('++++++++++++++++++++++++++++++++++')
    print('processing silo bill pay')
    bill = db.query(Bill).filter(  #type:ignore
        Bill.bill_id == pa.bill_id).first() or Bill() #type:ignore

    if pa.status == ATTEMPT_STATUS_FAILED:
        bill.status = BILL_STATUS_TRY_AGAIN
    elif pa.status == ATTEMPT_STATUS_WAITING_ON_STRIPE \
            or pa.status == ATTEMPT_STATUS_WAITING_TO_PROCESS \
            or pa.status == ATTEMPT_STATUS_PROCESSING:
        bill.status = BILL_STATUS_PROCESSING
    elif pa.status == ATTEMPT_STATUS_PROCESSED:
        bill.status = BILL_STATUS_PAID

    db.add(bill)
    db_commit(db, rb)


def _adjust_probius_credit(pa: StripePaymentAttempt, probius: Probius) -> None:
    max_credit = probius.max_credit_to_apply(pa.total_price)
    if max_credit != pa.credit_applied:
        msg = (f'credit application mismatch: {pa.credit_applied} was ',
               f'applied, but max credit is {max_credit} at {nowstamp()}')
        plog.warning(msg)
        pa.admin_notes += f'; {msg}'

    if pa.silo == SILO_ADD_CREDIT:
        probius.credit += pa.total_price

    elif pa.silo == SILO_BILL_PAY or \
            pa.silo == SILO_BASKET or \
            pa.silo == SILO_PLAN:
        probius.credit -= pa.credit_applied

    else:
        msg = f'Invalid payment_attempt.silo+{pa.silo}'
        plog.critical(msg)
        raise RuntimeError(msg)


def _process_basket_item(item: BasketItem):
    print('++++++++++++++++++++++++++++++++++')
    print('processing silo basket... not implemented')
    print(item.Name)


def _should_process_payment_attempt(
    payment_attempt: StripePaymentAttempt) -> bool:

    age = nowstamp() - payment_attempt.time_created
    time_since_update = nowstamp() - payment_attempt.time_updated

    # after 2 minutes, poll slower
    if age > 120 and time_since_update > 30:
        return True

    # after 3 minutes, poll slower
    if age > 180 and time_since_update > 60:
        return True

    if age > 1200:
        return False

    return False
