#!/usr/bin/env python


from boto3 import client as boto3_client
from arrow import get as arrow_get
from arrow import utcnow as arrow_utcnow
from secretshare.library import secretsmanager


def list_secrets(boto_client):
    """Return a list of all secrets"""
    next_token = ""
    pagination_finished = False
    secrets = []
    response = boto_client.list_secrets(
        MaxResults=20
    )
    while not pagination_finished:
        for secret in response['SecretList']:
            secrets.append(secret)
        if 'NextToken' in response:
            next_token = response['NextToken']
            response = boto_client.list_secrets(
                MaxResults=20,
                NextToken=next_token
            )
        else:
            pagination_finished = True

    return secrets

def delete_secret(boto_client, secret_name):
    """Remove a secret"""
    response = boto_client.delete_secret(
        SecretId=secret_name,
        ForceDeleteWithoutRecovery=True
    )
    return response

def purge_expired_secrets():
    """Purge all expired secrets."""
    client = boto3_client('secretsmanager')
    all_secrets = list_secrets(client)
    for secret_data in all_secrets:
        secret = secretsmanager.Secret()
        secret.check_tags_expired(secret_data)
        if secret.expired:
            print(f"[+] Purging expired secret {secret_data['Name']}")
            delete_secret(client, secret_data['Name'])
