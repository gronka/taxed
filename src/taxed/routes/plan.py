from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import uuid

from taxed.core import (
    ApiError,
    ApiSchema,
    db_commit,
    get_db,
    Gibs,
    Policies,
    policy_fails,
    ProjectIdIn,
    Puid,
    ResponseBuilder,
)
from taxed.models import (
    Plan,
    PlanChangeRequest,
    Project,
)
from taxed.state import conf

router = APIRouter()


class PlanIdIn(ApiSchema):
    PlanId: Puid

class PlanSchema(ApiSchema):
    PlanId: Puid
    SortId: int

    BundledTokens: int
    Months: int
    Price: int
    PriceCurrency: str

    AdminNotes: str
    Description: str
    IsAvailable: bool
    IsTailored: bool
    Rules: str
    Title: str

@router.post('/plan/get.byId', response_model=PlanSchema)
async def plan_get_by_id(request: Request,
                            jin: PlanIdIn,
                            db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    plan: Plan = db.query(Plan).filter(
        Plan.plan_id == jin.PlanId).first()  # type: ignore
    if plan is None:
        return rb.missing_requirement_response('plan')

    rb.set_fields_with_dict(plan.as_dict())
    return rb.build_response()


PlanChangeError = ApiError(
    code='plan_change_error',
    msg='Error changing planIdNext')

class ProjectPlanIdNextChangeIn(ApiSchema):
     ProjectId: Puid
     PlanIdNext: str
     TermsAccepted: bool

@router.post('/project/planIdNext.change', response_model=ApiSchema)
async def project_plan_id_next_change(request: Request,
                                      jin: ProjectPlanIdNextChangeIn,
                                      db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()
    if not jin.TermsAccepted:
        rb.add_error(PlanChangeError)
        return rb.build_response()

    project: Project = db.query(Project).filter(
        Project.project_id == jin.ProjectId).first()  # type: ignore
    if project is None:
        return rb.missing_requirement_response('project')

    plan: Plan = db.query(Plan).filter(
        Plan.plan_id == jin.PlanIdNext).first()  # type: ignore
    if plan is None:
        return rb.missing_requirement_response('plan')

    project.plan_id_next = jin.PlanIdNext
    db.add(project)
    db_commit(db, rb)

    pcr = PlanChangeRequest()
    pcr.plan_change_id = str(uuid.uuid4())
    pcr.is_cancellation = False
    pcr.surfer_id = gibs.surfer_id()
    pcr.plan_id_next = jin.PlanIdNext
    pcr.project_id = str(jin.ProjectId)
    pcr.terms_accepted_version = conf.terms_version
    db.add(pcr)
    db_commit(db, rb)

    return rb.build_response()


@router.post('/project/planIdNext.cancel', response_model=ApiSchema)
async def project_plan_id_next_cancel(request: Request,
                                      jin: ProjectIdIn,
                                      db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    project: Project = db.query(Project).filter(
        Project.project_id == jin.ProjectId).first()  # type: ignore
    if project is None:
        return rb.missing_requirement_response('project')

    project.plan_id_next = project.plan_id
    db.add(project)
    db_commit(db, rb)

    pcr = PlanChangeRequest()
    pcr.plan_change_id = str(uuid.uuid4())
    pcr.is_cancellation = True
    pcr.surfer_id = gibs.surfer_id()
    pcr.plan_id_next = project.plan_id
    pcr.project_id = str(jin.ProjectId)
    pcr.terms_accepted_version = ''
    db.add(pcr)
    db_commit(db, rb)

    return rb.build_response()
