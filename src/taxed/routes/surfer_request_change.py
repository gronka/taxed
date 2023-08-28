from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from taxed.core import (
    ApiSchema,
    db_commit,
    EmailIn,
    EmptySchema,
    get_db,
    Gibs,
    in_x_minutes,
    nowstamp,
    plog,
    Policies,
    policy_fails,
    random_token,
    RequestChangeSchema,
    ResponseBuilder,
    send_email_simple,
    TokenIn,
)
from taxed.core.errors import (
    AccountNotFoundError,
    LoginToChangeEmailError,
    TokenExpiredError,
)
from taxed.models import (
    Surfer, 
    SurferChangeEmailRequest,
    SurferChangePasswordRequest,
)
from taxed.state import conf

router = APIRouter()


# works for both logged in and logged out
@router.post('/surfer/change.password.request', response_model=EmptySchema)
async def surfer_change_password_request(jin: EmailIn,
                                         db: Session = Depends(get_db)):
    rb = ResponseBuilder()
    if policy_fails(rb, await Policies.public()):
        return rb.policy_failed_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.email == jin.Email).first()  # type: ignore
    if surfer is None:
        rb.add_error(AccountNotFoundError)
        return rb.build_response()

    token = random_token()
    url = conf.make_url(f'surfer/change.password.link/{token}')

    plog.info(f'password change request for {surfer.surfer_id}, url:\n{url}')

    change_req = SurferChangePasswordRequest()
    change_req.token = token
    change_req.is_consumed = False
    change_req.surfer_id = surfer.surfer_id
    change_req.time_expires = int(in_x_minutes(60).timestamp())

    db.add(change_req)
    db_commit(db, rb)

    subject = 'FairlyTaxed: Password Change Requested'
    msg = ('Click the link below to change your password for your FairlyTaxed '
           'account.'
           f'\n\n{url}')
    send_email_simple(conf, conf.email_noreply, [surfer.email], subject, msg)

    return rb.build_response()


@router.post('/surfer/change.password.request.validate',
             response_model=RequestChangeSchema)
async def surfer_change_password_request_validate(
        jin: TokenIn,
        db: Session = Depends(get_db)):
    rb = ResponseBuilder()
    if policy_fails(rb, await Policies.public()):
        return rb.policy_failed_response()

    change_req: SurferChangePasswordRequest = db.query(
        SurferChangePasswordRequest).filter( #type:ignore
            SurferChangePasswordRequest.token == jin.Token).first() #type:ignore
    if change_req is None:
        return rb.missing_requirement_response('change_req')

    rb.set_field('IsConsumed', change_req.is_consumed)
    rb.set_field('SurferId', change_req.surfer_id)
    rb.set_field('TimeExpires', change_req.time_expires)
    return rb.build_response()


@router.post('/surfer/change.email.request', response_model=EmptySchema)
async def surfer_change_email_request(request: Request,
                                      db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.email_confirm_token == jin.Token).first()  # type: ignore
    if surfer is None:
        return rb.missing_requirement_response('surfer')

    token = random_token()
    url = conf.make_url(f'surfer/change.email.link/{token}')

    plog.info(f'email change request for {surfer.surfer_id}, url:\n{url}')

    change_req = SurferChangeEmailRequest()
    change_req.token = token
    change_req.is_applied = False
    change_req.is_consumed = False
    change_req.surfer_id = surfer.surfer_id
    change_req.time_expires = int(in_x_minutes(15).timestamp())
    db.add(change_req)
    db_commit(db, rb)

    subject = 'FairlyTaxed: Email Change Requested'
    msg = ('Click the link below to change your email for your FairlyTaxed '
           'account. You must be logged in for the link to work.'
           f'\n\n{url}')
    send_email_simple(conf, conf.email_noreply, [surfer.email], subject, msg)

    return rb.build_response()


@router.post('/surfer/change.email.request.validate',
             response_model=RequestChangeSchema)
async def surfer_change_email_request_validate(
        request: Request,
        jin: TokenIn,
        db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.email == jin.Email).first()  # type: ignore
    if surfer is None:
        return rb.missing_requirement_response('surfer')

    change_req: SurferChangeEmailRequest = db.query(
        SurferChangeEmailRequest).filter( #type:ignore
            SurferChangeEmailRequest.token == jin.Token).first() #type:ignore
    if change_req is None:
        return rb.missing_requirement_response('change_req')

    rb.set_field('IsConsumed', change_req.is_consumed)
    rb.set_field('SurferId', change_req.developer_id)
    rb.set_field('TimeExpires', change_req.time_expires)
    return rb.build_response()


class ChangeEmailIn(ApiSchema):
    Email: str
    Token: str

@router.post('/surfer/change.email', response_model=EmptySchema)
async def surfer_change_email(request: Request,
                              jin: ChangeEmailIn,
                              db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.surfer_id == jin.SurferId).first()  # type: ignore
    if surfer is None:
        rb.add_error(AccountNotFoundError)
        return rb.build_response()

    change_req: SurferChangeEmailRequest = db.query(
        SurferChangeEmailRequest).filter(
             SurferChangeEmailRequest.token == jin.Token).first() #type:ignore
    if change_req is None:
        return rb.missing_requirement_response('change_req')

    if policy_fails(rb, await Policies.is_user_this_surfer(
            gibs, surfer.surfer_id), inspection_count= 2):
        return rb.policy_failed_response()

    if str(surfer.surfer_id) != gibs.surfer_id:
        rb.add_error(LoginToChangeEmailError)
        return rb.build_response()

    if str(change_req.developer_id) != gibs.surfer_id:
        rb.add_error(LoginToChangeEmailError)
        return rb.build_response()

    if change_req.is_consumed or nowstamp() > change_req.time_expires:
        rb.add_error(TokenExpiredError)
        return rb.build_response()

    change_req.is_consumed = True
    change_req.new_email = jin.Email
    change_req.old_email = surfer.email

    subject = 'FairlyTaxed: Verify email change'
    url = conf.make_url('surfer/change.email.validate.new.link/'
                        f'{change_req.token}')
    msg = ('Click the link below to change your e-mail address for FairlyTaxed.'
           f'\n\n{url}')
    send_email_simple(conf, conf.email_noreply, [surfer.email], subject, msg)

    db.add(change_req)
    db.add(surfer)
    db_commit(db, rb)
    return rb.build_response()


@router.post('/surfer/change.email.validate.new.link', 
             response_model=EmptySchema)
async def surfer_change_email_validate_new_link(jin: TokenIn,
                                                db: Session = Depends(get_db)):
    rb = ResponseBuilder()
    if policy_fails(rb, await Policies.public()):
        return rb.policy_failed_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.email_confirm_token == jin.Token).first()  # type: ignore
    if surfer is None:
        return rb.missing_requirement_response('surfer')

    surfer.is_email_verified = True
    db.add(surfer)
    db_commit(db, rb)
    return rb.build_response()
