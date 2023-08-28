from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from taxed.core import (
    ApiSchema,
    get_db,
    Gibs,
    Policies,
    policy_fails,
    PaymentIdIn,
    ProbiusIdIn,
    Puid,
    ResponseBuilder,
)
from taxed.models import (
    Payment,
    Probius,
    StripePaymentAttempt,
)

router = APIRouter()


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

    payment = db.query(Payment).filter(
        Payment.payment_id == jin.PaymentId).first()  # type: ignore
    if payment is None:
        return rb.missing_requirement_response('payment')

    probius: Probius = db.query(Probius).filter(
        Probius.probius_id == payment.probius_id).first()  # type: ignore
    if probius is None:
        return rb.missing_requirement_response('probius')
    if policy_fails(rb, await Policies.is_user_admin_of_probius(gibs, probius),
                    inspection_count= 2):
        return rb.policy_failed_response()

    rb.set_fields_with_dict(payment.as_dict())
    return rb.build_response()


@router.post('/payments/get.successful.byProbiusId',
             response_model=PaymentCollectionSchema)
async def payments_get_succesful_by_probius_id(request: Request,
                                               jin: ProbiusIdIn,
                                               db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    probius: Probius = db.query(Probius).filter(
        Probius.probius_id == jin.ProbiusId).first()  # type: ignore
    if probius is None:
        return rb.missing_requirement_response('probius')
    if policy_fails(rb, await Policies.is_user_admin_of_probius(gibs, probius),
                    inspection_count= 2):
        return rb.policy_failed_response()

    payments = db.query(Payment).filter(Payment.probius_id == jin.ProbiusId #type:ignore
        ).order_by(Payment.time_created.desc()).all()

    collection = []
    for payment in payments:
        collection.append(payment.as_dict())

    rb.set_field('Collection', collection)
    return rb.build_response()


@router.post('/payments/get.ccAttempts.byProbiusId',
             response_model=PaymentCollectionSchema)
async def payments_get_cc_attempts_by_probius_id(request: Request,
                                                 jin: ProbiusIdIn,
                                                 db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    probius: Probius = db.query(Probius).filter(
        Probius.probius_id == jin.ProbiusId).first()  # type: ignore
    if probius is None:
        return rb.missing_requirement_response('probius')
    if policy_fails(rb, await Policies.is_user_admin_of_probius(gibs, probius),
                    inspection_count= 2):
        return rb.policy_failed_response()

    payments = db.query(StripePaymentAttempt).filter(
        StripePaymentAttempt.probius_id == jin.ProbiusId #type:ignore
            ).order_by(StripePaymentAttempt.time_created.desc()).all()

    collection = []
    for payment in payments:
        collection.append(payment.as_dict())

    rb.set_field('Collection', collection)
    return rb.build_response()
