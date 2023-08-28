#!/usr/bin/env python
import requests
from taxed.conf import Conf


conf = Conf(skip_env=True)


def send_message():
    google_places_key = conf.google_places_key

    url = ('https://maps.googleapis.com/maps/api/place/autocomplete/json'
           '?input=3207 Free'
           '&inputtype=textquery'
           '&fields=formatted_address'
           '%2Cplace_id'
           '%2Cname'
           '%2Cgeometry'
           '%2Caddress_components'
           f'&key={google_places_key}')
    payload={}
    headers = {}
    resp = requests.request("GET", url, headers=headers, data=payload)
    # print(resp.text)
    # jason = resp.json()

    if resp.status_code < 200 or resp.status_code > 299:
        print(f'STATUS CODE {resp.status_code}')
    else:
        # print(jason['predictions'][0])
        print(resp.json())

    # jason = resp.json()

    print('=======================================')

    place_id = 'EiczMjA3IE1vYmlsZSBIaWdod2F5LCBQZW5zYWNvbGEsIEZMLCBVU0EiMRIvChQKEgnXZZfwJL-QiBGs8Hdn3tDOhBCHGSoUChIJUxa90hK9kIgR4qG2a2165VU'

    url = ('https://maps.googleapis.com/maps/api/place/details/json'
           f'?place_id={place_id}'
           '&fields=place_id'
           '%2Caddress_components'
           f'&key={google_places_key}')

    resp = requests.request("GET", url, headers=headers, data=payload)
    print('')
    print(resp.text)

    if resp.status_code < 200 or resp.status_code > 299:
        print(f'STATUS CODE {resp.status_code}')
    else:
        print(resp.json())

send_message()
