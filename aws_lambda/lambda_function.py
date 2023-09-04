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

    price = None

    for key in ("currentPrice", "ask"):
        try:
            price = ticker.info[key]
        except KeyError:
            pass

    if price is None:
        raise PriceException(404, f"No price found for ticker {ticker_name}")

    return price


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

    ticker_name = request_params.get("ticker")
    format_csv = request_params.get("csv", False)
    print(f"Format csv: {format_csv}")

    if not ticker_name:
        print(f"No 'ticker' name found in {request_params}")
        return lambda_api_gateway_response(400)

    try:
        print(f"Checking price for {ticker_name}")
        price = get_ticker_price(ticker_name)

        if format_csv:
            response_body = f"{ticker_name},{price}"
            content_type= "text/csv"
        else:
            response_body = json.dumps({"ticker": ticker_name, "price": price})
            content_type= "application/json"

    except PriceException as e:
        return lambda_api_gateway_response(e.status_code)

    print(f"Sending response body: {response_body}")
    return lambda_api_gateway_response(200, content_type, response_body)
