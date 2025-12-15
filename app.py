#
#  app.py
#  CryptoTracker
#
#  Created by Cascade on Dec 14, 2025.
#  Copyright © 2025 CryptoTracker. All rights reserved.
#

from datetime import datetime
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


def format_timestamp(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() + "Z" if value else None


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
    cache["cryptos"]["timestamp"] = datetime.utcnow()
    return sanitized


def fetch_crypto_history(coin_id: str) -> Dict[str, Any]:
    params = {"vs_currency": VS_CURRENCY, "days": HISTORY_DAYS}
    url = COINGECKO_HISTORY_URL.format(coin_id=coin_id)
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    payload = {"id": coin_id, "prices": response.json().get("prices", [])}
    cache["history"][coin_id] = {
        "data": payload,
        "timestamp": datetime.utcnow(),
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
