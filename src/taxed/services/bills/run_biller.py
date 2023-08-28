import socket
from sqlalchemy import and_
import sys
import time
from typing import List

from taxed.services.bills.arrears_handler import (
    refresh_arrears_status_steps,
)
from taxed.services.bills.bill_alerter import BillAlerter
from taxed.services.bills.bill_maker import BillMaker
from taxed.services.bills.bill_processor import BillProcessor
from taxed.core import (
    get_period_now,
    make_mailer,
    make_previous_period,
    now,
    plog,
    Puid,
    SessionLocal,
)
from taxed.models import (
    Bill,
    BILL_STATUS_CREATED,
    BILL_STATUS_PAID,
    BILL_STATUS_TRY_AGAIN,
    Project,
)
from taxed.state import conf


def make_bills(for_period: int):
    with SessionLocal() as db:
        try:
            projects: List[Project] = db.query(Project).all() #type:ignore
            for project in projects:
                bm = BillMaker(project, db, for_period)
                bm.make_monthly_bill_if_not_exists()

            plog.debug(f'DONE: bill_maker')

        except Exception as err:
            plog.exception('bill_maker failed:', err)

        db.close()


def alert_bill_ready_to_all(for_period: int):
    with SessionLocal() as db:
        mailer = make_mailer(conf)
        try:
            bills: List[Bill] = db.query(Bill).filter(
                and_(Bill.status == BILL_STATUS_CREATED, #type:ignore
                     Bill.period == for_period)).all() #type:ignore
            for bill in bills:
                ba = BillAlerter(bill, db, mailer)
                ba.alert_bill_ready()

            plog.debug(f'DONE: bill_reminder')

        except Exception as err:
            plog.exception('bill_processor failed:', err)

        db.close()


def try_to_pay_new_bills(for_period: int):
    with SessionLocal() as db:
        mailer = make_mailer(conf)
        try:
            bills: List[Bill] = db.query(Bill).filter(
                and_(Bill.status == BILL_STATUS_CREATED, #type:ignore
                     Bill.period == for_period)).order_by( #type:ignore
                         Bill.period.asc()).all() #type:ignore
            for bill in bills:
                ba = BillAlerter(bill, db, mailer)
                bp = BillProcessor(bill, db, ba)
                bp.try_to_pay_bill()

            plog.debug(f'DONE: bill_processor')

        except Exception as err:
            plog.exception('bill_processor failed:', err)

        db.close()


def try_to_pay_failed_bills(project_id: Puid):
    with SessionLocal() as db:
        mailer = make_mailer(conf)
        try:
            bills: List[Bill] = db.query(Bill).filter(
                and_(Bill.status == BILL_STATUS_TRY_AGAIN, #type:ignore
                     Bill.project_id == project_id)).order_by( #type:ignore
                         Bill.period.asc()).all() #type:ignore
            for bill in bills:
                ba = BillAlerter(bill, db, mailer)
                bp = BillProcessor(bill, db, ba)
                bp.try_to_pay_bill()

            plog.debug(f'DONE: bill_processor')

        except Exception as err:
            plog.exception('bill_processor failed:', err)

        db.close()


def alert_bill_late(for_period: int):
    with SessionLocal() as db:
        mailer = make_mailer(conf)
        try:
            bills: List[Bill] = db.query(Bill).filter(
                and_(Bill.status != BILL_STATUS_PAID, #type:ignore
                     Bill.period == for_period)).all() #type:ignore
            for bill in bills:
                ba = BillAlerter(bill, db, mailer)
                ba.alert_bill_payment_late()

            plog.debug(f'DONE: bill_reminder')

        except Exception as err:
            plog.exception('bill_processor failed:', err)

        db.close()


def refresh_arrears_status():
    with SessionLocal() as db:
        mailer = make_mailer(conf)
        try:
            refresh_arrears_status_steps(db, mailer)

            plog.debug(f'DONE: bill_reminder')

        except Exception as err:
            plog.exception('bill_processor failed:', err)

        db.close()


def listen_forever():
    while True:
        hours_16 = 57600
        time.sleep(hours_16)
        for_period: int = make_previous_period(get_period_now())

        if now().day == 1:
            make_bills(for_period)
            alert_bill_ready_to_all(for_period)

        if now().day == 7:
            try_to_pay_new_bills(for_period)

        if now().day == 14:
            alert_bill_late(for_period)

        if now().day == 21:
            refresh_arrears_status()


if __name__ == '__main__':
    print('if you pass an arg, use the format day=1,7,14,21 period=202201')

    print(sys.argv)
    if len(sys.argv) == 1:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            # create an abstract socket by prefixing it with null
            sock.bind('\0papi_biller_lock')
            listen_forever()
        except socket.error as err:
            err_code = err.args[0]
            err_msg = err.args[1]
            plog.error(f'Process already running {err_code}: {err_msg}')

    if len(sys.argv) == 2:
        day: int = int(sys.argv[1].split('=')[-1])
        for_period: int = make_previous_period(get_period_now())

        if day == 1:
            make_bills(for_period)
            alert_bill_ready_to_all(for_period)

        if day == 7:
            try_to_pay_new_bills(for_period)

        if day == 14:
            alert_bill_late(for_period)

        if day == 21:
            refresh_arrears_status()

    if len(sys.argv) == 3:
        day: int = int(sys.argv[1].split('=')[-1])
        for_period: int = int(sys.argv[2].split('=')[-1])

        if day == 1:
            make_bills(for_period)
            alert_bill_ready_to_all(for_period)

        if day == 7:
            try_to_pay_new_bills(for_period)

        if day == 14:
            alert_bill_late(for_period)

        if day == 21:
            refresh_arrears_status()
