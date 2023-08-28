import stripe

from taxed.state import conf


stripe.api_key = conf.stripe_secret_key
