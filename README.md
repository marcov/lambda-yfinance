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
$ ./main.py
```

Send request in another terminal:

```console
$ curl -s "localhost:5000/price?tickers=MSFT,AMZN,GOOG&csv=1" | jq -r .body
MSFT,338.115,1.15
AMZN,142.585,3.15
GOOG,137.72,0.38
~ »

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
VWRA.L,110.38,0.3
```

### Using on gsheet

Get the price:

```
=index(importdata("https://API-ID.execute-api.eu-central-1.amazonaws.com/default/LAMBDA-NAME?tickers=VWRA.L&csv=1"), 1, 2)
```

Get the daily change percentage:

```
=index(importdata("https://API-ID.execute-api.eu-central-1.amazonaws.com/default/LAMBDA-NAME?tickers=VWRA.L&csv=1"), 1, 3)
```

