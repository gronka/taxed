from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from taxed.core import (
    ApiError,
    ApiSchema,
    get_db,
    Gibs,
    plog,
    Policies,
    policy_fails,
    PaymentIdIn,
    ProjectIdIn,
    Puid,
    ResponseBuilder,
)
from taxed.models import (
    ATTEMPT_STATUS_FAILED,
    ATTEMPT_STATUS_WAITING_ON_STRIPE,
    ATTEMPT_STATUS_WAITING_TO_PROCESS,
    Payment,
    Project,
    StripePaymentAttempt,
)
from taxed.payments.payment_attempt import (
    get_and_update_payment_attempt_status_from_intent,
    process_payment_attempt,
)
from taxed.payments.payment_handler import (
    PaymentDetailsHandler,
    PaymentDetailsIn,
)

router = APIRouter()

PaymentFailedError = ApiError(
    code='payment_failed',
    msg='Payment failed. Try anothe method.')


class StripePayOut(ApiSchema):
    PaymentAttemptId: Optional[str]
    StripeUrl: Optional[str]
    Status: str


class PaymentSchema(ApiSchema):
    AttemptId: Puid = ''
    PaymentId: Puid = ''
    PaymentIntentId: Puid = ''
    BillId: Puid = ''
    ChargeIds: List[str] = []
    PlasticId: str = ''
    ProbiusId: Puid

    AdminNotes: str
    Basket: str
    CreditApplied: int
    Currency: str
    IsAutopaySelected: bool
    Notes: str = ''
    Silo: str
    Status: str
    TimeCreated: int
    TotalPrice: int
    TotalPriceAfterCredit: int

class PaymentCollectionSchema(ApiSchema):
    Collection: List[Optional[PaymentSchema]]

