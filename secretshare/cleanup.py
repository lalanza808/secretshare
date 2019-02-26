#!/usr/bin/env python


from boto3 import client as boto3_client
from arrow import get as arrow_get
from arrow import utcnow as arrow_utcnow
from secretshare.library import secretsmanager


def purge_expired_secrets():
    """Purge all expired secrets. This is run as
    a recurring Lambda function.
    """
    client = boto3_client('secretsmanager')
    all_secrets = secretsmanager.list_secrets(client)
    for secret_data in all_secrets:
        secret = secretsmanager.Secret()
        secret.check_tags_expired(secret_data)
        if secret.expired:
            print(f"[+] Purging expired secret {secret_data['Name']}")
            secretsmanager.delete_secret(client, secret_data['Name'])
