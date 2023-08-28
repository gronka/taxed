from fastapi import APIRouter, Depends
import requests
from sqlalchemy.orm import Session
import uuid

from taxed.core import (
    ApiSchema,
    db_commit,
    create_jwt_long,
    create_jwt_short,
    get_db,
    in_x_months,
    nowstamp,
    Policies,
    policy_fails,
    ResponseBuilder,
    SurferSession,
)

from taxed.core.errors import (
    FailedToValidateWithGoogleError,
)
from taxed.models import Surfer
from taxed.payments import stripe
from taxed.routes.surfer import SignInOut
from taxed.utils.tokens import generate_token

router = APIRouter()


class GoogleIn(ApiSchema):
    Token: str
    InstanceId: str
    Platform: str

@router.post('/surfer/signIn.withGoogle', response_model=SignInOut)
async def surfer_sign_in_with_google(jin: GoogleIn,
                                     db: Session = Depends(get_db)):
    rb = ResponseBuilder()
    if policy_fails(rb, await Policies.public()):
        return rb.policy_failed_response()

    url = 'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token='
    resp = requests.get(f'{url}{jin.Token}')

    resp_json = resp.json()
    google_email = resp_json.get('email', '')
    google_id = resp_json.get('user_id', '')
    expires_in = resp_json.get('expires_in', 0)

    if resp.status_code != 200 or \
            google_email == '' or \
            google_id == '' or\
            expires_in <= 0:
        rb.add_error(FailedToValidateWithGoogleError)
        return rb.build_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.email == google_email).first()  # type: ignore

    if not surfer:
        surfer = Surfer()
        surfer.surfer_id = uuid.uuid4()
        surfer.is_email_verified = True
        surfer.email = google_email
        surfer.google_id = google_id
        surfer.password = generate_token()

        customer = stripe.Customer.create(
            email=surfer.email,
            metadata={
                'surfer_id': surfer.surfer_id,
            }
        )

        surfer.stripe_customer_id = customer.id
        db.add(surfer)
        db_commit(db, rb)

    # google account can verify email
    if not surfer.is_email_verified:
        surfer.is_email_verified = True
        db.add(surfer)

    new_jwt_long = create_jwt_long({'SurferId': surfer.surfer_id,
                                    'InstanceId': jin.InstanceId})
    new_jwt_short = create_jwt_short({'SurferId': surfer.surfer_id,
                                      'InstanceId': jin.InstanceId})

    rb.set_field('NewJwtLong', new_jwt_long)
    rb.set_field('NewJwtShort', new_jwt_short)
    rb.set_field('SurferId', str(surfer.surfer_id))

    check_session = db.query(SurferSession).filter(
        SurferSession.instance_id == jin.InstanceId).first()  # type: ignore
    if check_session:
        session = check_session
    else:
        session = SurferSession()

    session.instance_id = jin.InstanceId
    session.surfer_id = surfer.surfer_id
    session.is_apple_session = False
    session.is_google_session = True
    session.session_jwt = new_jwt_long
    session.platform = jin.Platform
    session.time_last_used = int(nowstamp())
    session.time_expires = int(in_x_months(12).timestamp())
    db.add(session)
    db_commit(db, rb)

    return rb.build_response()
