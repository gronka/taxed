from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from taxed.core.exceptions import register_exception_handlers
from taxed.routes import attach_routes
from taxed.state import conf


def create_app() -> FastAPI:
    app = FastAPI(
        title=conf.api_name,
        root_path='/api',
    )
    # v1_attach_routes(app)
    attach_routes(app)

    # TODO: set origins for production launch
    # origins = [
        # 'http://localhost',
        # 'http://127.0.0.1',
        # 'http://localhost:8000',
        # 'http://127.0.0.1:8000',
    # ]

    app.add_middleware(
        CORSMiddleware,
        # allow_origins=origins,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount('/static', StaticFiles(directory='static'), name='static')

    register_exception_handlers(app)

    return app
