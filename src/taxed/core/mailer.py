from email.message import EmailMessage
from smtplib import SMTP, SMTPException
import ssl
from typing import List, Union

from taxed.conf import Conf


mailcon_type = Union[None, SMTP]

MAIL_CONTEXT = ssl.create_default_context()


def make_mailer(conf: Conf):
        return Mailer(conf.smtp_host, conf.smtp_user, conf.smtp_pass)


def send_email_simple(conf: Conf,
                      from_: str,
                      recipients: List[str],
                      subject: str,
                      body: str):
    mailer = make_mailer(conf)
    for recipient in recipients:
        mailer.send_email(from_,
                          recipient,
                          subject,
                          body)


def send_email_with_attachments(conf: Conf,
                                from_: str,
                                recipients: List[str],
                                subject: str,
                                body: str,
                                filepaths: List[str]):
    mailer = make_mailer(conf)
    for recipient in recipients:
        mailer.send_email_with_attachments(from_,
                                           recipient,
                                           subject,
                                           body,
                                           filepaths)


def send_email_error(conf: Conf,
                     subject: str,
                     body: str):
    send_email_simple(conf,
                      conf.email_errors,
                      [conf.email_error_recipients],
                      subject,
                      body)


class Mailer:
    def __init__(self,
                 smtp_host: str,
                 smtp_user: str,
                 smtp_pass: str):
        try:
            self.mailcon: mailcon_type = SMTP(smtp_host, 587)
            self.mailcon.starttls(context=MAIL_CONTEXT)
            self.mailcon.login(smtp_user, smtp_pass)
        except ConnectionRefusedError:
            print(f'failed to connect to smtp at {smtp_host}')
            self.mailcon: mailcon_type = None

    def send_email(self, from_: str, to_: str, subject: str, body: str):
        msg = EmailMessage()
        msg['From'] = from_
        msg['To'] = to_
        msg['Subject'] = subject
        # msg['Importance'] = 'high'
        msg.set_content(body)

        print(f'Attempt to send email to {to_}: {subject}\n{msg.get_body()}')

        if self.mailcon:
            try:
                self.mailcon.send_message(msg)
            except SMTPException as err:
                print(f'unable to send email to: {to_}')
                print(err)
        else:
            print(f'could not send email since no mailcon for: {to_}')

    def send_email_with_attachments(self, from_: str, to_: str, subject: str,
                                    body: str, filepaths: List[str]):
        msg = EmailMessage()
        msg['From'] = from_
        msg['To'] = to_
        msg['Subject'] = subject
        # msg['Importance'] = 'high'
        msg.set_content(body)

        for filepath in filepaths:
            filename = filepath.split('/')[-1]

            with open(filepath, 'rb') as fil:
                content = fil.read()
                msg.add_attachment(content,
                                   maintype='application',
                                   subtype='octet-stream',
                                   filename=filename)

        print(f'Attempt to send email to {to_}: {subject}\n{msg.get_body()}')

        if self.mailcon:
            try:
                self.mailcon.send_message(msg)
            except SMTPException as err:
                print(f'unable to send email to: {to_}')
                print(err)
        else:
            print(f'could not send email since no mailcon for: {to_}')
