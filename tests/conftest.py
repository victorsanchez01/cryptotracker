"""
//
//  conftest.py
//  CryptoTracker
//
//  Created by Cascade on Dec 14, 2025.
//  Copyright © 2025 CryptoTracker. All rights reserved.
//
"""

from datetime import datetime
from typing import Any, Dict, List

import pytest
import responses
from responses import RequestsMock, matchers

from app import (
    COINGECKO_HISTORY_URL,
    COINGECKO_MARKETS_URL,
    HISTORY_DAYS,
    VS_CURRENCY,
    app as flask_app,
    cache,
)


@pytest.fixture(scope="session")
def app_instance():
    flask_app.config.update({"TESTING": True})
    return flask_app


@pytest.fixture()
def client(app_instance):
    return app_instance.test_client()


@pytest.fixture()
def sample_market_data() -> List[Dict[str, Any]]:
    return [
        {
            "id": "bitcoin",
            "symbol": "btc",
            "name": "Bitcoin",
            "current_price": 45000.0,
            "price_change_percentage_24h": 2.5,
            "market_cap": 880000000000,
            "image": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
            "total_volume": 38000000000,
        },
        {
            "id": "ethereum",
            "symbol": "eth",
            "name": "Ethereum",
            "current_price": 3200.0,
            "price_change_percentage_24h": -1.2,
            "market_cap": 380000000000,
            "image": "https://assets.coingecko.com/coins/images/279/large/ethereum.png",
            "total_volume": 18000000000,
        },
    ]


@pytest.fixture()
def sample_history_payload() -> Dict[str, Dict[str, Any]]:
    timestamp = int(datetime.utcnow().timestamp()) * 1000
    return {
        "bitcoin": {"id": "bitcoin", "prices": [[timestamp, 45000.0]]},
        "ethereum": {"id": "ethereum", "prices": [[timestamp, 3200.0]]},
    }


@pytest.fixture()
def mock_coingecko(
    sample_market_data: List[Dict[str, Any]],
    sample_history_payload: Dict[str, Dict[str, Any]],
):
    with RequestsMock(assert_all_requests_are_fired=False) as mocked_requests:
        mocked_requests.add(
            responses.GET,
            COINGECKO_MARKETS_URL,
            json=sample_market_data,
            status=200,
        )
        for coin_id, payload in sample_history_payload.items():
            mocked_requests.add(
                responses.GET,
                COINGECKO_HISTORY_URL.format(coin_id=coin_id),
                match=[
                    matchers.query_param_matcher(
                        {"vs_currency": VS_CURRENCY, "days": str(HISTORY_DAYS)}
                    )
                ],
                json=payload,
                status=200,
            )
        yield mocked_requests


@pytest.fixture(autouse=True)
def reset_cache_state():
    cache["cryptos"] = {"data": None, "timestamp": None}
    cache["history"] = {}
    yield
    cache["cryptos"] = {"data": None, "timestamp": None}
    cache["history"] = {}
