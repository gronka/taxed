from taxed.core.mailer import make_mailer
from taxed.state import conf


def send_email_verification(to_: str, token: str):
    subject = 'FairlyTaxed: Verify your e-mail'
    url = conf.make_url(f'email.confirm.link/{token}')
    msg = ('Click the link below to verify your e-mail address for FairlyTaxed.'
           f'\n\n{url}')

    mailer = make_mailer(conf)
    mailer.send_email(conf.email_noreply, to_, subject, msg)


def send_change_email_verification(to_: str, token: str):
    subject = 'FairlyTaxed: Verify email change'
    url = conf.make_url(f'change.email.validate.new.link/{token}')
    msg = ('Click the link below to change your e-mail address for FairlyTaxed.'
           f'\n\n{url}')

    mailer = make_mailer(conf)
    mailer.send_email(conf.email_noreply, to_, subject, msg)
