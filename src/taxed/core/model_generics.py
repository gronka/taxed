from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, types
from sqlalchemy.ext.declarative import declarative_base
from typing import cast

from taxed.core import nowstamp


Base = declarative_base()


class NonNullBigInt(types.TypeDecorator):
    cache_ok = True
    impl = types.BigInteger
    def process_result_value(self, value, dialect):
        return value if value else 0


class NonNullBool(types.TypeDecorator):
    cache_ok = True
    impl = types.Boolean
    def process_result_value(self, value, dialect):
        return value if value else False


class NonNullInt(types.TypeDecorator):
    cache_ok = True
    impl = types.Integer
    def process_result_value(self, value, dialect):
        return value if value else 0

class NonNullString(types.TypeDecorator):
    cache_ok = True
    impl = types.Unicode
    def process_result_value(self, value, dialect):
        return value if value else ''


class TimesMixin(object):
    time_created = cast(int, Column(BigInteger,
                                    nullable=False,
                                    default=nowstamp,
                                    ))
    time_updated = cast(int, Column(BigInteger,
                                    nullable=False,
                                    default=nowstamp,
                                    onupdate=nowstamp,
                                    ))

    def not_found(self) -> bool:
        if self.time_created is None or self.time_created == 0:
            return True
        return False

    def time_dict(self):
        return  {
            'TimeCreated': self.time_created,
            'TimeUpdated': self.time_updated,
        }

    def datetime_created(self):
        return datetime.utcfromtimestamp(self.time_created)

    def datetime_updated(self):
        return datetime.utcfromtimestamp(self.time_updated)

    def month_created(self):
        return self.datetime_created.strftime('%m')

    def day_created(self):
        return self.datetime_created.strftime('%d')

    def update_time_updated(self):
        self.time_created = datetime.now(timezone.utc).timestamp()
