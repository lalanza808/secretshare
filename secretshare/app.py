#!/usr/bin/env python


from flask import Flask, jsonify, request, make_response
from flask_restplus import Api, Resource, reqparse, fields
from flask_cors import CORS as cors
from secretshare import __version__
from secretshare.library import secretsmanager


# Define Flask application
app = Flask(__name__)
app.config.from_envvar('FLASK_SECRETS')
cors(app, origins=app.config.get('ALLOWED_DOMAINS', '*'))
api = Api(app, version=__version__, title=app.config.get('APP_NAME', 'secretshare'),
    description='Simple secret sharing API using AWS Secrets Manager'
)

# Define models
secret_data = api.model('secret_data', {
    'username': fields.String,
    'password': fields.String,
    'message': fields.String,
    'expiration': fields.DateTime,
    'expire_on_read': fields.Boolean
})
response_data = api.inherit('response_data', secret_data, {
    'token': fields.String,
    'error_msg': fields.String,
    'error_id': fields.String
})

# Parse query strings/arguments
parser = reqparse.RequestParser()
parser.add_argument('token', type=str, help='Token provided when creating the secret')


@api.route('/secret/')
class Secrets(Resource):
    """Represents available actions
    for managing secrets on AWS Secrets
    Manager. Can retrieve and create secrets.
    """

    @api.doc('retrieve', parser=parser)
    @api.marshal_with(response_data, code=200, skip_none=True)
    def get(self):
        args = parser.parse_args()

        if args.get('token'):
            secret_name = args.get('token')
            secret = secretsmanager.Secret(secret_name=secret_name)

            if secret.exists and not secret.expired:
                # If secret exists and not expired, return secret
                return secret.retrieve(), 200
            else:
                # If secret is expired or doesn't exist, return error
                return {
                    'error_msg': 'This secret is expired or does not exist.',
                    'error_id': 'expired_secret'
                }, 400
        else:
            # If no query string provided, return error
            return {
                'error_msg': 'No secret token provided.',
                'error_id': 'no_token'
            }, 400

    @api.doc('create')
    @api.expect(secret_data, validate=True)
    @api.marshal_with(response_data, code=201, skip_none=True)
    def post(self):
        if api.payload:
            try:
                secret = secretsmanager.Secret()
                secret.create(
                    username=api.payload.get('username', ''),
                    password=api.payload.get('password', ''),
                    message=api.payload.get('message', ''),
                    expiration=api.payload.get('expiration', ''),
                    expire_on_read=api.payload.get('expire_on_read', False)
                )
                return {
                    'token': secret.secret_name
                }, 201
            except ValueError as err:
                return {
                    'error_msg': 'Invalid expiration date',
                    'error_id': err
                }, 400
        else:
            return {
                'error_msg': 'No secret JSON payload provided',
                'error_id': 'no_payload'
            }, 400


@app.errorhandler(404)
def not_found(error):
    response = make_response(jsonify({
        'error_msg': 'Route not found',
        'error_id': 'not_found'}
    ), 404)
    return response


if __name__ == '__main__':
    app.run()