@router.post('/payment/get.byId', response_model=PaymentSchema)
async def payment_get_by_id(request: Request,
                            jin: PaymentIdIn,
                            db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    project: Project = db.query(Project).filter(
        Project.probius_id == jin.ProbiusId).first()  # type: ignore
    if project is None:
        return rb.missing_requirement_response('project')
    if policy_fails(rb, await Policies.is_user_admin_of_project(gibs, project),
                    inspection_count= 2):
        return rb.policy_failed_response()

    payment = db.query(Payment).filter(
        Payment.payment_id == jin.PaymentId).first()  # type: ignore
    if payment is None:
        return rb.missing_requirement_response('payment')

    rb.set_fields_with_dict(payment.as_dict())
    return rb.build_response()

@router.post('/stripe/pay', response_model=StripePayOut)
async def stripe_create_session(request: Request,
                                jin: PaymentDetailsIn,
                                db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    pdh = PaymentDetailsHandler(jin, db, rb)

    pdh.step1_validate()
    if pdh.spa.status == ATTEMPT_STATUS_FAILED:
        pdh.commit_changes()
        rb.add_error(PaymentFailedError)
        return rb.build_response()

    if jin.IsPlasticIdUnlisted:
        session = pdh.step2_make_stripe_session_with_unlisted_card(request)

        rb.set_field('StripeUrl', session.url)
        rb.set_field('Status', 'waitForStripe')
        # print(str(pdh.spa.attempt_id))
        rb.set_field('PaymentAttemptId', str(pdh.spa.attempt_id))
        return rb.build_response()

    else:
        session = pdh.step2_make_stripe_session_with_saved_card()

        if pdh.spa.status == ATTEMPT_STATUS_FAILED:
            rb.add_error(PaymentFailedError)
            rb.set_field('Status', 'failed')
            return rb.build_response()
        else:
            rb.set_field('Status', 'success')
            await process_payment_attempt(pdh.spa.attempt_id, rb, db)
            return rb.build_response()


@router.post('/payments/get.successful.byProjectId',
             response_model=PaymentCollectionSchema)
async def payments_get_succesful_by_project_id(request: Request,
                                               jin: ProjectIdIn,
                                               db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    project: Project = db.query(Project).filter(
        Project.probius_id == jin.ProbiusId).first()  # type: ignore
    if project is None:
        return rb.missing_requirement_response('project')
    if policy_fails(rb, await Policies.is_user_admin_of_project(gibs, project),
                    inspection_count= 2):
        return rb.policy_failed_response()

    payments = db.query(Payment).filter(Payment.project_id == jin.ProjectId
        ).order_by(Payment.time_created.desc()).all() #type:ignore

    collection = []
    for payment in payments:
        collection.append(payment.as_dict())

    rb.set_field('Collection', collection)
    return rb.build_response()


@router.post('/payments/get.ccAttempts.byProjectId',
             response_model=PaymentCollectionSchema)
async def payments_get_cc_attempts_by_project_id(request: Request,
                                                 jin: ProjectIdIn,
                                                 db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    project: Project = db.query(Project).filter(
        Project.probius_id == jin.ProbiusId).first()  # type: ignore
    if project is None:
        return rb.missing_requirement_response('project')
    if policy_fails(rb, await Policies.is_user_admin_of_project(gibs, project),
                    inspection_count= 2):
        return rb.policy_failed_response()

    payments = db.query(StripePaymentAttempt).filter(
        StripePaymentAttempt.project_id == jin.ProjectId #type:ignore
            ).order_by(StripePaymentAttempt.time_created.desc()).all() #type:ignore

    collection = []
    for payment in payments:
        collection.append(payment.as_dict())

    rb.set_field('Collection', collection)
    return rb.build_response()


@router.get('/payment/result', response_class=HTMLResponse)
async def stripe_success(payment_attempt_id: str,
                         db: Session = Depends(get_db)):
    rb = ResponseBuilder()
    print('1111111111111111111111111111111111111111111111111111111')
    print(payment_attempt_id)
    status = get_and_update_payment_attempt_status_from_intent(
        payment_attempt_id, rb, db)

    msg = 'Thank you! Your payment is processing.'
    if status >= ATTEMPT_STATUS_WAITING_TO_PROCESS:
        msg = 'Thank you! Your payment was successful.'
        await process_payment_attempt(payment_attempt_id, rb, db)

    elif status == ATTEMPT_STATUS_FAILED:
        msg = 'Your payment failed. Please try again.'

    elif status == ATTEMPT_STATUS_WAITING_ON_STRIPE:
        msg = 'Your payment is still processing.'

    else:
        plog.critical(
            f'unknown payment_attempt.status for attempt_id = {payment_attempt_id}')

    return HTMLResponse(msg)


class PaymentAttemptStatusIn(ApiSchema):
    PaymentAttemptId: str

class PaymentAttemptStatusOut(ApiSchema):
    Status: int

@router.post('/paymentAttempt/status.getAndHandle',
             response_model=PaymentAttemptStatusOut)
async def is_payment_attempt_successful(request: Request,
                                        jin: PaymentAttemptStatusIn,
                                        db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    print('22222222222222222222222222222222222')
    print(jin.PaymentAttemptId)
    payment_attempt = db.query(StripePaymentAttempt).filter(
        StripePaymentAttempt.attempt_id == jin.PaymentAttemptId).first()  # type: ignore

    project: Project = db.query(Project).filter(
        Project.probius_id == payment_attempt.probius_id).first()  # type: ignore
    if project is None:
        return rb.missing_requirement_response('project')

    if policy_fails(rb, await Policies.is_user_admin_of_project(gibs, project),
                    inspection_count=2):
        return rb.policy_failed_response()

    status = get_and_update_payment_attempt_status_from_intent(
        jin.PaymentAttemptId, rb, db)

    rb.set_field('Status', status)
    if status == ATTEMPT_STATUS_WAITING_TO_PROCESS:
        await process_payment_attempt(jin.PaymentAttemptId, rb, db)
    
    return rb.build_response()

