# lambda-yfinance

I was super bothered about Google Sheets having broken quite a few tickers. This
gave me a good reason to have my own AWS lambda powered stocks price API using
the Python yfinance library :-)

TLDR:

1. setup an AWS lambda with this code - both the function and the associated
   layer.
2. Create an API gateway as trigger.
3. Test with:
```console
curl "https://API-ID.execute-api.eu-central-1.amazonaws.com/default/LAMBDA-NAME?ticker=VWRA.L&csv=1"
VWRA.L,113.0
```

4. Use on gsheet with:
```
=index(importdata("https://API-ID.execute-api.eu-central-1.amazonaws.com/default/LAMBDA-NAME?ticker=VWRA.L&csv=1"), 1, 2)
```

5. Profit :-)

>
> Notes:
>
> - I have included a Make target to create the Python layer package on macOS
>  using `lima`. Make sure the ARCH used by `pip3` inside `lima` matches the
>  architecture configured on AWS!
>
