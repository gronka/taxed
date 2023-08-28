import ssl
import traceback

from taxed.conf import LogLevel
from taxed.core.mailer import send_email_error
from taxed.state import conf


MAIL_CONTEXT = ssl.create_default_context()


class TaxedLogger:
    def exception(self, msg, err: Exception | None = None):
        msg = f'TAXED_EXCEPTION: {msg}'
        if err:
            msg = f'{msg}\n{traceback.format_exc()}'
            send_email_error(conf, 'TAXED EXCEPTION', msg)

    def v(self, msg):
        if LogLevel.VERBOSE >= conf.log_level:
            print(f'TAXED_VERBOSE: {msg}')

    def verbose(self, msg):
        self.v(msg)

    def d(self, msg):
        if LogLevel.DEBUG >= conf.log_level:
            print(f'TAXED_DEBUG: {msg}')

    def debug(self, msg):
        self.d(msg)

    def i(self, msg):
        if LogLevel.INFO >= conf.log_level:
            print(f'TAXED_INFO: {msg}')

    def info(self, msg):
        self.i(msg)

    def w(self, msg):
        if LogLevel.WARNING >= conf.log_level:
            print(f'TAXED_WARNING: {msg}')

    def warning(self, msg):
        self.w(msg)

    def e(self, msg):
        msg = f'TAXED ERROR: {msg}'
        if LogLevel.ERROR >= conf.log_level:
            send_email_error(conf, 'TAXED ERROR', msg)
            print(f'TAXED_WARNING: {msg}')

    def error(self, msg):
        self.e(msg)

    def wtf(self, msg):
        msg = f'TAXED WTF: {msg}'
        if LogLevel.WTF >= conf.log_level:
            send_email_error(conf, 'TAXED WTF', msg)

    def critical(self, msg):
        self.wtf(msg)


plog = TaxedLogger()
