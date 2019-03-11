#!/usr/bin/env python


from boto3 import client as boto3_client
from json import loads as json_loads
from json import dumps as json_dumps
from ast import literal_eval
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

        # Perform a check if secret name provided
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
        """Given a DescribeSecret JSON response, assess whether
        the metadata tags show the secret is expired or not
        """

        now = arrow_utcnow()
        for tag in json_data['Tags']:

            # Set expiration equal to tag value - perform date delta vs now
            if 'Expiration' in tag.values():
                self.expiration = tag['Value']
                expiration_date = arrow_get(tag['Value'])
                if (expiration_date - now).total_seconds() < 0:
                    # If delta is negative, we've passed expiration
                    self.expired = True
                else:
                    self.expired = False

            # Set value if it's set to expire after first read
            if 'ExpireOnRead' in tag.values():
                self.expire_on_read = literal_eval(str(tag['Value']).title())
            else:
                self.expire_on_read = False

        # If 'LastAccessedDate' in json then the record has been read
        if 'LastAccessedDate' in json_data and self.expire_on_read:
                self.expired = True

        return


    def create(self, username, password, message, expiration='', expire_on_read=False):
        """Create a secret"""

        now = arrow_utcnow()
        client = boto3_client('secretsmanager')
        self.secret_name = token_urlsafe(32)
        self.username = str(username)
        self.password = str(password)
        self.message = str(message)
        self.expire_on_read = bool(expire_on_read)
        data_object = {
            "username": self.username,
            "password": self.password,
            "message": self.message
        }

        if not expiration:
            # Set default time expiration
            self.expiration = str(now.shift(hours=app.config.get('DEFAULT_HOURS')))
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
                {
                    'Key': 'ExpireOnRead',
                    'Value': str(self.expire_on_read)
                }
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
        secret_value['expire_on_read'] = self.expire_on_read

        return secret_value
