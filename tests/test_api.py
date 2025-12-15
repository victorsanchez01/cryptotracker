"""
//
//  test_api.py
//  CryptoTracker
//
//  Created by Cascade on Dec 14, 2025.
//  Copyright © 2025 CryptoTracker. All rights reserved.
//
"""

from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List

import pytest
import responses
from requests import Timeout
from responses import matchers

from app import (
    COINGECKO_HISTORY_URL,
    COINGECKO_MARKETS_URL,
    HISTORY_DAYS,
    VS_CURRENCY,
    cache,
)

REQUIRED_FIELDS = [
    "id",
    "symbol",
    "name",
    "current_price",
    "price_change_percentage_24h",
    "market_cap",
    "image",
]


def _build_crypto_item(idx: int) -> Dict[str, Any]:
    base_value = float(1000 + idx)
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


def _generate_market_payload(count: int = 10) -> List[Dict[str, Any]]:
    return [_build_crypto_item(idx) for idx in range(1, count + 1)]


def _register_market_response(
    mocked_responses: responses.RequestsMock,
    payload: List[Dict[str, Any]],
    status: int = 200,
    **kwargs: Any,
) -> None:
    mocked_responses.add(
        responses.GET,
        COINGECKO_MARKETS_URL,
        json=payload,
        status=status,
        **kwargs,
    )


def _generate_history_payload(coin_id: str, days: int = HISTORY_DAYS) -> Dict[str, Any]:
    now = datetime.now(UTC)
    prices = [
        [int((now - timedelta(days=offset)).timestamp() * 1000), float(45000 - offset * 50)]
        for offset in range(days)
    ]
    return {"id": coin_id, "prices": prices}


def _register_history_response(
    mocked_responses: responses.RequestsMock,
    coin_id: str,
    payload: Dict[str, Any],
    status: int = 200,
    **kwargs: Any,
) -> None:
    mocked_responses.add(
        responses.GET,
        COINGECKO_HISTORY_URL.format(coin_id=coin_id),
        match=[
            matchers.query_param_matcher(
                {"vs_currency": VS_CURRENCY, "days": str(HISTORY_DAYS)}
            )
        ],
        json=payload,
        status=status,
        **kwargs,
    )


class TestGetCryptosEndpoint:
    """Conjunto de pruebas unitarias para el endpoint /api/cryptos."""

    @pytest.mark.unit
    def test_get_cryptos_success(self, client):
        # Verifica que la respuesta sea exitosa con datos mockeados
        payload = _generate_market_payload()
        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, payload)
            response = client.get("/api/cryptos")

        data = response.get_json()
        assert response.status_code == 200
        assert data["source"] == "live"
        assert data["data"] == payload

    @pytest.mark.unit
    def test_get_cryptos_returns_json(self, client):
        # Garantiza que la respuesta sea JSON válido
        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, _generate_market_payload())
            response = client.get("/api/cryptos")

        assert response.is_json
        assert "application/json" in response.content_type
        assert response.get_json()["data"] is not None

    @pytest.mark.unit
    def test_get_cryptos_has_required_fields(self, client):
        # Confirma que cada criptomoneda incluye los campos requeridos
        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, _generate_market_payload())
            response = client.get("/api/cryptos")

        entries = response.get_json()["data"]
        for entry in entries:
            for field in REQUIRED_FIELDS:
                assert field in entry

    @pytest.mark.unit
    def test_get_cryptos_returns_10_items(self, client):
        # Comprueba que siempre se retornen 10 criptomonedas
        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, _generate_market_payload(15))
            response = client.get("/api/cryptos")

        assert len(response.get_json()["data"]) == 10

    @pytest.mark.unit
    def test_get_cryptos_api_error(self, client):
        # Maneja correctamente respuestas 500 de CoinGecko
        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, [], status=500)
            response = client.get("/api/cryptos")

        body = response.get_json()
        assert response.status_code == 502
        assert "error" in body

    @pytest.mark.unit
    def test_get_cryptos_timeout(self, client):
        # Controla escenarios de timeout de la API externa
        with responses.RequestsMock() as mocked:
            mocked.add(
                responses.GET,
                COINGECKO_MARKETS_URL,
                body=Timeout("request timed out"),
            )
            response = client.get("/api/cryptos")

        assert response.status_code == 502
        assert "error" in response.get_json()

    @pytest.mark.unit
    def test_get_cryptos_cache_fallback(self, client):
        # Recurre al caché cuando la API falla después de haber obtenido datos
        payload = _generate_market_payload()
        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, payload)
            first_response = client.get("/api/cryptos")
            assert first_response.status_code == 200

        with responses.RequestsMock() as mocked:
            _register_market_response(mocked, [], status=500)
            cached_response = client.get("/api/cryptos")

        body = cached_response.get_json()
        assert cached_response.status_code == 200
        assert body["source"] == "cache"
        assert body["data"] == payload[:10]
        assert cache["cryptos"]["data"] == payload[:10]


