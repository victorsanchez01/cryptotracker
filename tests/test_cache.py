"""
//
//  test_cache.py
//  CryptoTracker
//
//  Created by Cascade on Dec 14, 2025.
//  Copyright © 2025 CryptoTracker. All rights reserved.
//
"""

from typing import Any, Dict, List

import pytest
import responses

from app import COINGECKO_MARKETS_URL, cache


def _build_crypto_item(idx: int, price_seed: float = 0) -> Dict[str, Any]:
    base_value = float(1000 + idx + price_seed)
    return {
        "id": f"coin-{idx}",
        "symbol": f"c{idx}",
        "name": f"Coin {idx}",
        "current_price": base_value,
        "price_change_percentage_24h": float(idx),
        "market_cap": int(base_value * 1_000_000),
        "image": f"https://cdn.example.com/coin-{idx}.png",
        "total_volume": int(base_value * 10_000),
    }


def _generate_market_payload(count: int = 10, price_seed: float = 0) -> List[Dict[str, Any]]:
    return [_build_crypto_item(idx, price_seed) for idx in range(1, count + 1)]


def _register_market_response(
    mocked_responses: responses.RequestsMock,
    payload: List[Dict[str, Any]],
    status: int = 200,
) -> None:
    mocked_responses.add(
        responses.GET,
        COINGECKO_MARKETS_URL,
        json=payload,
        status=status,
    )


class TestCacheBehavior:
    """Validaciones específicas del sistema de caché."""

    @pytest.mark.unit
    def test_cache_stores_successful_response(self, client):
        # Un hit exitoso debe persistir datos y timestamp en caché
        payload = _generate_market_payload()
        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, payload)
            response = client.get("/api/cryptos")

        assert response.status_code == 200
        assert cache["cryptos"]["data"] == payload[:10]
        assert cache["cryptos"]["timestamp"] is not None

    @pytest.mark.unit
    def test_cache_returns_stale_data_on_api_failure(self, client):
        # Cuando la API falla, se debe responder con los datos almacenados
        payload = _generate_market_payload()
        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, payload)
            client.get("/api/cryptos")

        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, [], status=500)
            response = client.get("/api/cryptos")

        body = response.get_json()
        assert response.status_code == 200
        assert body["source"] == "cache"
        assert body["data"] == payload[:10]

    @pytest.mark.unit
    def test_cache_empty_on_first_failure(self, client):
        # Si no hay datos cacheados, un fallo externo debe propagar error
        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, [], status=500)
            response = client.get("/api/cryptos")

        assert response.status_code == 502
        assert "error" in response.get_json()

    @pytest.mark.unit
    def test_cache_updates_on_new_data(self, client):
        # Un nuevo fetch exitoso debe sobrescribir la información previa
        first_payload = _generate_market_payload(price_seed=0)
        updated_payload = _generate_market_payload(price_seed=100)

        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, first_payload)
            client.get("/api/cryptos")

        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, updated_payload)
            response = client.get("/api/cryptos")

        assert response.status_code == 200
        assert cache["cryptos"]["data"] == updated_payload[:10]
        assert cache["cryptos"]["data"] != first_payload[:10]
