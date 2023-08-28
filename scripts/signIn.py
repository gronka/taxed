#!/usr/bin/env python
import requests

url = 'http://localhost:8000/api/v1/surfer/signIn.withEmail'
headers = {
    'content-type': 'application/json',
}

def send_message():
    resp = requests.post(
        url,
        json={
            "Email": "2@2.2",
            "Password": "asdf",
        },
        headers=headers)

    if resp.status_code < 200 or resp.status_code > 299:
        print(f'STATUS CODE {resp.status_code}')
    else:
        print(resp)
        print(resp.json())

send_message()
