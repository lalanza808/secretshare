# secretshare

## Overview

This project uses the [Flask](http://flask.pocoo.org/) web framework in conjunction with [Flask-RESTPlus](https://flask-restplus.readthedocs.io/en/stable/) and [Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) to offer a very simple REST API for creating secrets on [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/).

It's intended to be used as a way to share secrets over various means of communication (email, chat, text, etc). The use case is similar to several other open source projects:

* https://github.com/MichaelThessel/pwx
* https://github.com/onetimesecret/onetimesecret
* https://github.com/samtorno/angerona2

However, this application fully supports serverless AWS architecture - [API Gateway](https://aws.amazon.com/api-gateway/) and [Lambda](https://aws.amazon.com/lambda/) - using [Zappa](https://github.com/Miserlou/Zappa).

## Setup

#### AWS

In order for this application to work, you will need an active AWS account, AWSCLI installed to your local machine, and an administrative IAM key pair configured in any AWSCLI profile.

#### Python

This is a Python project and requires version >=3.6.0. There are many ways to setup a development environment in Python, the most common one probably looks like this:

```
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install .
```

#### Zappa

I've provided an example config, which is _almost_ good to go, but you'll need to specify an S3 bucket for Zappa to upload files to (it generates this for you). Keep in mind, S3 bucket names are global - there cannot be more than one bucket of the same name for the world. Make it **really** random. Also, check the other settings to ensure they are what you want, primarily `aws_region` and `profile_name`.

Copy the example Zappa config to `zappa_settings.json` and edit the above values.


```
$ cp zappa_settings.{example.json,json}
$ vim zappa_settings.json
```

#### secretshare

Last thing, the application has a simple configuration file which sets some defaults like the app name and default expiration time.

Copy the example config file to `config.py` and make any modifications if you'd like to change them.

```
$ cp secretshare/config.{example.py,py}
$ vim secretshare/config.py
```

## Running Locally

If you'd like to develop and play around first, you can run a local web server to interact with the application without deploying it to AWS. To do so, drop into your virtual environment and run the Flask web server:

```
$ source .venv/bin/activate
$ export FLASK_APP=secretshare/app.py
$ export FLASK_SECRETS=config.py
$ export FLASK_DEBUG=1
$ flask run
```

With debug mode enabled you will be able to modify files and have Flask automatically reload the changes. Assuming everything is setup properly, you should be able to interact with the API. I like `curl`:

```
# POST a new secret
$ curl http://127.0.0.1:5000/secret/ \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"lance\",  \"password\": \"TopS3cr3t1\"}"

{
  "token": "tpXv-Pk3W1lZJzY5v-6oEU8029IublWHjSs3BzbETW4"
}


# GET an existing secret
$ curl http://127.0.0.1:5000/secret/?token=tpXv-Pk3W1lZJzY5v-6oEU8029IublWHjSs3BzbETW4

{
  "username": "lance",
  "password": "TopS3cr3t1",
  "expiration": "2019-02-26T09:46:49.790153+00:00"
}

```

By nature of using Flask-RESTPlus there is some Swagger documentation that is automatically generated. You can view it in your browser: http://127.0.0.1:5000/

## Deploying to AWS

As long as you're setup properly you can deploy to AWS using Zappa.

```
$ zappa deploy
```

When the deployment is finished you will be provided a new AWS API Gateway endpoint; something like `https://2rdpleh3tf.execute-api.us-west-2.amazonaws.com/dev`. You can validate the endpoint by running the same `curl` commands as above but replacing the endpoint with your API Gateway.

Part of the Zappa configuration includes a recurring event; every 12 hours a Lambda function is scanning all secrets and purging expired secrets. If no `expiration` was set during secret creation then the application defaults to **1 hour** expiration; this can be changed in `secretshare/config.py`. The tag set on the secret is the basis for this expiration check.

If you'd like to cleanup the secrets manually, you can invoke the Lambda function manually with Zappa:

```
$ zappa invoke secretshare.cleanup.purge_expired_secrets
```

## What Now?

Most people don't necessarily care about the backend API - this is only one half of the battle as we need something to present the information. This API can be used in conjunction with any static website with simple Javascript for posting, retrieving, and rendering the data. I'll be creating an example static website to showcase this; it's on my to-do list.
