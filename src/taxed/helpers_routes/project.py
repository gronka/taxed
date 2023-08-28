from sqlalchemy.orm import Session
import uuid

from taxed.core import (
    db_commit,
    get_period_now,
    ResponseBuilder,
)
from taxed.models import (
    PLAN_FREE,
    Probius,
    Project,
    Surfer,
)
from taxed.payments import stripe


def initialize_project_and_probius(
        db: Session,
        rb: ResponseBuilder,
        surfer: Surfer):
    customer = stripe.Customer.create(
            email=surfer.email,
            metadata={
                'SurferId': surfer.surfer_id,
                }
            )

    probius = Probius()
    probius.probius_id = uuid.uuid4()
    probius.creator_id = surfer.surfer_id
    probius.project_id = surfer.surfer_id
    probius.first_period = get_period_now()
    probius.is_autopay_enabled = False
    probius.name = 'probius attached to project for surfer'
    probius.stripe_customer_id = customer.id
    probius.tokens_bought = 0
    probius.tokens_used = 0

    db.add(probius)
    db_commit(db, rb)

    project = Project()
    project.project_id = surfer.surfer_id
    project.creator_id = surfer.surfer_id
    project.plan_id = PLAN_FREE
    project.probius_id = probius.probius_id
    project.notes = 'project for surfer personal items'
    project.time_plan_expires = 0
    db.add(project)
    db_commit(db, rb)

    surfer.project_id = project.project_id
    db.add(surfer)
    db_commit(db, rb)
