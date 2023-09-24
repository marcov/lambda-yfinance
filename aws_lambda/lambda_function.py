import yfinance as yf
import json
from pprint import pformat
import logging
import pandas
import time

logger: logging.Logger


def get_change_percent(old, new):
    if not old:
        return 0
    return round(((new - old) / old) * 100, 2)


def lambda_handler(event, context):
    global logger
    logger = getattr(context, "logger", logging.getLogger())

    logger.setLevel(logging.INFO)

    logger.info(f"Started -- lambda request ID: {context.aws_request_id}")

    try:
        request_params = event["queryStringParameters"]
        logger.info("Detected API gateway invocation")
    except KeyError:
        request_params = event
        logger.info("Detected naked invocation")

    logger.debug(f"Request params: {request_params}")

    tickers_names = request_params.get("tickers").split(",")
    format_csv = request_params.get("csv", False)
    logger.info(f"Format csv: {format_csv}")

    # API gateway expected response.
    lambda_api_gateway_response = lambda status_code, content_type=None, body=None: {
        "isBase64Encoded": False,
        "statusCode": status_code,
        "headers": {"Content-Type": content_type},
        "body": body,
    }

    if not tickers_names:
        logger.error(f"No 'tickers' URL-encoded parameter found in {request_params}")
        return lambda_api_gateway_response(400)

    response_dict = dict()

    all_data: pandas.DataFrame

    ts = time.time()
    logger.info(f"Downloading data for {len(tickers_names)} tickers ...")

    all_data = yf.download(
        tickers=tickers_names, period="7d", rounding=True, progress=False, timeout=20
    )

    logger.info(f"Data download took {round(time.time() - ts, 1)}s")

    # HACK - learn how to use pandas ...
    if len(tickers_names) == 1:
        all_close = {tickers_names[0]: all_data["Close"]}
    else:
        all_close = all_data["Close"]

    for ticker in tickers_names:
        logger.debug(f"Reading downloaded info for {ticker}")

        try:
            logger.debug(f"{ticker}: all close: {all_close[ticker]}")
            close_filt = tuple(filter(pandas.notna, all_close[ticker]))

            if len(close_filt) <= 2:
                logger.warning(
                    f"len close_filt for {ticker} is {len(close_filt)} -- {all_close[ticker]}"
                )
                if len(close_filt) < 2:
                    continue

            curr = close_filt[-1]
            prev = close_filt[-2]

        except KeyError as e:
            logger.error(f"Got exception {e} while reading price")
            return lambda_api_gateway_response(
                400, f"Failed to read price for {ticker}"
            )
        except IndexError as e:
            logger.error(f"Got exception {e} while reading price")
            return lambda_api_gateway_response(
                400, f"Failed to read price for {ticker}"
            )

        change_pct = get_change_percent(prev, curr)
        response_dict[ticker] = (curr, change_pct)
        logger.info(f"{ticker}: open: {prev}, close: {curr}, chg: {change_pct}%")

    logger.debug(f"Response dict: {pformat(response_dict)}")

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

    logger.debug(f"Sending response body: {response_body}")
    return lambda_api_gateway_response(200, content_type, response_body)
