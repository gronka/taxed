from sqlalchemy.orm import Session
from fastapi import Request
# from jose import exceptions
from typing import Mapping

# from taxed.core.plogger import plog
from taxed.core import (
    decode_jwt_long,
    decode_jwt_short,
    Puid,
    # jwt_expired_exception
    # ZEROS_UUID_STR,
)
from taxed.core.surfer_session import SurferSession


class Gibs:
    def __init__(self, request: Request, skip_processing = False):
        self.jwt_long_decoded: Mapping = {}
        self.jwt_short_decoded: Mapping = {}
        self.jwt_long: str = ''
        self.jwt_short: str = ''

        self.failed_auth_for_long: bool = False
        self.failed_auth_for_short: bool = False

        self.instance_id: str = ''
        self._surfer_id_long: Puid = ''
        self._surfer_id_short: Puid = ''

        if not skip_processing:
            self._process_jwt(request)

    def _process_jwt(self, request: Request) -> None:
        self.jwt_long = request.headers.get('JwtLong') or ''
        self.jwt_short = request.headers.get('JwtShort') or ''

        # plog.debug('JwtShort: ' + self.jwt_short)
        # plog.debug('JwtLong: ' + self.jwt_long)

        try:
            self.jwt_short_decoded = decode_jwt_short(self.jwt_short)
        # except exceptions.ExpiredSignatureError:
            self._surfer_id_short = str(self.jwt_short_decoded.get('SurferId', ''))
            self.instance_id = str(self.jwt_short_decoded.get('InstanceId', ''))
            # plog.debug(self.jwt_short_decoded)
            if self._surfer_id_short == '':
                self.failed_auth_for_short = True
        except Exception:
            self.failed_auth_for_short = True

        if not self.surfer_id():
            try:
                self.jwt_long_decoded = decode_jwt_long(self.jwt_long)
                self._surfer_id_long = str(self.jwt_long_decoded.get('SurferId', ''))
                self.instance_id = str(self.jwt_long_decoded.get('InstanceId', ''))
                # plog.debug(self.jwt_long_decoded)
                if self._surfer_id_long == '':
                    self.failed_auth_for_long = True
            except Exception:
                self.failed_auth_for_long = True

    def surfer_id(self) -> Puid:
        if self._surfer_id_short:
            return self._surfer_id_short
        elif self._surfer_id_long:
            return self._surfer_id_long
        return ''

    def is_jwt_short_valid(self) -> bool:
        if self._surfer_id_short and not self.failed_auth_for_short:
            return True
        return False

    def is_jwt_long_valid(self, db: Session) -> bool:
        instance_id: str = self.jwt_long_decoded.get('InstanceId') or ''

        check_session: SurferSession = db.query(SurferSession).filter(
            SurferSession.instance_id == instance_id).first()  # type: ignore

        if check_session is not None:
            if str(check_session.surfer_id) == self._surfer_id_long:
                return True
        return False
