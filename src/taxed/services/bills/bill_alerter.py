from sqlalchemy.orm import Session

from taxed.core import (
    Mailer,
    plog,
    )
from taxed.models import (
    Bill,
    Probius,
    Surfer,
)
from taxed.mailers.bill import BillEmailData, send_bill_alert
from taxed.state import conf


class BillAlerter:
    def __init__(self, bill: Bill, db: Session, mailer: Mailer):
        self.bill = bill
        self.db = db
        self.mailer = mailer

        # NOTE: surfer and projecct_id are the same
        # project: Project = db.query(Project).filter(
            # Project.project_id == jin.ProjectId).first()  # type: ignore
        probius: Probius = db.query(Probius).filter(
            Probius.probius_id == bill.probius_id).first()  # type: ignore
        if probius is None:
            plog.wtf(f'probius not found for bill_id: {bill.bill_id}')
            return

        surfer: Surfer = db.query(Surfer).filter(
            Surfer.project_id == probius.project_id).first()  # type: ignore
        if surfer is None:
            plog.wtf(f'surfer not found for project_id: {probius.project_id}')
            return

        self.bed = BillEmailData()
        self.bed.from_ = conf.email_noreply
        self.bed.to_ = surfer.email if surfer else ''
        self.bed.project_id = bill.project_id
        self.link = conf.make_url('/bill/{self.bill.bill_id}')

    # 01
    def alert_bill_ready(self):
        self.bed.subject = 'FairlyTaxed: Your bill is ready'

        self.bed.body = (
            'Your bill for FairlyTaxed is ready. If you have autopayment '
            'enabled or credit on your project, then your bill will '
            'automatically be paid on the 7th of the month. If you bill is '
            'unpaid for 2 weeks, then limits will be placed on your project. '
            'Click the link below to view your bill.'
            f'<br /><a href="{self.link}">{self.link}</a>')

        send_bill_alert(self.bed)

    # 02.a
    def alert_bill_due_now(self):
        self.bed.subject = 'FairlyTaxed: Your bill is due today'

        self.bed.body = (
            'Your bill for FairlyTaxed is due today. Autopayment was not '
            'enabled so you must complete the payment manually. Click the link '
            'below to view your bill.'
            f'<br /><a href="{self.link}">{self.link}</a>')
        send_bill_alert(self.bed)

    # 02.b
    def alert_bill_paid(self):
        self.bed.subject = 'FairlyTaxed: Your bill has been paid'

        self.bed.body = (
                'Your bill for FairlyTaxed has been paid. Click the link below '
                f'to view it.'
                f'<br /><a href="{self.link}">{self.link}</a>')
        send_bill_alert(self.bed)

    # 02.c
    def alert_bill_payment_failed(self):
        self.bed.from_ = conf.email_noreply
        self.bed.subject = 'ATTENTION: You FairlyTaxed payment has failed'

        self.bed.body = (
            'A payment has failed for your FairlyTaxed bill. If your bill '
            'remains unpaid on the 21st of the month, then limits will be '
            'applied to this project. Click the link below to view your bill.'
            f'<br /><a href="{self.link}">{self.link}</a>')
        send_bill_alert(self.bed)

    # 03
    def alert_bill_payment_late(self):
        self.bed.from_ = conf.email_noreply
        self.bed.subject = 'ATTENTION: Your FairlyTaxed payment is late'

        self.bed.body = (
            'Your payment for FairlyTaxed is 1 week late. If your bill '
            'remains unpaid on the 21st of the month, then limits will be '
            'applied to this project. Click the link below to view your bill.'
            f'<br /><a href="{self.link}">{self.link}</a>')
        send_bill_alert(self.bed)

    # 04
    def alert_project_in_arrears(self):
        self.bed.from_ = conf.email_noreply
        self.bed.subject = 'ATTENTION: your FairlyTaxed project has been limited'

        self.bed.body = (
            'Your FairlyTaxed project payment is 2 weeks past due. Therefore, '
            'we have limited your ability to send new notifications. Click the '
            'link below to view your bill.'
            f'<br /><a href="{self.link}">{self.link}</a>')
        send_bill_alert(self.bed)
