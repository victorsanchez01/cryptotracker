#
#  app.py
#  CryptoTracker
#
#  Created by Cascade on Dec 14, 2025.
#  Copyright © 2025 CryptoTracker. All rights reserved.
#

import os
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from requests import RequestException

COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINGECKO_HISTORY_URL = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
TOP_LIMIT = 10
HISTORY_DAYS = 7
VS_CURRENCY = "usd"

app = Flask(__name__)
CORS(app)

CacheEntry = Dict[str, Any]

cache: Dict[str, Any] = {
    "cryptos": {"data": None, "timestamp": None},
    "history": {},
}


def _env_flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes"}


app.config.setdefault("USE_MOCK_DATA", _env_flag("MOCK_COINGECKO"))

MOCK_MARKET_DATA: List[Dict[str, Any]] = [
    {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "current_price": 45000,
        "price_change_percentage_24h": 3.2,
        "market_cap": 880_000_000_000,
        "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
        "total_volume": 38_000_000_000,
    },
    *[
        {
            "id": f"mock-coin-{index}",
            "symbol": f"mc{index}",
            "name": f"Mock Coin {index}",
            "current_price": 1000 + index * 10,
            "price_change_percentage_24h": (-1) ** index * 2.5,
            "market_cap": 10_000_000_000 + index * 1_000_000_000,
            "image": "https://via.placeholder.com/64",
            "total_volume": 500_000_000 + index * 100_000_000,
        }
        for index in range(1, 11)
    ],
][:TOP_LIMIT]


def set_mock_data(enabled: bool = True) -> None:
    app.config["USE_MOCK_DATA"] = enabled


def use_mock_data() -> bool:
    env_override = os.getenv("MOCK_COINGECKO")
    if env_override is not None:
        return _env_flag("MOCK_COINGECKO")
    return bool(app.config.get("USE_MOCK_DATA"))


def format_timestamp(value: Optional[datetime]) -> Optional[str]:
    if not value:
        return None
    aware_value = value.astimezone(UTC)
    return aware_value.isoformat().replace("+00:00", "Z")


def sanitize_market_data(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fields = [
        "id",
        "symbol",
        "name",
        "current_price",
        "price_change_percentage_24h",
        "market_cap",
        "image",
        "total_volume",
    ]
    return [
        {field: entry.get(field) for field in fields}
        for entry in entries[:TOP_LIMIT]
    ]


def fetch_top_cryptos() -> List[Dict[str, Any]]:
    if use_mock_data():
        sanitized = sanitize_market_data(MOCK_MARKET_DATA)
        cache["cryptos"]["data"] = sanitized
        cache["cryptos"]["timestamp"] = datetime.now(UTC)
        return sanitized

    params = {
        "vs_currency": VS_CURRENCY,
        "order": "market_cap_desc",
        "per_page": TOP_LIMIT,
        "page": 1,
        "sparkline": "false",
    }
    response = requests.get(COINGECKO_MARKETS_URL, params=params, timeout=10)
    response.raise_for_status()
    sanitized = sanitize_market_data(response.json())
    cache["cryptos"]["data"] = sanitized
    cache["cryptos"]["timestamp"] = datetime.now(UTC)
    return sanitized


def fetch_crypto_history(coin_id: str) -> Dict[str, Any]:
    if use_mock_data():
        now = datetime.now(UTC)
        prices = [
            [int((now - timedelta(days=offset)).timestamp() * 1000), 1000 + offset * 5]
            for offset in range(HISTORY_DAYS)
        ]
        payload = {"id": coin_id, "prices": prices}
        cache["history"][coin_id] = {
            "data": payload,
            "timestamp": datetime.now(UTC),
        }
        return payload

    params = {"vs_currency": VS_CURRENCY, "days": HISTORY_DAYS}
    url = COINGECKO_HISTORY_URL.format(coin_id=coin_id)
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    payload = {"id": coin_id, "prices": response.json().get("prices", [])}
    cache["history"][coin_id] = {
        "data": payload,
        "timestamp": datetime.now(UTC),
    }
    return payload


def build_cached_response(entry: CacheEntry, source: str) -> Dict[str, Any]:
    return {
        "data": entry.get("data"),
        "source": source,
        "cached_at": format_timestamp(entry.get("timestamp")),
    }


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/api/cryptos", methods=["GET"])
def get_top_cryptos():
    try:
        data = fetch_top_cryptos()
        return jsonify({"data": data, "source": "live", "cached_at": None})
    except RequestException:
        cached = cache["cryptos"]
        if cached.get("data"):
            return jsonify(build_cached_response(cached, "cache")), 200
        return jsonify({"error": "Unable to fetch cryptocurrency data."}), 502


@app.route("/api/crypto/<string:coin_id>/history", methods=["GET"])
def get_crypto_history(coin_id: str):
    try:
        payload = fetch_crypto_history(coin_id)
        return jsonify({"data": payload, "source": "live", "cached_at": None})
    except RequestException:
        history_entry = cache["history"].get(coin_id)
        if history_entry:
            return jsonify(build_cached_response(history_entry, "cache")), 200
        return jsonify({"error": f"Unable to fetch price history for {coin_id}."}), 502


if __name__ == "__main__":
    app.run(debug=True)
