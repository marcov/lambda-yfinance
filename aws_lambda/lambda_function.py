#!/usr/bin/env python3

import yfinance as yf
import requests
import json


class PriceException(Exception):
    def __init__(self, status_code, *args):
        super().__init__(args)
        self.status_code = status_code


def get_ticker_price(ticker_name):
    if not ticker_name:
        raise RuntimeError("No ticker_name given")

    ticker = yf.Ticker(ticker_name)

    try:
        ticker.get_info()
    except requests.exceptions.HTTPError as e:
        print(f"Got {e}")
        raise PriceException(e.response.status_code, e.response)

    for key in ("currentPrice", "ask"):
        try:
            if ticker.info[key] == 0.0:
                continue

            return ticker.info[key]
        except KeyError:
            pass
    else:
        raise PriceException(404, f"No price found for ticker {ticker_name}")


def lambda_handler(event, context):
    if context:
        print("Lambda Request ID:", context.aws_request_id)

    # API gateway expected response.
    lambda_api_gateway_response = lambda status_code, content_type=None, body=None: {
        "isBase64Encoded": False,
        "statusCode": status_code,
        "headers": {"Content-Type": content_type},
        "body": body,
    }

    # This is when it's invoked directly with no API gateway.
    request_params = event.get("queryStringParameters")

    if request_params:
        print("Detected API gateway invocation")
    else:
        print("Detected naked invocation")
        # Assume API gateway
        request_params = event

    print(f"Request params: {request_params}")

    tickers_names = request_params.get("tickers")
    format_csv = request_params.get("csv", False)
    print(f"Format csv: {format_csv}")

    if not tickers_names:
        print(f"No 'tickers' URL-encoded parameter found in {request_params}")
        return lambda_api_gateway_response(400)

    response_dict = dict()

    for name in tickers_names.split(","):
        try:
            print(f"Checking price for {name}")
            response_dict[name] = get_ticker_price(name)
            print(f"Price is {response_dict[name]}")

        except PriceException as e:
            return lambda_api_gateway_response(e.status_code)

    if format_csv:
        content_type = "text/csv"

        response_body = "\n".join(
            tuple(map(lambda item: f"{item[0]},{item[1]}", response_dict.items()))
        )
    else:
        content_type = "application/json"

        response_body = json.dumps(response_dict)

    print(f"Sending response body: {response_body}")
    return lambda_api_gateway_response(200, content_type, response_body)
