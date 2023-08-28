#!/usr/bin/env python
import requests


def get_predictions():
    url = 'http://localhost/api/v1/place/autocomplete.get'
    headers = {
        'content-type': 'application/json',
    }
    resp = requests.post(
        url,
        json={
            "Input": "3207",
            "Lat": "70",
            "Long": "70",
        },
        headers=headers)

    if resp.status_code < 200 or resp.status_code > 299:
        print(f'STATUS CODE {resp.status_code}')
    else:
        print(resp.text)


def get_place():
    url = 'http://localhost/api/v1/place/placeIdToPlace'
    headers = {
        'content-type': 'application/json',
    }
    resp = requests.post(
        url,
        json={
            "PlaceId": "EikzMjA3IE1vYmlsZSBId3ksIFBlbnNhY29sYSwgRkwgMzI1MDUsIFVTQSIxEi8KFAoSCddll_Akv5CIEazwd2fe0M6EEIcZKhQKEglTFr3SEr2QiBHiobZrbXrlVQ",
        },
        headers=headers)

    if resp.status_code < 200 or resp.status_code > 299:
        print(resp.text)
        print(f'STATUS CODE {resp.status_code}')
    else:
        print(resp.text)
        print(resp.json())


get_predictions()
get_place()
