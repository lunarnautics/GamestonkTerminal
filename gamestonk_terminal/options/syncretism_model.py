"""ops.syncretism.io model"""
__docformat__ = "numpy"

import configparser
from typing import Tuple

import pandas as pd
import requests
import yfinance as yf

from gamestonk_terminal.options import yfinance_model


def get_historical_greeks(
    ticker: str, expiry: str, chain_id: str, strike: float, put: bool
) -> pd.DataFrame:
    """Get histoical option greeks

    Parameters
    ----------
    ticker: str
        Stock ticker
    expiry: str
        Option expiration date
    chain_id: str
        OCC option symbol.  Overwrites other inputs
    strike: float
        Strike price to look for
    put: bool
        Is this a put option?

    Returns
    -------
    df: pd.DataFrame
        Dataframe containing historical greeks
    """
    if not chain_id:
        options = yfinance_model.get_option_chain(ticker, expiry)

        if put:
            options = options.puts
        else:
            options = options.calls

        chain_id = options.loc[options.strike == strike, "contractSymbol"].values[0]

    r = requests.get(f"https://api.syncretism.io/ops/historical/{chain_id}")

    if r.status_code != 200:
        print("Error in request.")
        return pd.DataFrame()

    history = r.json()

    iv, delta, gamma, theta, rho, vega, premium, price, time = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )

    for entry in history:
        time.append(pd.to_datetime(entry["timestamp"], unit="s"))
        iv.append(entry["impliedVolatility"])
        gamma.append(entry["gamma"])
        delta.append(entry["delta"])
        theta.append(entry["theta"])
        rho.append(entry["rho"])
        vega.append(entry["vega"])
        premium.append(entry["premium"])
        price.append(entry["regularMarketPrice"])

    data = {
        "iv": iv,
        "gamma": gamma,
        "delta": delta,
        "theta": theta,
        "rho": rho,
        "vega": vega,
        "premium": premium,
        "price": price,
    }

    df = pd.DataFrame(data, index=time)
    return df


def get_screener_output(preset: str, presets_path: str) -> Tuple[pd.DataFrame, str]:
    """Screen options based on preset filters

    Parameters
    ----------
    preset: str
        Preset file to screen for
    presets_path: str
        Path to preset folder
    Returns
    -------
    pd.DataFrame:
        DataFrame with screener data, or empty if errors
    str:
        String containing error message if supplied
    """
    d_cols = {
        "contractSymbol": "CS",
        "symbol": "S",
        "optType": "T",
        "strike": "Str",
        "expiration": "Exp ∨",
        "impliedVolatility": "IV",
        "lastPrice": "LP",
        "bid": "B",
        "ask": "A",
        "volume": "V",
        "openInterest": "OI",
        "yield": "Y",
        "monthlyyield": "MY",
        "regularMarketPrice": "SMP",
        "regularMarketDayLow": "SMDL",
        "regularMarketDayHigh": "SMDH",
        "lastTradeDate": "LU",
        "lastCrawl": "LC",
        "inTheMoney": "ITM",
        "pChange": "PC",
        "priceToBook": "PB",
    }

    preset_filter = configparser.RawConfigParser()
    preset_filter.optionxform = str  # type: ignore
    preset_filter.read(presets_path + preset + ".ini")

    d_filters = {k: v for k, v in dict(preset_filter["FILTER"]).items() if v}
    s_filters = str(d_filters)
    s_filters = s_filters.replace(": '", ": ").replace("',", ",").replace("'}", "}")
    s_filters = s_filters.replace("'", '"')
    errors = check_presets(d_filters)

    if errors:
        return pd.DataFrame(), errors

    link = "https://api.syncretism.io/ops"

    res = requests.get(
        link, headers={"Content-type": "application/json"}, data=s_filters
    )

    # pylint:disable=no-else-return
    if res.status_code == 200:
        df_res = pd.DataFrame(res.json())

        if df_res.empty:
            return df_res, f"No options data found for preset: {preset}"

        df_res = df_res.rename(columns=d_cols)[list(d_cols.values())[:17]]
        df_res["Exp ∨"] = df_res["Exp ∨"].apply(
            lambda x: pd.to_datetime(x, unit="s").strftime("%m-%d-%y")
        )
        df_res["LU"] = df_res["LU"].apply(
            lambda x: pd.to_datetime(x, unit="s").strftime("%m-%d-%y")
        )
        df_res["Y"] = df_res["Y"].round(3)
        df_res["MY"] = df_res["MY"].round(3)
        return df_res, ""

    else:
        return pd.DataFrame(), f"Request Error: {res.status_code}"


