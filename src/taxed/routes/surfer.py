from fastapi import APIRouter, Depends, Request
from pydantic import Field
from sqlalchemy.orm import Session
from typing import Literal
import uuid

from taxed.core import (
    ApiError,
    ApiSchema,
    db_commit,
    decode_jwt_long,
    create_surfer_jwt_long,
    create_surfer_jwt_short,
    EmptySchema,
    get_db,
    Gibs,
    in_x_months,
    nowstamp,
    plog,
    Policies,
    policy_fails,
    Puid,
    random_token,
    ResponseBuilder,
    SessionJwtIn,
    SurferIdIn,
    TokenIn,
)
from taxed.core.errors import (
    EmailNotVerifiedError,
    EmailRegisteredError,
    LoginFailedError,
)
from taxed.core import SurferSession
from taxed.helpers_routes.project import initialize_project_and_probius
from taxed.models import Project, Surfer
from taxed.mailers.verification import send_email_verification
from taxed.state import conf

router = APIRouter()


TODD_TYPES = Literal['admin', 'surfer']

class RegisterWithEmailIn(ApiSchema):
    Email: str = Field(
        min_length=5,
    )
    Password: str = Field(
        min_length=4,
    )

@router.post('/surfer/register.withEmail', response_model=EmptySchema)
async def surfer_register_with_email(jin: RegisterWithEmailIn,
                                     db: Session = Depends(get_db)):
    rb = ResponseBuilder()
    if policy_fails(rb, await Policies.public()):
        return rb.policy_failed_response()

    check_surfer = db.query(Surfer).filter(
        Surfer.email == jin.Email).first()  # type: ignore
    surfer = Surfer()
    if check_surfer:
        rb.add_error(EmailRegisteredError)
        return rb.build_response()

    surfer = Surfer()
    surfer.surfer_id = uuid.uuid4()
    surfer.is_email_verified = False
    surfer.is_phone_verified = False
    surfer.email = jin.Email
    surfer.password = conf.pwds.hash(jin.Password)
    # manually add admins to database
    surfer.is_admin = False
    # make the surfer and project_id the same
    surfer.project_id = surfer.surfer_id
    surfer.email_confirm_token = random_token()

    try:
        db.add(surfer)
        db_commit(db, rb)
        send_email_verification(surfer.email, surfer.email_confirm_token)
    except Exception as err:
        plog.wtf(err)
        surfer.delete()
        db_commit(db, rb)
        rb.add_error(ApiError('registration_failed', 'Registration failed.'))
    return rb.build_response()


class SignInIn(ApiSchema):
    Email: str = Field(
        min_length=5,
    )
    Password: str = Field(
        min_length=4,
    )
    InstanceId: str
    Platform: str

class SignInOut(ApiSchema):
    SurferId: Puid
    NewJwtShort: str
    NewJwtLong: str
    ToddType: TODD_TYPES

@router.post('/surfer/signIn.withEmail', response_model=SignInOut)
async def surfer_sign_in_with_email(jin: SignInIn,
                                    db: Session = Depends(get_db)):
    rb = ResponseBuilder()
    if policy_fails(rb, await Policies.public()):
        return rb.policy_failed_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.email == jin.Email).first()  # type: ignore
    if surfer is None:
        return rb.missing_requirement_response('surfer')

    if not surfer.is_email_verified:
        rb.add_error(EmailNotVerifiedError)
        return rb.build_response()

    if conf.pwds.verify(jin.Password, surfer.password):
        jwt_long = create_surfer_jwt_long(surfer.surfer_id,
                                          jin.InstanceId)
        jwt_short = create_surfer_jwt_short(surfer.surfer_id)

        rb.set_field('NewJwtLong', jwt_long)
        rb.set_field('NewJwtShort', jwt_short)
        rb.set_field('SurferId', str(surfer.surfer_id))

        check_session = db.query(SurferSession).filter(
            SurferSession.instance_id == jin.InstanceId).first()  # type: ignore
        if check_session:
            session = check_session
        else:
            session = SurferSession()

        session.instance_id = jin.InstanceId
        session.surfer_id = surfer.surfer_id
        session.jwt_long = jwt_long
        session.platform = jin.Platform
        session.time_last_used = int(nowstamp())
        session.time_expires = int(in_x_months(12).timestamp())
        db.add(session)
        db_commit(db, rb)

        #NOTE: look up project and create if not exists
        project: Project = db.query(Project).filter(
            Project.project_id == surfer.surfer_id).first()  # type: ignore
        if project is None:
            initialize_project_and_probius(db, rb, surfer)

    else:
        rb.add_error(LoginFailedError)

    if surfer.is_admin:
        rb.set_field('ToddType', 'admin')
    else:
        rb.set_field('ToddType', 'surfer')

    return rb.build_response()


