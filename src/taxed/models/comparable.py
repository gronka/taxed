import os
from sqlalchemy import Boolean, Column, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from typing import cast

from taxed.core import (
    Base,
    NonNullString,
    Puid,
    TimesMixin,
)
from taxed.state import conf


class Comparable(Base, TimesMixin):
    __tablename__ = 'comparables'
    comparable_id = cast(Puid,
                          Column(UUID(as_uuid=True),
                                 nullable=False,
                                 primary_key=True,
                                 server_default=text('uuid_generate_v4()'),
                                 unique=True,
                                 ))
    challenge_id = cast(Puid,
                        Column(UUID(as_uuid=True),
                               nullable=False,
                               ))
    # property_id is only set if this is the target_property
    property_id = cast(Puid,
                       Column(UUID(as_uuid=True),
                              ))
    target_property_id = cast(Puid,
                              Column(UUID(as_uuid=True),
                                     nullable=False,
                                     ))

    query_url = cast(str, Column(NonNullString, nullable=False))
    query_source = cast(str, Column(NonNullString, nullable=False))

    # damaged data is missing something like sq ft size or lot size. These
    # properties are fine to use, but in the future we might add more cases.
    is_data_damaged = cast(bool, Column(Boolean, nullable=False))
    marker_label = cast(str, Column(NonNullString, nullable=False))

    mortgage_holder = cast(str, Column(NonNullString, nullable=False))
    parcel_id = cast(str, Column(NonNullString, nullable=False))
    miles = cast(str, Column(NonNullString, nullable=False))
    sqft_living = cast(str, Column(Integer, nullable=False))
    sqft_lot = cast(str, Column(Integer, nullable=False))
    latitude = cast(str, Column(NonNullString, nullable=False))
    longitude = cast(str, Column(NonNullString, nullable=False))
    sale_date = cast(str, Column(NonNullString, nullable=False))
    sale_price = cast(str, Column(NonNullString, nullable=False))
    year_built = cast(str, Column(Integer, nullable=False))
    bath_count = cast(str, Column(NonNullString, nullable=False))
    bed_count = cast(str, Column(Integer, nullable=False))
    assessed_price_1 = cast(str, Column(NonNullString, nullable=False))
    assessed_price_2 = cast(str, Column(NonNullString, nullable=False))

    street_1 = cast(str, Column(NonNullString, nullable=False))
    city = cast(str, Column(NonNullString, nullable=False))
    state = cast(str, Column(NonNullString, nullable=False))
    postal = cast(str, Column(NonNullString, nullable=False))

    # not postgresql fields
    map_image: bytes = b''
    street_image: bytes = b''

    def as_dict(self):
        return {
            **self.time_dict(),
            'ComparableId': self.comparable_id,
            'ChallengeId': self.challenge_id,
            'TargetPropertyId': self.target_property_id,

            'QueryUrl': self.query_url,
            'QuerySource': self.query_source,
            'IsDataDamaged': self.is_data_damaged,
            'MarkerLabel': self.marker_label,

            'MortgageHolder': self.mortgage_holder,
            'ParcelId': self.parcel_id,
            'Miles': self.miles,
            'SqftLiving': self.sqft_living,
            'SqftLot': self.sqft_lot,
            'Latitude': self.latitude,
            'Longitude': self.longitude,
            'SaleDate': self.sale_date,
            'SalePrice': self.sale_price,
            'YearBuilt': self.year_built,
            'BathCount': self.bath_count,
            'BedCount': self.bed_count,

            'AssessedPrice1': self.assessed_price_1,
            'AssessedPrice2': self.assessed_price_2,

            'Street1': self.street_1,
            'City': self.city,
            'State': self.state,
            'Postal': self.postal,
        }

    # property_id does not exist for non-target properties
    def is_target(self) -> bool:
        return True if self.property_id == self.target_property_id else False

    def street_image_path(self):
        return os.path.join(conf.path_data,
                            'street',
                            f'{self.comparable_id}.jpg')

    def map_image_path(self):
        return os.path.join(conf.path_data,
                            'map',
                            f'{self.challenge_id}.jpg')

    def challenge_doc_name(self):
        short_id = str(self.challenge_id)[:8]
        name = (f'Challenge-{self.street_1}-{self.city}-{short_id}.docx')
        return name

    def challenge_doc_path(self):
        return os.path.join(conf.path_data,
                            'challenge',
                            self.challenge_doc_name())

    def comparables_doc_name(self):
        short_id = str(self.challenge_id)[:8]
        name = (f'Comparables-{self.street_1}-{self.city}-{short_id}.docx')
        return name

    def comparables_doc_path(self):
        return os.path.join(conf.path_data,
                            'comparables',
                            self.comparable_doc_name())

    def full_address(self):
        return (f'{self.street_1.lower().title()}, {self.city.lower().title()}, '
                f'{self.state.lower().title()}, {self.postal}')

    def full_address_short(self):
        return (f'{self.street_1.lower().title()}, {self.city.lower().title()}')