# pylint: disable=eval-used


def check_presets(preset_dict: dict) -> str:
    """Checks option screener preset values

    Parameters
    ----------
    preset_dict: dict
        Defined presets from configparser
    Returns
    -------
    error: str
        String of all errors accumulated
    """
    float_list = [
        "min-iv",
        "max-iv",
        "min-oi",
        "max-oi",
        "min-strike",
        "max-strike",
        "min-volume",
        "max-volume",
        "min-voi",
        "max-voi",
        "min-diff",
        "max-diff",
        "min-ask-bid",
        "max-ask-bid",
        "min-exp",
        "max-exp",
        "min-price",
        "max-price",
        "min-price-20d",
        "max-price-20d",
        "min-volume-20d",
        "max-volume-20d",
        "min-iv-20d",
        "max-iv-20d",
        "min-delta-20d",
        "max-delta-20d",
        "min-gamma-20d",
        "max-gamma-20d",
        "min-theta-20d",
        "max-theta-20d",
        "min-vega-20d",
        "max-vega-20d",
        "min-rho-20d",
        "max-rho-20d",
        "min-price-100d",
        "max-price-100d",
        "min-volume-100d",
        "max-volume-100d",
        "min-iv-100d",
        "max-iv-100d",
        "min-delta-100d",
        "max-delta-100d",
        "min-gamma-100d",
        "max-gamma-100d",
        "min-theta-100d",
        "max-theta-100d",
        "min-vega-100d",
        "max-vega-100d",
        "min-rho-100d",
        "max-rho-100d",
        "min-sto",
        "max-sto",
        "min-yield",
        "max-yield",
        "min-myield",
        "max-myield",
        "min-delta",
        "max-delta",
        "min-gamma",
        "max-gamma",
        "min-theta",
        "max-theta",
        "min-vega",
        "max-vega",
        "min-cap",
        "max-cap",
    ]
    bool_list = ["active", "stock", "etf", "puts", "calls", "itm", "otm", "exclude"]
    error = ""
    for key, value in preset_dict.items():
        if key in float_list:
            try:
                float(value)
                if value.startswith("."):
                    error += f"{key} : {value} needs to be formatted with leading 0\n"
            except Exception:
                error += f"{key} : {value}, should be float\n"

        elif key in bool_list:
            if value not in ["true", "false"]:
                error += f"{key} : {value},  Should be [true/false]\n"

        elif key == "tickers":
            for ticker in value.split(","):
                try:
                    eval(ticker)
                    if yf.Ticker(ticker).info["regularMarketPrice"] is None:
                        error += f"{key} : {ticker} not found on yfinance"

                except NameError:
                    error += f"{key} : {value}, {ticker} failed"

        elif key == "limit":
            try:
                int(value)
            except Exception:
                error += f"{key} : {value} , should be integer\n"

        elif key == "order-by":
            accepted_orders = [
                "e_desc",
                "e_asc",
                "iv_desc",
                "iv_asc",
                "md_desc",
                "md_asc",
                "lp_desc",
                "lp_asc",
            ]
            if value not in accepted_orders:
                error += f"{key} : {value} not accepted ordering\n"

    return error
