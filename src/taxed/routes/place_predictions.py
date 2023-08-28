from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import json
from typing import List
import requests

from taxed.core import (
    ApiSchema,
    get_db,
    Gibs,
    plog,
    Policies,
    policy_fails,
    ResponseBuilder,
)
from taxed.state import conf

router = APIRouter()


# AC = autocomplete
class AcIn(ApiSchema):
    Input: str
    Lat: str
    Long: str

class AcOut(ApiSchema):
    Address: str
    PlaceId: str

def parse_ac(ac: dict) -> AcOut:
    out = AcOut(
        Address=ac['description'],
        PlaceId=ac['place_id'],
    )
    return out

class AcCollection(ApiSchema):
    Collection: List[AcOut]

@router.post('/place/predictions.get', response_model=AcCollection)
async def place_predictions_get(request: Request,
                                jin: AcIn,
                                db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    url = ('https://maps.googleapis.com/maps/api/place/autocomplete/json'
           f'?input={jin.Input}'
           '&inputtype=textquery'
           f'&locationbias=circle%3A2000%40{jin.Lat}%2C{jin.Long}'
           '&fields=formatted_address'
           '%2Cplace_id'
           '%2Cname'
           f'&key={conf.google_places_key}')

    payload={}
    headers = {}
    resp = requests.request("GET", url, headers=headers, data=payload)

    collection: List[AcOut] = []
    if resp.status_code < 200 or resp.status_code > 299:
        plog.error('Failed to perform autocomplete:\n'
                   f'Input: {jin.Input}'
                   f'HTTP Code: {resp.status_code}')
    else:
        jon = resp.json()
        for ac in jon['predictions']:
            collection.append(parse_ac(ac))

    rb.set_field('Collection', collection)
    return rb.build_response()


class PlaceIdIn(ApiSchema):
    PlaceId: str

class PlaceOut(ApiSchema):
    Address: str
    City: str
    County: str
    Country: str
    Postal: str
    State: str
    StreetNumber: str
    StreetName: str
    Street2: str
    PlaceId: str

def parse_place(jon: dict) -> PlaceOut:
    result = jon['result']
    out = PlaceOut(
        Address=result['formatted_address'],
        City='',
        County='',
        Country='',
        Postal='',
        State='',
        StreetNumber='',
        StreetName='',
        Street2='',
        PlaceId=result['place_id'],
    )

    print(json.dumps(result, indent=4))

    for component in result['address_components']:
        types = component['types']
        value = component['long_name']

        print(component)
        print(types)
        print('locality' in types)
        print('sublocality' in types)
        print('sublocality_level_1' in types)

        if 'street_number' in types:
            out.StreetNumber = value
            print('streetnum: ' + value)

        elif 'route' in types:
            out.StreetName = value
            print('streetname: ' + value)

        elif 'locality' in types \
                or 'sublocality' in types \
                or 'sublocality_level_1' in types:
            out.City = value
            print('city: ' + value)

        elif 'administrative_area_level_1' in types:
            out.State = value
            print('state: ' + value)

        elif 'administrative_area_level_2' in types:
            out.County = value
            print('county: ' + value)

        elif 'country' in types:
            out.Country = value
            print('country: ' + value)

        elif 'postal_code' in types:
            out.Postal = value
            print('postal: ' + value)

        elif 'subpremise' in types \
                or 'administrative_area_level_2' in types \
                or 'neighborhood' in types \
                or 'postal_code_suffix' in types:
            print('none: ' + value)

        else:
            plog.wtf(f'unrecognized Google Places type: {types} for\n {jon}')

        print('---')

    print(out)
    return out

@router.post('/place/get.byPlaceId', response_model=PlaceOut)
async def place_get_by_place_id(request: Request,
                                jin: PlaceIdIn,
                                db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    url = ('https://maps.googleapis.com/maps/api/place/details/json'
           f'?place_id={jin.PlaceId}'
           '&fields=place_id'
           '%2Caddress_components'
           '%2Cformatted_address'
           f'&key={conf.google_places_key}')

    payload={}
    headers = {}
    resp = requests.request("GET", url, headers=headers, data=payload)

    if resp.status_code < 200 or resp.status_code > 299:
        plog.error('Failed to lookup Place from PlaceId:\n'
                   f'PlaceId: {jin.PlaceId}'
                   f'HTTP Code: {resp.status_code}')
    else:
        jon = resp.json()
        place = parse_place(jon)
        rb.set_fields_with_dict(dict(place))

    return rb.build_response()
