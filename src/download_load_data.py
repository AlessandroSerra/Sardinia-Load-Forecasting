import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

load_dotenv()

CLIENT_ID = os.getenv("TERNA_API_KEY")
CLIENT_SECRET = os.getenv("TERNA_API_SECRET")

TOKEN_URL = "https://api.terna.it/public-api/access-token"
TOTAL_LOAD_URL = "https://api.terna.it/load/v2.0/total-load"

CHUNK_DAYS = 60
SLEEP_SECONDS = 5


# ---------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------


def get_access_token():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError("Missing TERNA_API_KEY or TERNA_API_SECRET in .env")

    response = requests.post(
        TOKEN_URL,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Authentication failed ({response.status_code}):\n{response.text}"
        )

    data = response.json()

    if "access_token" not in data:
        raise RuntimeError(f"No access_token found in response:\n{data}")

    return data["access_token"]


# ---------------------------------------------------------------------
# Single API request
# ---------------------------------------------------------------------


def fetch_total_load_chunk(
    token,
    date_from,
    date_to,
    bidding_zone="Sardinia",
):
    response = requests.get(
        TOTAL_LOAD_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        params={
            "dateFrom": date_from,
            "dateTo": date_to,
            "biddingZone": bidding_zone,
        },
        timeout=60,
    )

    if not response.ok:
        raise RuntimeError(
            f"Terna API request failed ({response.status_code})\n"
            f"URL: {response.url}\n"
            f"Response: {response.text}"
        )

    data = response.json()

    if "total_load" not in data:
        raise RuntimeError(f"Unexpected API response:\n{data}")

    return pd.DataFrame(data["total_load"])


# ---------------------------------------------------------------------
# Download arbitrary date range
# ---------------------------------------------------------------------


def fetch_total_load_range(
    date_from,
    date_to,
    bidding_zone="Sardinia",
    chunk_days=CHUNK_DAYS,
    sleep_seconds=SLEEP_SECONDS,
):
    start = pd.to_datetime(date_from, dayfirst=True)
    end = pd.to_datetime(date_to, dayfirst=True)

    if start > end:
        raise ValueError("date_from must be before date_to")

    chunks = []

    current_start = start

    while current_start <= end:
        # 60 calendar days inclusive
        current_end = min(
            current_start + pd.Timedelta(days=chunk_days - 1),
            end,
        )

        date_from_str = current_start.strftime("%d/%m/%Y")
        date_to_str = current_end.strftime("%d/%m/%Y")

        print(
            f"Fetching {date_from_str} -> {date_to_str}...",
            flush=True,
        )

        # Get a fresh token for every chunk.
        # Terna access tokens are short-lived.
        token = get_access_token()

        chunk = fetch_total_load_chunk(
            token=token,
            date_from=date_from_str,
            date_to=date_to_str,
            bidding_zone=bidding_zone,
        )

        print(f"  received {len(chunk):,} rows")

        chunks.append(chunk)

        current_start = current_end + pd.Timedelta(days=1)

        if current_start <= end:
            time.sleep(sleep_seconds)

    if not chunks:
        return pd.DataFrame()

    return pd.concat(
        chunks,
        ignore_index=True,
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

if __name__ == "__main__":
    DATE_FROM = "01/01/2023"
    DATE_TO = "05/10/2026"
    BIDDING_ZONE = "Sardinia"

    OUTPUT_PATH = Path("data/raw/terna_total_load_2023_2026.csv")

    print(
        f"Downloading Terna total load data\n"
        f"Zone: {BIDDING_ZONE}\n"
        f"Period: {DATE_FROM} -> {DATE_TO}\n"
    )

    df = fetch_total_load_range(
        date_from=DATE_FROM,
        date_to=DATE_TO,
        bidding_zone=BIDDING_ZONE,
    )

    print("\nDownload completed.")
    print(f"Total rows: {len(df):,}")

    if not df.empty:
        print("\nColumns:")
        print(df.columns.tolist())

        print("\nFirst rows:")
        print(df.head())

        print("\nLast rows:")
        print(df.tail())

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"\nSaved to: {OUTPUT_PATH}")
