from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
import requests
from sqlalchemy.orm import Session
from typing import Dict

from taxed.core import (
    ApiError,
    ApiSchema,
    db_commit,
    EmptySchema,
    get_db,
    Gibs,
    plog,
    Policies,
    policy_fails,
    ProbiusIdIn,
    Puid,
    ResponseBuilder,
)
from taxed.models import (
    Probius,
)
from taxed.payments import stripe
from taxed.state import conf

router = APIRouter()

AgreementMustBeAcceptedError = ApiError(
    code='agreement_not_accepted',
    msg='You must accept the terms and conditions.')


class PlasticSchema(EmptySchema):
    PlasticId: str
    Brand: str
    Country: str
    ExpMonth: int
    ExpYear: int
    IsDefault: bool
    Last4: str

class PlasticKV(ApiSchema):
    KV: Dict[str, PlasticSchema]

@router.post('/probius/plastics/get.all.byProbiusId',
             response_model=PlasticKV)
async def probius_plastics_get_all_by_probius_id(request: Request,
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


    url = ('https://api.stripe.com/v1/customers/'
           f'{probius.stripe_customer_id}/payment_methods')
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Bearer {conf.stripe_secret_key}',
    }
    params = {'type': 'card'}

    resp = requests.get(
        url,
        headers=headers,
        params=params,
    )

    apj = resp.json()

    kv = {}
    if 'data' in apj:
        for datum in apj['data']:
            plastic_id = datum['id']
            is_default = probius.default_plastic_id == plastic_id
            card = datum['card']
            plastic = PlasticSchema(
                PlasticId=plastic_id,
                Brand=card['brand'],
                Country=card['country'],
                ExpMonth=card['exp_month'],
                ExpYear=card['exp_year'],
                IsDefault=is_default,
                Last4=card['last4'],
            )

            if is_default:
                print(f'default card: {plastic.Last4}, {plastic.ExpYear}')
            else:
                print(f'{plastic.Last4}, {plastic.ExpYear}')

            kv[plastic.PlasticId] = plastic
    else:
        plog.wtf(apj)
    print(kv)

    rb.set_field('KV', kv)
    print(rb._body)
    return rb.build_response()


class ProbiusIdSchema(ApiSchema):
    ProbiusId: Puid

class ProbiusAddPlasticOut(ApiSchema):
    StripeUrl: str

@router.post('/probius/plastic.add', response_model=ProbiusAddPlasticOut)
async def probius_plastic_add(request: Request,
                              jin: ProbiusIdSchema,
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

    # success/cancel url are called after a card is added
    pre = f'{request.base_url}probius/change.defaultCard'
    success_url = f'{pre}.success'
    cancel_url = f'{pre}.cancel'

    session = stripe.checkout.Session.create(
        customer=probius.stripe_customer_id,
        payment_method_types=['card'],
        mode='setup',
        success_url=success_url,
        cancel_url=cancel_url,
    )

    rb.set_field('StripeUrl', session.url)
    return rb.build_response()


class PlasticDeleteIdIn(ApiSchema):
    PlasticId: Puid
    ProbiusId: Puid

@router.post('/probius/plastic.delete', response_model=EmptySchema)
async def probius_plastic_delete(request: Request,
                                 jin: PlasticDeleteIdIn,
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

    url = ('https://api.stripe.com/v1/payment_methods/'
           f'{jin.PlasticId}/detach')
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Bearer {conf.stripe_secret_key}',
    }

    resp = requests.post(
        url,
        headers=headers,
    )

    apj = resp.json()
    print(apj)

    if probius.default_plastic_id == jin.PlasticId:
        probius.default_plastic_id = ''
        db.add(probius)
        db_commit(db, rb)

    return rb.build_response()


class ProbiusChangeDefaultPlasticIdIn(ApiSchema):
    DefaultPlasticId: str
    ProbiusId: str
    TermsAcceptedVersion: str

#NOTE: this route sets the autopay method
@router.post('/probius/change.defaultPlasticId', response_model=EmptySchema)
async def probius_change_default_plastic_id(
        request: Request,
        jin: ProbiusChangeDefaultPlasticIdIn,
        db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    if not jin.TermsAcceptedVersion:
        rb.add_error(AgreementMustBeAcceptedError)
        return rb.build_response()

    #TODO: check that plastic id exists for developer on stripe
    probius = db.query(Probius).filter(
       Probius.probius_id == jin.ProbiusId).first() #type:ignore
    if probius is None:
        return rb.missing_requirement_response('probius')
    if policy_fails(rb, await Policies.is_user_admin_of_probius(gibs, probius),
                    inspection_count= 2):
        return rb.policy_failed_response()


    probius.default_plastic_id = jin.DefaultPlasticId
    db.add(probius)
    db_commit(db, rb)

    probius.is_autopay_enabled = True
    db.add(probius)
    db_commit(db, rb)
    return rb.build_response()


@router.get('/probius/change.defaultCard.success', response_class=HTMLResponse)
async def payment_method_change_success():
    msg = 'Success! Reload the previous page to use your card.'
    return HTMLResponse(msg)


@router.get('/probius/change.defaultCard.cancel', response_class=HTMLResponse)
async def payment_method_change_cancel():
    msg = 'Your card was not saved.'
    return HTMLResponse(msg)
