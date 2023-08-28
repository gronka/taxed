from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from taxed.core import (
    ApiSchema,
    ComparableIdIn,
    get_db,
    Gibs,
    Policies,
    policy_fails,
    Puid,
    ResponseBuilder,
)
from taxed.models import (
    Challenge,
    Comparable,
)

router = APIRouter()


class ComparableSchema(ApiSchema):
    ComparableId: Puid
    SurferId: Puid
    TargetPropertyId: Puid

    ChallengeDocName: str
    ComparableDocName: str
    FullAddress: str
    TimeCreated: int

@router.post('/comparable/get.byId', response_model=ComparableSchema)
async def comparable_get_by_id(request: Request,
                                      jin: ComparableIdIn,
                                      db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    comparable: Comparable = db.query(Comparable).filter(
        Comparable.comparable_id == jin.ComparableId).first()  #type:ignore
    if comparable is None:
        return rb.missing_requirement_response('comparable')

    challenge: Challenge = db.query(Challenge).filter(
        Challenge.challenge_id == comparable.challenge_id).first()  #type:ignore
    if policy_fails(rb, 
                    await Policies.is_user_admin_of_challenge(gibs, challenge),
                    inspection_count= 2):
        return rb.policy_failed_response()

    rb.set_fields_with_dict(comparable.as_dict())
    rb.set_field('ChallengeDocName', comparable.challenge_doc_name())
    rb.set_field('ComparableDocName', comparable.comparable_doc_name())
    rb.set_field('FullAddress', comparable.full_address())
    return rb.build_response()
