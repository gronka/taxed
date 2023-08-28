import json
from sqlalchemy import and_
from sqlalchemy.orm import Session
from typing import List
import uuid

from taxed.core import (
    timestamps_from_period,
)
from taxed.models import (
    Bill,
    BILL_TYPE_MONTHLY,
    BILL_STATUS_CREATED,
    Charge,
    Probius,
)


class BillMaker:
    def __init__(self, probius: Probius, db: Session, for_period):
        self.probius = probius
        self.db = db
        self.for_period = for_period

    def make_monthly_bill_if_not_exists(self):
        bill: Bill = self.db.query(Bill).filter(
            and_(Bill.probius_id == self.probius.probius_id, #type:ignore
                 Bill.period == self.for_period)).first() #type:ignore
        if bill:
            return

        bill = Bill()
        bill.bill_id = uuid.uuid4()
        bill.period = self.for_period
        bill.probius_id = self.probius.probius_id
        bill.status = BILL_STATUS_CREATED
        bill.currency = 'USD'
        bill.was_autopay_used = False

        start, end = timestamps_from_period(self.for_period)
        charges: List[Charge] = self.db.query(Charge).filter(
            and_(Charge.probius_id == self.probius.probius_id, #type:ignore
                 Charge.time_created.between(start, end))).all()

        total = 0
        charge_ids: List[str] = []
        for charge in charges:
            total = total + charge.price #type:ignore
            charge_ids.append(str(charge.charge_id))

        bill.bill_type = BILL_TYPE_MONTHLY
        bill.charge_ids = json.dumps(charge_ids)
        bill.price = total

        self.db.add(bill)
        self.db.commit()
