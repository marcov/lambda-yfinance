# lambda-yfinance

I was super bothered about Google Sheets having broken quite a few tickers. This
gave me a good reason to have my own AWS lambda powered stocks price API using
the Python yfinance library :-).

## Features

- Support for both JSON and CSV output modes.
- Can request multiple tickers in a single API invocation.

See the TLDR to grok the API syntax.

## TLDR

### Run locally

Run locally for test purposes.

Start server in one terminal:

```console
# ./main.py
```

Send request in another terminal:

```console
$ curl -s "localhost:5000/price?tickers=MSFT,AMZN,GOOG&csv=1" | jq -r .body
MSFT,328.66
AMZN,138.12
GOOG,136.8
```

### Setup on AWS

1. Setup an AWS lambda with this code - both the function and the associated
   layer.
>
> **NOTES** about the libraries layer:
>
> - I have included a make target to create the Python layer package on macOS
>  using `lima`. Make sure the ARCH used by `pip3` inside `lima` matches the
>  architecture configured on AWS!
>

2. Create an API gateway as trigger.
3. Test the API with:

```console
curl "https://API-ID.execute-api.eu-central-1.amazonaws.com/default/LAMBDA-NAME?tickers=VWRA.L&csv=1"
VWRA.L,113.0
```

### Using on gsheet

```
=index(importdata("https://API-ID.execute-api.eu-central-1.amazonaws.com/default/LAMBDA-NAME?tickers=VWRA.L&csv=1"), 1, 2)
```

