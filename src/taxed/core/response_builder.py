from typing import List
# from fastapi import status  #TODO: use library
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from taxed.core.exceptions import no_policy_applied_exception
from taxed.core.generics import ApiError
from taxed.validation import Validation


class ResponseBuilder:
    def __init__(self):
        self._body: dict = {}
        self._errors: List[ApiError] = []
        self.policy_inspections: int = 0
        #TODO: decide if we should also always inspect requirements
        # self._requirements_inspected: bool = False

    def build_response(self, status_code: int = 200):
        '''Determines what the body of the response should be. If there are
        errors, the response is replaced with an error response. This skips
        the normal schema validation process.
        '''
        if self.policy_inspections == 0:
            raise no_policy_applied_exception

        if self._errors:
            errors = [error.to_dict() for error in self._errors]
            return JSONResponse(
                status_code=status_code,
                content={'errors': errors,
                         'errored': True,
                         },
            )
        return self._body

    def missing_requirement_response(self, name: str):
        error = ApiError(
            code='missing_requirement',
            msg=f'{name} not found.')
        return JSONResponse(
            status_code=200,
            content={'errors': [error.to_dict()]})

    def add_error(self, error: ApiError):
        self._errors.append(error)

    def read_validation(self, validation: Validation):
        for error in validation.api_errors:
            self.add_error(error)
        for message in validation.messages:
            self.add_error(ApiError(
                code='validation_error',
                msg=message,
            ))

    @property
    def has_errors(self):
        return True if self._errors else False

    def set_field(self, key: str, value):
        if key in self._body:
            raise HTTPException(
                status_code=500,
                detail=f'Server attempted to set key "{key}" twice.')
        self._body[key] = value

    def set_fields_with_dict(self, obj: dict):
        for key in obj.keys():
            if key in self._body:
                raise HTTPException(
                    status_code=500,
                    detail=f'Server attempted to set key "{key}" twice.')
        # self._body = self._body | obj  # only supported in python3.9.0+
        self._body = {**self._body, **obj}

    def policy_failed_response(self):
        return JSONResponse(
                status_code=200,
                content={
                    'errors': [
                        ApiError(
                            code='policy_failed',
                            msg=f'Policy failed on #{self.policy_inspections}.',
                            ).to_dict()
                        ]
                    }
                )

