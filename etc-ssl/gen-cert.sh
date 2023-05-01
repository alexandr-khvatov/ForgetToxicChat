#!/bin/bash

IP=212.109.219.35
KEY_OUT="certs/$IP/webhook_pkey.pem"
CERT_OUT="certs/$IP/webhook_cert.pem"


openssl req -newkey rsa:2048 -sha256 -nodes -keyout $KEY_OUT \
-x509 -days 3650 -out $CERT_OUT \
-subj "/C=RU/ST=Saratov/L=Saratov/O=ForgetToxicChatBot/CN=$IP"
