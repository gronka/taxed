from pydantic import BaseModel
from taxed.core import Puid
from taxed.core.mailer import make_mailer
from taxed.state import conf

class BillEmailData(BaseModel):
    surfer_id: Puid = ''
    body: str = ''
    from_: str = ''
    to_: str = ''
    project_id: Puid = ''
    subject: str = ''
    was_allow_email_bills_enabled: bool = False
    link: str = ''


def send_bill_alert(ad: BillEmailData):
    mailer = make_mailer(conf)
    mailer.send_email(ad.from_, ad.to_, ad.subject, ad.body)
