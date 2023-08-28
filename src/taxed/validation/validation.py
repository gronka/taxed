from typing import List

from taxed.core import ApiError


class Validation:
    def __init__(self):
        self.api_errors: List[ApiError] = []
        self.is_valid: bool = True
        self.messages: List[str] = []

    @property
    def is_not_valid(self) -> bool:
        return not self.is_valid

    def add_error(self, msg: str) -> None:
        self.is_valid = False
        self.messages.append(msg)

    def add_api_error(self, api_error: ApiError) -> None:
        self.is_valid = False
        self.api_errors.append(api_error)

    def perform(self, val: 'Validation'):
        for message in val.messages:
            self.add_error(message)

        for api_error in val.api_errors:
            self.add_api_error(api_error)
