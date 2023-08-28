from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from taxed.core import (
    ApiSchema,
    get_db,
    Gibs,
    Policies,
    policy_fails,
    Puid,
    ResponseBuilder,
)
from taxed.models import (
    Project
)

router = APIRouter()


class ProjectIdIn(ApiSchema):
    ProjectId: Puid

class ProjectSchema(ApiSchema):
    ProjectId: Puid
    CreatorId: Puid
    PlanId: str
    PlanIdNext: str
    ProbiusId: Puid

    Name: str
    Notes: str
    TimePlanExpires: int
    TimeCreated: int
    TimeUpdated: int

@router.post('/project/get.byId', response_model=ProjectSchema)
async def project_get_by_id(request: Request,
                            jin: ProjectIdIn,
                            db: Session = Depends(get_db)):
    gibs = Gibs(request); rb = ResponseBuilder()
    if policy_fails(rb, await Policies.is_user_signed_in(gibs, db, rb)):
        return rb.policy_failed_response()

    project: Project = db.query(Project).filter(
        Project.project_id == jin.ProjectId).first()  # type: ignore
    if project is None:
        return rb.missing_requirement_response('project')

    rb.set_fields_with_dict(project.as_dict())
    return rb.build_response()
