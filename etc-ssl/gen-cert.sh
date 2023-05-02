#!/bin/bash

IP=212.109.219.35
KEY_OUT="webhook_pkey.key"
CERT_OUT="webhook_cert.pem"

openssl req -newkey rsa:2048 -sha256 -nodes -keyout $KEY_OUT \
-x509 -days 365 -out $CERT_OUT \
-subj "/C=US/ST=New York/L=Brooklyn/O=Example Brooklyn Company/CN=$IP"
