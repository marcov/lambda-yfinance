#!/usr/bin/env python3

import flask
import aws_lambda.lambda_function as lf


api = flask.Flask(__name__)


@api.route("/price", methods=["GET"])
def handle_get_price():
    lambda_response = lf.lambda_handler(flask.request.args, None)

    if lambda_response["statusCode"] != 200:
        flask.abort(lambda_response["statusCode"])

    return lambda_response


def main():
    api.run()


if __name__ == "__main__":
    main()
