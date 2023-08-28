from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from taxed.core import (
    ApiSchema,
    db_commit,
    get_db,
    Gibs,
    Policies,
    policy_fails,
    Puid,
    ResponseBuilder,
)
from taxed.models import (
    Probius,
    Project,
)

router = APIRouter()


class ProbiusIdIn(ApiSchema):
    ProbiusId: Puid

class ProbiusSchema(ApiSchema):
    ProbiusId: Puid
    CreatorId: Puid
    DefaultPlasticId: str
    ProjectId: Puid
    StripeCustomerId: str

    Credit: int
    Debt: int
    IsAutopayEnabled: bool
    TokensBought: int
    TokensUsed: int
    FirstPeriod: int
    IsBillOverdue: bool
    IsClosed: bool
    IsInArrears: bool
    Notes: str
    TimeLastBillIssued: int
    TimeLastPaidOff: int
    TimeCreated: int

@router.post('/probius/get.byId', response_model=ProbiusSchema)
async def probius_get_by_id(request: Request,
                            jin: ProbiusIdIn,
                            db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    probius: Probius = db.query(Probius).filter(
        Probius.probius_id == jin.ProbiusId).first()  # type: ignore
    if probius is None:
        return rb.missing_requirement_response('probius')

    project: Project = db.query(Project).filter(
        Project.probius_id == jin.ProbiusId).first()  # type: ignore
    if project is None:
        return rb.missing_requirement_response('project')
    if policy_fails(rb, await Policies.is_user_admin_of_project(gibs, project),
                    inspection_count= 2):
        return rb.policy_failed_response()

    rb.set_fields_with_dict(probius.as_dict())
    return rb.build_response()


class ToggleAutopayIn(ApiSchema):
    EnableAutopay: bool
    ProbiusId: Puid

@router.post('/probius/toggle.autopay', response_model=ApiSchema)
async def probius_toggle_autopay(request: Request,
                                 jin: ToggleAutopayIn,
                                 db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    probius: Probius = db.query(Probius).filter(
        Probius.probius_id == jin.ProbiusId).first()  # type: ignore
    if probius is None:
        return rb.missing_requirement_response('probius')

    if not probius.default_plastic_id:
        return rb.missing_requirement_response('probius.default_plastic_id')

    if policy_fails(rb, await Policies.is_user_admin_of_probius(gibs, probius),
                    inspection_count= 2):
        return rb.policy_failed_response()

    probius.is_autopay_enabled = jin.EnableAutopay
    if not jin.EnableAutopay:
        probius.default_plastic_id = ''
    db.add(probius)
    db_commit(db, rb)

    return rb.build_response()
