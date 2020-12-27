#!/usr/bin/env python

import requests

# openssl x509 -x509toreq -in certificate.crt -out CSR.csr -signkey privateKey.key


payload = 'username=wutianyao01@gmail.com&password=Wty200801='
headers = {'X-Application': 'SomeKey', 'Content-Type': 'application/x-www-form-urlencoded'}

resp = requests.post('https://identitysso-cert.betfair.com/api/certlogin', data=payload,
                     cert=('C:/Program Files/OpenSSL-Win64/bin/client-2048.crt',
                           'C:/Program Files/OpenSSL-Win64/bin/client-2048.key'), headers=headers)

if resp.status_code == 200:
    resp_json = resp.json()
    print (resp_json['loginStatus'])
    print (resp_json['sessionToken'])
else:
    print ("Request failed.")