class TestGetCryptoHistoryEndpoint:
    """Pruebas unitarias enfocadas en /api/crypto/<id>/history."""

    coin_id = "bitcoin"

    @pytest.mark.unit
    def test_get_history_success(self, client):
        # Verifica que se obtenga el historial correctamente para Bitcoin
        payload = _generate_history_payload(self.coin_id)
        with responses.RequestsMock() as mocked:
            _register_history_response(mocked, self.coin_id, payload)
            response = client.get(f"/api/crypto/{self.coin_id}/history")

        data = response.get_json()
        assert response.status_code == 200
        assert data["data"]["id"] == self.coin_id
        assert len(data["data"]["prices"]) == HISTORY_DAYS

    @pytest.mark.unit
    def test_get_history_returns_prices_array(self, client):
        # Comprueba que la estructura de precios sea un arreglo de [timestamp, price]
        payload = _generate_history_payload(self.coin_id)
        with responses.RequestsMock() as mocked:
            _register_history_response(mocked, self.coin_id, payload)
            response = client.get(f"/api/crypto/{self.coin_id}/history")

        prices = response.get_json()["data"]["prices"]
        assert isinstance(prices, list)
        assert prices
        for point in prices:
            assert isinstance(point, list)
            assert len(point) == 2

    @pytest.mark.unit
    def test_get_history_7_days_data(self, client):
        # Asegura que el endpoint entregue datos para los 7 días configurados
        payload = _generate_history_payload(self.coin_id, days=7)
        with responses.RequestsMock() as mocked:
            _register_history_response(mocked, self.coin_id, payload)
            response = client.get(f"/api/crypto/{self.coin_id}/history")

        assert len(response.get_json()["data"]["prices"]) == 7

    @pytest.mark.unit
    def test_get_history_invalid_crypto(self, client):
        # Un identificador inexistente debería retornar un error controlado
        coin_id = "unknown-coin"
        with responses.RequestsMock() as mocked:
            _register_history_response(
                mocked,
                coin_id,
                {"error": "Not Found"},
                status=404,
            )
            response = client.get(f"/api/crypto/{coin_id}/history")

        body = response.get_json()
        assert response.status_code == 502
        assert "error" in body
        assert coin_id in body["error"]

    @pytest.mark.unit
    def test_get_history_api_error(self, client):
        # Manejo genérico de errores 500 de CoinGecko
        with responses.RequestsMock() as mocked:
            _register_history_response(
                mocked,
                self.coin_id,
                {"error": "server error"},
                status=500,
            )
            response = client.get(f"/api/crypto/{self.coin_id}/history")

        assert response.status_code == 502
        assert "error" in response.get_json()

    @pytest.mark.unit
    def test_get_history_empty_id(self, client):
        # Si no se envía un ID, Flask debería responder con 404 por ruta inválida
        response = client.get("/api/crypto//history")
        assert response.status_code == 404
