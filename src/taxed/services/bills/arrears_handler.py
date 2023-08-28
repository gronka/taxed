from sqlalchemy import and_
from sqlalchemy.orm import Session
from typing import List

from taxed.services.bills.bill_alerter import BillAlerter
from taxed.core import (
    Mailer,
    nowstamp,
)
from taxed.models import (
    Bill,
    BILL_STATUS_PAID,
    Probius,
    Project,
)


def does_project_have_past_due_bill(project: Project, db: Session) -> bool:
    bills: List[Bill] = db.query(Bill).filter(
        and_(Bill.project_id == project.project_id,
             Bill.status != BILL_STATUS_PAID)).all() #type:ignore

    for bill in bills:
        three_weeks = 60 * 60 * 24 * 21
        if (bill.time_created - nowstamp()) > three_weeks:
            return True

    return False


def refresh_arrears_status_steps(db: Session, mailer: Mailer):
    check_all_old_arrears_statuses(db)
    check_all_unpaid_bills(db, mailer)


def check_all_old_arrears_statuses(db: Session):
    projects: List[Project] = db.query(Project).filter( #type:ignore
        Project.is_in_arrears == True).all()

    for project in projects:
        if not does_project_have_past_due_bill(project, db):
            project.is_in_arrears = False
            db.add(project)
            db.commit()


def check_all_unpaid_bills(db: Session, mailer: Mailer):
    bills: List[Bill] = db.query(Bill).filter(
        Bill.status != BILL_STATUS_PAID).all() #type:ignore

    for bill in bills:
        three_weeks = 60 * 60 * 24 * 21
        if (bill.time_created - nowstamp()) > three_weeks:
            probius: Probius = db.query(Probius).filter( 
                Probius.probius_id == bill.probius_id).first() or Probius() #type:ignore

            probius.is_in_arrears = True
            db.add(probius)
            db.commit()

            ba = BillAlerter(bill, db, mailer)
            ba.alert_project_in_arrears()
