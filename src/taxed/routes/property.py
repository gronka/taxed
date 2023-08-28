from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List
import uuid

from taxed.core import (
    ApiSchema,
    db_commit,
    EmptySchema,
    get_db,
    Gibs,
    Policies,
    policy_fails,
    PropertyIdIn,
    Puid,
    # puid_equals,
    ResponseBuilder,
    SurferIdIn,
)
from taxed.models import (
    Property,
)

router = APIRouter()


class PropertyCreateIn(ApiSchema):
    SurferId: Puid
    Address: str
    Street1: str
    Street2: str = ''
    City: str
    State: str
    Postal: str
    County: str = ''
    Country: str = ''

@router.post('/property/create', response_model=EmptySchema)
async def property_create(request: Request,
                          jin: PropertyCreateIn,
                          db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    #TODO: update all policy checks
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    prop = Property()
    prop.property_id = uuid.uuid4()
    prop.surfer_id = gibs.surfer_id()
    prop.address = jin.Address
    # prop.address = (f'{jin.Street}, {jin.Street2}, {jin.County}, {jin.City}, '
                  # f'{jin.State}, {jin.Postal}')
    prop.street_1 = jin.Street1
    prop.street_2 = jin.Street2
    prop.city = jin.City
    prop.county = jin.County
    # prop.country = jin.Country
    prop.country = "United States"
    prop.state = jin.State
    prop.postal = jin.Postal

    db.add(prop)
    db_commit(db, rb)

    return rb.build_response()


class PropertySchema(ApiSchema):
    PropertyId: Puid
    SurferId: Puid
    Category: str
    Notes: str
    # TimePurchased: int
    TimeUpdated: int
    Address: str
    Street1: str
    Street2: str
    City: str
    State: str
    County: str
    Country: str
    Postal: str
    ThumbUrl: str = ''

@router.post('/property/get.byId', response_model=PropertySchema)
async def property_get_by_id(request: Request,
                            jin: PropertyIdIn,
                            db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    prop: Property = db.query(Property).filter(
        Property.property_id == jin.PropertyId).first()  # type: ignore

    if prop is None:
        return rb.missing_requirement_response('property')

    rb.set_fields_with_dict(prop.as_dict())
    return rb.build_response()


@router.post('/property/delete', response_model=EmptySchema)
async def property_delete(request: Request,
                          jin: PropertyIdIn,
                          db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    prop: Property = db.query(Property).filter(
        Property.property_id == jin.PropertyId).first()  # type: ignore

    if prop is None:
        return rb.missing_requirement_response('property')

    db.delete(prop)
    db_commit(db, rb)
    return rb.build_response()


class PropertyCollection(ApiSchema):
    Collection: List[PropertySchema]
    IdList: List[str]

@router.post('/properties/get.bySurferId', response_model=PropertyCollection)
async def properties_get_by_surfer_id(request: Request,
                                      jin: SurferIdIn,
                                      db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    props = db.query(Property).filter(
        Property.surfer_id == jin.SurferId).all()  #type:ignore

    collection = []
    id_list = []
    for prop in props:
        collection.append(prop.as_dict())
        id_list.append(str(prop.property_id))

    rb.set_field('Collection', collection)
    rb.set_field('IdList', id_list)
    return rb.build_response()


class PropertyIdsIn(ApiSchema):
    PropertyIds: List[Puid]

@router.post('/properties/get.byIds', response_model=PropertyCollection)
async def properties_get_by_ids(request: Request,
                                jin: PropertyIdsIn,
                                db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    collection = []
    for id in jin.PropertyIds:
        prop: Property = db.query(Property).filter(
            Property.property_id == id).first()  #type:ignore
        if prop is None:
            return rb.missing_requirement_response('property')

        collection.append(prop.as_dict()) #type:ignore

    rb.set_field('Collection', collection)
    return rb.build_response()
