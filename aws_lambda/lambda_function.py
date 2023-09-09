import yfinance as yf
import requests
import json
from pprint import pprint


class ApiException(Exception):
    def __init__(self, status_code, *args):
        super().__init__(args)
        self.status_code = status_code


def get_ticker_info(ticker_name):
    if not ticker_name:
        raise RuntimeError("No ticker_name given")

    ticker = yf.Ticker(ticker_name)

    try:
        tinfo = ticker.get_info()
    except requests.exceptions.HTTPError as e:
        raise ApiException(e.response.status_code, e.response)

    if not tinfo:
        raise ApiException(501, "Could not retrieve ticker info")

    # pprint(tinfo)
    return tinfo


def get_current_price(tinfo):
    for key in ("currentPrice", "ask"):
        try:
            if tinfo[key] == 0.0:
                continue

            return tinfo[key]
        except KeyError:
            pass
    else:
        raise ApiException(400, f"No price found for ticker {tinfo['symbol']}")


def get_daychange_percent(tinfo):
    cur = get_current_price(tinfo)
    prev = tinfo["previousClose"]

    pct = lambda cur, prev: ((cur - prev) / prev) * 100

    return round(pct(cur, prev), 2)


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
            tinfo = get_ticker_info(name)
            resp_tuple = (get_current_price(tinfo), get_daychange_percent(tinfo))
            response_dict[name] = resp_tuple
        except ApiException as e:
            return lambda_api_gateway_response(e.status_code)

    pprint(response_dict)

    def list_to_string(lst):
        to_string = lambda list_item: str(list_item)
        return list(map(to_string, lst))

    def to_csv():
        return "\n".join(
            map(
                lambda dict_item: ",".join(
                    [dict_item[0]] + list_to_string(dict_item[1])
                ),
                response_dict.items(),
            )
        )

    if format_csv:
        content_type = "text/csv"
        response_body = to_csv()
    else:
        content_type = "application/json"
        response_body = json.dumps(response_dict)

    print(f"Sending response body: {response_body}")
    return lambda_api_gateway_response(200, content_type, response_body)
