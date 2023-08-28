from sqlalchemy import BigInteger, Column, text
from sqlalchemy.dialects.postgresql import UUID
from typing import cast

from taxed.core import (
    Base,
    NonNullString,
    Puid,
    TimesMixin,
)


class Property(Base, TimesMixin):
    __tablename__ = 'properties'
    property_id = cast(Puid,
                       Column(UUID(as_uuid=True),
                              nullable=False,
                              primary_key=True,
                              server_default=text('uuid_generate_v4()'),
                              unique=True,
                              ))
    surfer_id = cast(Puid, Column(UUID(as_uuid=True), nullable=False))

    # category is commercial or residential
    category = cast(str, Column(NonNullString, nullable=False))
    notes = cast(str, Column(NonNullString, nullable=False))

    address = cast(str, Column(NonNullString, nullable=False))
    street_1 = cast(str, Column(NonNullString, nullable=False))
    street_2 = cast(str, Column(NonNullString, nullable=False))
    state = cast(str, Column(NonNullString, nullable=False))
    city = cast(str, Column(NonNullString, nullable=False))
    county = cast(str, Column(NonNullString, nullable=False))
    country = cast(str, Column(NonNullString, nullable=False))
    postal = cast(str, Column(NonNullString, nullable=False))

    time_purchased = cast(int, Column(BigInteger, nullable=False))

    def as_dict(self):
        return {
            **self.time_dict(),
            'PropertyId': self.property_id,
            'SurferId': self.surfer_id,

            'Category': self.category,
            'Notes': self.notes,

            'Address': self.address,
            'Street1': self.street_1,
            'Street2': self.street_2,
            'City': self.city,
            'State': self.state,
            'County': self.county,
            'Country': self.country,
            'Postal': self.postal,

            'TimePurchased': self.time_purchased,
            'TimeUpdated': self.time_updated,
        }
