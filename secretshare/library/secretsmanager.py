#!/usr/bin/env python


from boto3 import client as boto3_client
from json import loads as json_loads
from json import dumps as json_dumps
from arrow import get as arrow_get
from arrow import utcnow as arrow_utcnow
from flask import current_app as app
from secrets import token_urlsafe


class Secret(object):
    """
    Secret objects represent a secret on
    AWS Secrets Manager. Methods involve actions
    you can perform on these items via the AWS API.
    """

    def __init__(self, secret_name=''):
        self.secret_name = secret_name

        if self.secret_name:
            self.check()


    def check(self):
        """Check if secret exists and if expired or not"""

        client = boto3_client('secretsmanager')

        try:
            response = client.describe_secret(
                SecretId=self.secret_name
            )
            self.check_tags_expired(response)
            self.exists = True
        except:
            self.exists = False
            self.expired = None

    def check_tags_expired(self, json_data):
        """Given a DescribeSecret JSON response and assess whether
        the 'Expiration' tag shows the secret is expired or not
        """

        now = arrow_utcnow()
        for tag in json_data['Tags']:
            if 'Expiration' in tag.values():
                self.expiration = tag['Value']
                expiration_date = arrow_get(tag['Value'])
                if (expiration_date - now).total_seconds() < 0:
                    # If delta is negative, we've passed expiration
                    self.expired = True
                else:
                    self.expired = False

        return


    def create(self, username, password, message, expiration=''):
        """Create a secret"""

        now = arrow_utcnow()
        client = boto3_client('secretsmanager')
        self.secret_name = token_urlsafe(32)
        self.username = str(username)
        self.password = str(password)
        self.message = str(message)
        data_object = {
            "username": self.username,
            "password": self.password,
            "message": self.message
        }

        if not expiration:
            # Set default time expiration
            self.expiration = str(now.shift(hours=app.config['DEFAULT_HOURS']))
        else:
            # Otherwise validate we have a good expiration date
            try:
                arrow_get(expiration)
            except:
                raise ValueError('invalid_datestamp')

            try:
                assert (arrow_get(expiration) - now).total_seconds() > 0
            except:
                raise ValueError('expired_datestamp')

            self.expiration = str(arrow_get(expiration))

        response = client.create_secret(
            Name=self.secret_name,
            SecretString=json_dumps(data_object),
            Tags=[
                {
                    'Key': 'Expiration',
                    'Value': self.expiration
                },
            ]
        )

        return response


    def retrieve(self):
        """Retrieve a secret's value as dictionary object"""

        client = boto3_client('secretsmanager')
        response = client.get_secret_value(
            SecretId=self.secret_name
        )
        secret_value = json_loads(response["SecretString"])
        secret_value['expiration'] = self.expiration

        return secret_value


# One-off functions used by cleanup Lambda

def list_secrets(boto_client):
    """List all secrets"""
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