@router.post('/surfer/signOut', response_model=EmptySchema)
async def surfer_sign_out(request: Request,
                          jin: SessionJwtIn,
                          db: Session = Depends(get_db)):
    gibs = Gibs(request, True); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    if gibs.is_jwt_long_valid(db):
        payload = decode_jwt_long(jin.SessionJwt)
        check_session = db.query(SurferSession).filter(
            SurferSession.instance_id == payload['InstanceId']).first()  # type: ignore
        if check_session is None:
            return rb.missing_requirement_response('check_session')

        db.delete(check_session)
        db_commit(db, rb)
    return rb.build_response()


@router.post('/surfer/email.verify', response_model=EmptySchema)
async def surfer_email_verify(jin: TokenIn,
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


@router.post('/surfer/delete', response_model=EmptySchema)
async def surfer_delete(request: Request,
                        jin: SurferIdIn,
                        db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.surfer_id == jin.SurferId).first()  # type: ignore
    if surfer is None:
        return rb.missing_requirement_response('surfer')

    if policy_fails(rb, await Policies.is_user_this_surfer(
            gibs, surfer.surfer_id), inspection_count=2):
        return rb.policy_failed_response()
    db.delete(surfer)
    db_commit(db, rb)
    return rb.build_response()


class SurferOut(ApiSchema):
    SurferId: Puid
    ProjectId: Puid
    Email: str
    Phone: str
    FirstName: str
    LastName: str
    IsEmailVerified: bool
    IsPhoneVerified: bool

@router.post('/surfer/get.byId', response_model=SurferOut)
async def surfer_get_by_id(request: Request,
                           jin: SurferIdIn,
                           db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.surfer_id == jin.SurferId).first()  # type: ignore
    if surfer is None:
        return rb.missing_requirement_response('surfer')

    if policy_fails(rb, await Policies.is_user_this_surfer(
            gibs, surfer.surfer_id), inspection_count=2):
        return rb.policy_failed_response()
    rb.set_fields_with_dict(surfer.as_dict())
    return rb.build_response()


class SetFirstNameIn(ApiSchema):
    SurferId: Puid
    FirstName: str

@router.post('/surfer/set.firstName', response_model=EmptySchema)
async def surfer_set_first_name(request: Request,
                                jin: SetFirstNameIn,
                                db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.surfer_id == jin.SurferId).first()  # type: ignore
    if surfer is None:
        return rb.missing_requirement_response('surfer')

    if policy_fails(rb, await Policies.is_user_this_surfer(
            gibs, surfer.surfer_id), inspection_count= 2):
        return rb.policy_failed_response()

    surfer.first_name = jin.FirstName
    db.add(surfer)
    db_commit(db, rb)
    return rb.build_response()


class SetLastNameIn(ApiSchema):
    SurferId: Puid
    LastName: str

@router.post('/surfer/set.lastName', response_model=EmptySchema)
async def surfer_set_last_name(request: Request,
                               jin: SetLastNameIn,
                               db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.surfer_id == jin.SurferId).first()  # type: ignore
    if surfer is None:
        return rb.missing_requirement_response('surfer')

    if policy_fails(rb, await Policies.is_user_this_surfer(
            gibs, surfer.surfer_id), inspection_count= 2):
        return rb.policy_failed_response()

    surfer.last_name = jin.LastName
    db.add(surfer)
    db_commit(db, rb)
    return rb.build_response()


class SetPhoneIn(ApiSchema):
    SurferId: Puid
    Phone: str

@router.post('/surfer/set.phone', response_model=EmptySchema)
async def surfer_set_phone(request: Request,
                           jin: SetPhoneIn,
                           db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.surfer_id == jin.SurferId).first()  # type: ignore
    if surfer is None:
        return rb.missing_requirement_response('surfer')

    if policy_fails(rb, await Policies.is_user_this_surfer(
            gibs, surfer.surfer_id), inspection_count= 2):
        return rb.policy_failed_response()

    surfer.phone = jin.Phone
    db.add(surfer)
    db_commit(db, rb)
    return rb.build_response()
