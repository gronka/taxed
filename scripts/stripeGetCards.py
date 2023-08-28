#!/usr/bin/env python
import requests
from taxed.conf import Conf

conf = Conf(skip_env=True)

url = 'https://api.stripe.com/v1/customers/cus_Nnvqg5lN0nagvW/payment_methods'
headers = {
    'content-type': 'application/json',
    'Authorization': f'Bearer {conf.stripe_secret_key}'
}
params = {'type': 'card'}

def send_message():
    resp = requests.get(
        url,
        headers=headers,
        params=params,
        )

    if resp.status_code < 200 or resp.status_code > 299:
        print(f'STATUS CODE {resp.status_code}')
    else:
        print(resp)
        print(resp.json())

    apj = resp.json()
    for datum in apj['data']:
        print(datum['id'])
        print(datum['card']['brand'])
        print(datum['card']['country'])
        print(datum['card']['exp_month'])
        print(datum['card']['exp_year'])
        print(datum['card']['last4'])

send_message()
