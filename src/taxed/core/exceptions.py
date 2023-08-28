import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import (
    FastAPIError,
    HTTPException,
    RequestValidationError,
    WebSocketRequestValidationError)
from starlette.responses import PlainTextResponse


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(FastAPIError)
    async def fast_api_exception_handler(request: Request, exc: FastAPIError):
        print(f'Error processing route {request.url}')
        # import pdb; pdb.set_trace()
        print(exc)
        print(traceback.print_exc())
        return PlainTextResponse(str(exc), status_code=500)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        print(f'Error processing route {request.url}')
        # import pdb; pdb.set_trace()
        print(exc.detail)
        print(traceback.print_exc())
        return PlainTextResponse(str(exc), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request,
                                           exc: RequestValidationError):
        print(f'Error processing route {request.url}')
        # import pdb; pdb.set_trace()
        print(exc)
        print(traceback.print_exc())
        return PlainTextResponse(str(exc), status_code=422)

    @app.exception_handler(WebSocketRequestValidationError)
    async def web_socket_request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        print(f'Error processing route {request.url}')
        # import pdb; pdb.set_trace()
        print(exc)
        print(traceback.print_exc())
        return PlainTextResponse(str(exc), status_code=422)


authorization_exception = HTTPException(
    status_code=401,
    detail='Authorization failure.',
)


jwt_expired_exception = HTTPException(
    status_code=444,
    detail='JWT token expired.',
)


server_exception = HTTPException(
    status_code=500,
    detail='Server error.',
)


no_policy_applied_exception = HTTPException(
    status_code=500,
    detail='No policy has been applied.',
)


# class ApiException(Exception):
    # def __init__(self, name: str, status_code: int = 404, errors = List[str]):
        # self.name = name
        # self.status_code = status_code
        # self.errors = errors
