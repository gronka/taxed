from fastapi import APIRouter, Request

# from .admin import router as admin_router
from .challenge import router as challenge_router
from .comparable import router as comparable_router
from .place_predictions import router as places_router
from .plan import router as plan_router
from .plastic import router as plastic_router
from .probius import router as probius_router
from .project import router as project_router
from .property import router as property_router
from .stripe import router as stripe_router
from .surfer import router as surfer_router
from .surfer_request_change import router as surfer_request_change_router
# from .surfer_apple import router as surfer_apple_router
# from .surfer_google import router as surfer_google_router
from .zroutes import router as zroutes_router

from taxed.state import conf

health_router = APIRouter()


@health_router.get('/')
async def path_root():
    return {'path': 'root'}


@health_router.get('/health')
async def path_health():
    return {'path': 'health'}


@health_router.get('/app')
def read_main(request: Request):
    return {
        'message': 'Hello World',
        'root_path': request.scope.get('root_path'),
    }


def attach_routes(app):
    if conf.taxed_env == 'dev' or conf.taxed_env == 'local':
        app.include_router(zroutes_router, prefix='')

    app.include_router(health_router)
    # app.include_router(health_router, prefix='')

    app.include_router(challenge_router, prefix='')
    app.include_router(comparable_router, prefix='')
    app.include_router(places_router, prefix='')
    app.include_router(plan_router, prefix='')
    app.include_router(plastic_router, prefix='')
    app.include_router(probius_router, prefix='')
    app.include_router(project_router, prefix='')
    app.include_router(property_router, prefix='')
    app.include_router(stripe_router, prefix='')
    app.include_router(surfer_router, prefix='')
    app.include_router(surfer_request_change_router, prefix='')
