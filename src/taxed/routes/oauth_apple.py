from fastapi import APIRouter, Depends, Request
import jwt
import requests
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
import uuid

from taxed.core import (
    ApiSchema,
    create_jwt_long,
    create_jwt_short,
    db_commit,
    EmptySchema,
    get_db,
    in_x_months,
    nowstamp,
    plog,
    Policies,
    policy_fails,
    ResponseBuilder,
    SurferSession,
)

from taxed.core.errors import (
    FailedToValidateWithAppleError,
)
from taxed.models import Surfer
from taxed.payments import stripe
from taxed.routes.surfer import SignInOut
from taxed.state import conf
from taxed.utils.tokens import generate_token


router = APIRouter()

VALID_AUDIENCES = ['io.fairlytaxed.and', 'io.fairlytaxed.ios']

class IdTokenDetails:
    def __init__(self, id_token: str):
        dec = jwt.decode(id_token,
                             audience='https://appleid.apple.com',
                             options={"verify_signature": False},
                             algorithms=['ES256'],
                             )

        self.audience = dec.get('aud', '')
        self.email = dec.get('email', '')
        email_verified_str = dec.get('email_verified', False)
        self.is_email_verified = True if email_verified_str == 'true' else False
        self.exp: int = int(dec.get('exp', '0'))
        self.issuer = dec.get('iss', '')

        self.platform = 'notset'
        if self.audience == 'io.fairlytaxed.and':
            self.platform = 'android'
        if self.audience == 'io.fairlytaxed.ios':
            self.platform = 'ios'

    def get_client_id(self):
        return self.audience

    def is_valid(self):
        if self.issuer == 'https://appleid.apple.com' and \
                self.audience in VALID_AUDIENCES and \
                self.exp > nowstamp():
            return True
        return False


def make_client_secret(sub: str):
    headers = {
        'alg': 'ES256',
        'kid': conf.apple_sign_in_key_id,
    }

    payload = {
        'iss': conf.apple_team_id,
        'iat': nowstamp(),
        'exp': in_x_months(2).timestamp(),
        'aud': 'https://appleid.apple.com',
        'sub': sub,

        # 'c_hash': decoded['c_hash'],
        # 'email': decoded['email'],
        # 'email_verified': decoded['email_verified'],
        # 'nonce_supported': decoded['nonce_supported'],
    }

    return jwt.encode(
        payload,
        conf.apple_sign_in_p8,
        algorithm='ES256',
        headers=headers,
    )


def apple_24h_check(session: SurferSession) -> bool:
    url = 'https://appleid.apple.com/auth/token'
    headers = {'content-type': "application/x-www-form-urlencoded"}
    client_secret = make_client_secret(session.get_client_id())
    resp = requests.post(
        url,
        headers=headers,
        data={
            'client_id': session.get_client_id(),
            'client_secret': client_secret,
            'grant_type': 'refresh_token',  # OR 'refresh_token'
            'refresh_token': session.refresh_token_apple,
        },
    )

    apj = resp.json()
    if 'error' in apj:
        plog.error('invalid_client')

    apple_details = IdTokenDetails(apj.get('id_token', ''))
    #NOTE: basically, if email is set, then we can assume it's good
    if apple_details.email != '':
        return True
    else:
        return False


class AppleIn(ApiSchema):
    AuthCode: str
    IdToken: str
    InstanceId: str
    Platform: str

@router.post('/surfer/signIn.withApple', response_model=SignInOut)
async def surfer_sign_in_with_apple(jin: AppleIn,
                                    db: Session = Depends(get_db)):
    rb = ResponseBuilder()
    if policy_fails(rb, await Policies.public()):
        return rb.policy_failed_response()
    details_in = IdTokenDetails(jin.IdToken)

    url = 'https://appleid.apple.com/auth/token'
    headers = {'content-type': "application/x-www-form-urlencoded"}
    client_secret = make_client_secret(details_in.get_client_id())
    resp = requests.post(
        url,
        headers=headers,
        data={
            'client_id': details_in.get_client_id(),
            'client_secret': client_secret,
            'code': jin.AuthCode,
            'grant_type': 'authorization_code',  # OR 'refresh_token'
        },
    )

    apj = resp.json()
    if 'error' in apj:
        plog.error('invalid_client')
        rb.add_error(FailedToValidateWithAppleError)
        return rb.build_response()

    apple_details = IdTokenDetails(apj.get('id_token', ''))

    if not apple_details.is_valid():
        rb.add_error(FailedToValidateWithAppleError)
        return rb.build_response()

    surfer: Surfer = db.query(Surfer).filter(
        Surfer.email == apple_details.email).first()  # type: ignore

    if not surfer:
        surfer = Surfer()
        surfer.surfer_id = uuid.uuid4()
        surfer.is_email_verified = apple_details.is_email_verified
        surfer.email = apple_details.email
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

    # apple account can verify email
    if not surfer.is_email_verified:
        surfer.is_email_verified = apple_details.is_email_verified

    new_jwt_long = create_jwt_long({'SurferId': surfer.surfer_id,
                                    'InstanceId': jin.InstanceId})
    new_jwt_short = create_jwt_short({'SurferId': surfer.surfer_id,
                                      'InstanceId': jin.InstanceId})

    rb.set_field('NewJwtLong', new_jwt_long)
    rb.set_field('NewJwtShort', new_jwt_short)
    rb.set_field('SurferId', str(surfer.surfer_id))

    check_session = db.query(SurferSession).filter(
        SurferSession.instance_id == jin.instance_id).first()  # type: ignore
    if check_session:
        session = check_session
    else:
        session = SurferSession()

    session.instance_id = jin.InstanceId
    session.surfer_id = surfer.surfer_id
    session.is_apple_session = True
    session.is_google_session = False
    session.session_jwt = new_jwt_long
    session.platform = jin.Platform
    surfer.refresh_token_apple = apj.get('refresh_token', '')
    session.time_last_used = int(nowstamp())
    session.time_expires = int(in_x_months(12).timestamp())
    session.set_next_24h_check()
    db.add(session)
    db_commit(db, rb)

    return rb.build_response()

@router.post('/surfer/signIn.withApple.callback.android',
             response_model=EmptySchema)
async def surfer_sign_in_with_apple_callback(request: Request):
    prefix = 'intent://callback?'
    param_string = (await request.body()).decode('UTF-8')
    package = 'io.pushboi.and'
    suffix = f'#Intent;package={package};scheme=signinwithapple;end'
    redir = f'{prefix}{param_string}{suffix}'
    return RedirectResponse(redir, status_code=307)
