"""
//
//  conftest.py
//  CryptoTracker
//
//  Created by Cascade on Dec 14, 2025.
//  Copyright © 2025 CryptoTracker. All rights reserved.
//
"""

import os
import socket
import time
from multiprocessing import Process
from typing import Generator

import pytest

from app import app, set_mock_data

HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
PORT = int(os.environ.get("FLASK_PORT", "5000"))


def _run_server() -> None:
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


def _wait_for_server(host: str, port: int, timeout: int = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.5)
    raise RuntimeError(f"No se pudo iniciar el servidor Flask en {host}:{port}")


@pytest.fixture(scope="session")
def live_server(pytestconfig) -> Generator[str, None, None]:
    base_url = f"http://{HOST}:{PORT}"
    set_mock_data(True)
    os.environ["MOCK_COINGECKO"] = "1"
    os.environ["E2E_BASE_URL"] = base_url

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex((HOST, PORT)) == 0:
            yield base_url
            return

    process = Process(target=_run_server)
    process.start()
    try:
        _wait_for_server(HOST, PORT)
        yield base_url
    finally:
        process.terminate()
        process.join()
