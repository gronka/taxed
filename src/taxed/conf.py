import os
from passlib.context import CryptContext
from sqlalchemy.engine.url import URL
import sys
import toml
from typing import List


class LogLevel:
    VERBOSE = 10
    DEBUG = 20
    INFO = 30
    WARNING = 40
    ERROR = 50
    WTF = 60


class Conf:
    api_name = 'taxedapi'
    jwt_algorithm: str = 'HS256'
    jwt_algorithms: List[str] = ['HS256']
    jwt_short_lifetime_minutes: int = 0
    jwt_short_lifetime_seconds: int = 5
    jwt_long_lifetime_days: int = 365
    log_level: int = LogLevel.VERBOSE
    taxed_env: str = ''
    taxed_root: str = ''
    terms_version = '2.0'

    pwds= CryptContext(schemes=['bcrypt'], deprecated='auto')

    def __init__(self, skip_env: bool = False):
        # skip_env = True allows you to skip the forced env variable checks
        self.taxed_env = os.getenv('TAXED_ENV') or ''
        self.taxed_root = os.getenv('TAXED_ROOT') or ''

        if skip_env:
            print('Warning: using default env settings - could cause bugs')
            self.taxed_env = 'dev'
            self.taxed_root = '/tmp/taxed'
        else:
            if not self.taxed_env:
                raise RuntimeError('TAXED_ENV must be dev or local or prod')
            if not self.taxed_root:
                raise RuntimeError('TAXED_ROOT dir must be set')

        self.content_openxml = ('application/vnd.openxmlformats-officedocument.'
                                'wordprocessingml.document')
        self.content_openxml_sheet = ('application/vnd.openxmlformats-'
                                      'officedocument.wordprocessingml.sheet')

        with open('/taxed/certs/creds.toml', 'r')  as lf:
            pat = toml.loads(lf.read())
            self.smtp_host = pat['smtp']['host']
            self.smtp_pass = pat['smtp']['pass']
            self.smtp_user = pat['smtp']['user']
            from_domain = pat['smtp']['from_domain']
            self.email_errors = f'Fairly Taxed Errors <log@{from_domain}>'
            self.email_noreply = f'Fairly Taxed <noreply@{from_domain}>'
            self.email_documents = f'Fairly Taxed Documents <support@{from_domain}>'

            self.email_document_recipients = pat['smtp']['document_recipients']
            self.email_error_recipients = pat['smtp']['error_recipients']

            self.postgres_user = pat['database']['user']
            self.postgres_password = pat['database']['password']
            self.postgres_db = pat['database']['db']
            self.postgres_host = pat['database']['host']
            self.postgres_port = pat['database']['port']

            # tbg: jwt_long is for jwt-based log-out
            self.jwt_long_secret_key = pat['jwt']['long_secret']
            self.jwt_short_secret_key = pat['jwt']['short_secret']

            # not updated from trident
            self.attom_key = pat['apis-all']['attom_key']
            self.google_places_key = pat['apis-all']['google_places_key']
            self.google_staticmaps_key = pat['apis-all']['google_staticmaps_key']
            self.map_quest_key = pat['apis-all']['map_quest_key']

            self.path_base = os.path.join(pat['paths']['base'])
            self.path_data = os.path.join(pat['paths']['data'])
            self.path_templates = os.path.join(pat['paths']['templates'])

            #
            # OAuth
            #
            self.google_client_id = pat['auth']['google_client_id']
            self.google_client_secret = pat['auth']['google_client_secret']
            self.google_auth_token_key = pat['auth']['google_auth_token_key']
            self.google_auth_state_key = pat['auth']['google_auth_state_key']

            self.apple_team_id = pat['apple']['team_id']
            # apple_service_id = 'io.pusbhoi.ios'  # for web flows
            self.apple_bundle_id = pat['apple']['bundle_id']  # for apps
            self.apple_sign_in_key_id = pat['apple']['sign_in_key_id']
            self.apple_sign_in_key_contents = pat['apple']['sign_in_key_contents']
            self.apple_package_iden = pat['apple']['package_iden']

            # with open('/taxed/certs/AuthKey_xxxx_signInWithApple.p8',
                      # 'r') as fil:
                # self.apple_sign_in_p8 = fil.read()
            self.apple_sign_in_p8 = 'test_value'

        if self.taxed_env == 'dev' or self.taxed_env == 'local':
            self.attom_domain = pat['apis-dev']['attom_domain']
            self.paypal_api_prefix = pat['apis-dev']['paypal_api_prefix']
            self.paypal_cid = pat['apis-dev']['paypal_cid']
            self.paypal_secret = pat['apis-dev']['paypal_secret']
            self.stripe_publishable_key = pat['apis-dev']['stripe_publishable_key']
            self.stripe_secret_key = pat['apis-dev']['stripe_secret_key']

        elif self.taxed_env == 'prod':
            self.attom_domain = pat['apis-prod']['attom_domain']
            self.paypal_api_prefix = pat['apis-prod']['paypal_api_prefix']
            self.paypal_cid = pat['apis-prod']['paypal_cid']
            self.paypal_secret = pat['apis-prod']['paypal_secret']
            self.stripe_publishable_key = pat['apis-prod']['stripe_publishable_key']
            self.stripe_secret_key = pat['apis-dev']['stripe_secret_key']

        else:
            sys.exit('INVALID TAXED_ENV VALUE: ' + self.taxed_env)

        if not os.path.exists(self.path_data):
            sys.exit('DIR MISSING: /taxed/data')

        if self.postgres_password == '':
            sys.exit('No postgres password set')

        self.postgresql_dsn = URL.create(
            drivername='postgresql',
            username='postgres',
            password=self.postgres_password,
            host='localhost',
            port=None,
            database='fairly',
        )

        if self.is_dev():
            self.base_url = 'http://localhost/'
            self.image_url = 'http://localhost/'
        if self.is_local():
            self.base_url = 'http://localhost/'
            self.image_url = 'http://localhost/'
        if self.is_prod():
            self.base_url = 'https://fairlytaxed.com/'
            self.image_url = self.base_url

    def is_dev(self):
        if self.taxed_env == 'dev':
            return True
        return False

    def is_local(self):
        if self.taxed_env == 'local':
            return True
        return False

    def is_prod(self):
        if self.taxed_env == 'prod':
            return True
        return False

    def make_url(self, path: str):
        return f'{self.base_url}{path}'

    def make_image_url(self, path: str):
        return f'{self.image_url}{path}'
