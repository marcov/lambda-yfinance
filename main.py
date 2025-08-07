#!/usr/bin/env python3

import flask
import aws_lambda.lambda_function as lf


api = flask.Flask(__name__)


class FakeContext:
    def __init__(self, logger):
        self.logger = logger
        self.aws_request_id = "fake-context-not-lambda"


@api.route("/price", methods=["GET"])
def handle_get_price():
    lambda_response = lf.lambda_handler(
        flask.request.args, context=FakeContext(api.logger)
    )

    if lambda_response["statusCode"] != 200:
        flask.abort(lambda_response["statusCode"])

    return lambda_response


def main():
    api.run(host="127.0.0.1", port=3000)


if __name__ == "__main__":
    main()
