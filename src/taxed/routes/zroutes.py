import datetime
from fastapi import APIRouter, Request

from taxed.core import ApiSchema, create_jwt_short, Gibs, plog

router = APIRouter()


class MakeJwtForUserSchema(ApiSchema):
    DeveloperId: str

class TokenSchema(ApiSchema):
    Token: str

@router.get('/mail_test')
async def mail_test():
    plog.wtf('email test')
    return

@router.post('/z/makeJwtForUser', response_model=TokenSchema)
async def z_make_jwt_for_user(jin: MakeJwtForUserSchema):
    # we can generate a long jwt here for testing
    token = create_jwt_short(to_encode={'DeveloperId': jin.DeveloperId},
                             expires_delta=datetime.timedelta(days=365))
    print(token)
    return {'Token': token}


@router.post('/z/tables.truncate')
async def z_truncate_tables(request: Request):
    gibs = Gibs(request)
    print(gibs)
    return {'Tables': 'wiped'}


@router.post('/z/print.jwt')
async def z_print_jwt(request: Request):
    gibs = Gibs(request)
    print(gibs.jwt_short)
    return {'NewJwtShort': gibs.jwt_short}


class HealthOut(ApiSchema):
    Name: str
    Health: str

@router.get('/z/health', response_model=HealthOut)
async def z_health():
    return {
        'Name': 'taxed',
        'Health': '100',
        'isOk': True,
    }


# @app.get('/apiv1/devices')
# async def devices(request):
    # devices = await Device.query.gino.all()
    # return response.json([device.to_dict() for device in devices])

# @app.get('/apiv1/devices/<id>')
# async def devices(request, id):
    # device = await Device.get(id)
    # return response.json(device.to_dict())

# @app.get('/apiv1/devices/<id>/<model>')
# async def devices(request, id, model):
    # device = await Device.get(id)
    # await device.update(model=model).apply()
    # return response.json(device.to_dict())
