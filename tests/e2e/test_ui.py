"""
//
//  test_ui.py
//  CryptoTracker
//
//  Created by Cascade on Dec 14, 2025.
//  Copyright © 2025 CryptoTracker. All rights reserved.
//
"""

import asyncio
import os
from pathlib import Path
from typing import Awaitable, Callable, Dict

import pytest
from playwright.async_api import Page, async_playwright, expect
from playwright._impl._errors import TargetClosedError

DESKTOP_VIEWPORT: Dict[str, int] = {"width": 1400, "height": 900}
MOBILE_VIEWPORT: Dict[str, int] = {"width": 390, "height": 844}
DATA_TIMEOUT_MS = 20000
SCREENSHOT_DIR = Path(__file__).parent / "artifacts"


def _get_base_url() -> str:
    return os.environ.get("E2E_BASE_URL", "http://127.0.0.1:5000")


async def run_ui_flow(
    test_name: str,
    steps: Callable[[Page], Awaitable[None]],
    *,
    viewport: Dict[str, int] = DESKTOP_VIEWPORT,
) -> None:
    async with async_playwright() as playwright:
        base_url = _get_base_url()
        if not base_url:
            raise RuntimeError("E2E_BASE_URL no está configurado.")
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(viewport=viewport)
        page = await context.new_page()
        try:
            await page.goto(base_url, wait_until="networkidle")
            await steps(page)
        except Exception:
            SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
            await page.screenshot(
                path=str(SCREENSHOT_DIR / f"{test_name}.png"),
                full_page=True,
            )
            raise
        finally:
            try:
                await context.close()
            except TargetClosedError:
                pass
            await browser.close()


def run_async_test(
    test_name: str,
    steps: Callable[[Page], Awaitable[None]],
    *,
    viewport: Dict[str, int] = DESKTOP_VIEWPORT,
) -> None:
    asyncio.run(run_ui_flow(test_name, steps, viewport=viewport))


@pytest.mark.e2e
def test_homepage_loads(live_server):
    async def scenario(page: Page) -> None:
        await expect(page.get_by_role("heading", name="CryptoTracker")).to_be_visible()

    run_async_test("test_homepage_loads", scenario)


@pytest.mark.e2e
def test_crypto_table_visible(live_server):
    async def scenario(page: Page) -> None:
        await expect(page.locator("#cryptoGrid")).to_be_visible()

    run_async_test("test_crypto_table_visible", scenario)


@pytest.mark.e2e
def test_crypto_table_has_data(live_server):
    async def scenario(page: Page) -> None:
        rows = page.locator("#cryptoGrid .table-row")
        await expect(rows.nth(0)).to_be_visible(timeout=DATA_TIMEOUT_MS)

    run_async_test("test_crypto_table_has_data", scenario)


@pytest.mark.e2e
def test_search_filters_results(live_server):
    async def scenario(page: Page) -> None:
        first_row = page.locator("#cryptoGrid .table-row").nth(0)
        await expect(first_row).to_be_visible(timeout=DATA_TIMEOUT_MS)
        await page.fill("#searchInput", "bitcoin")
        await expect(
            page.locator("#cryptoGrid .table-row"),
        ).to_have_count(1, timeout=DATA_TIMEOUT_MS)
        await expect(
            page.locator("#cryptoGrid .table-row").first
        ).to_contain_text("Bitcoin")

    run_async_test("test_search_filters_results", scenario)


@pytest.mark.e2e
def test_crypto_table_has_10_rows(live_server):
    async def scenario(page: Page) -> None:
        rows = page.locator("#cryptoGrid .table-row")
        await expect(rows.nth(9)).to_be_visible(timeout=DATA_TIMEOUT_MS)
        assert await rows.count() == 10

    run_async_test("test_crypto_table_has_10_rows", scenario)


@pytest.mark.e2e
def test_click_crypto_shows_chart(live_server):
    async def scenario(page: Page) -> None:
        first_row = page.locator("#cryptoGrid .table-row").nth(0)
        await expect(first_row).to_be_visible(timeout=DATA_TIMEOUT_MS)
        await first_row.click()
        await expect(page.locator("#modalOverlay")).to_be_visible(timeout=DATA_TIMEOUT_MS)
        await expect(page.locator("#chartPanel")).to_be_visible(timeout=DATA_TIMEOUT_MS)

    run_async_test("test_click_crypto_shows_chart", scenario)


@pytest.mark.e2e
def test_chart_renders(live_server):
    async def scenario(page: Page) -> None:
        row = page.locator("#cryptoGrid .table-row").nth(0)
        await expect(row).to_be_visible(timeout=DATA_TIMEOUT_MS)
        await row.click()
        await expect(page.locator("#historyChart")).to_be_visible(timeout=DATA_TIMEOUT_MS)
        await page.wait_for_timeout(1500)
        has_pixels = await page.locator("#historyChart").evaluate(
            "canvas => canvas && canvas.width > 0 && canvas.height > 0"
        )
        assert has_pixels

    run_async_test("test_chart_renders", scenario)


@pytest.mark.e2e
def test_page_title_correct(live_server):
    async def scenario(page: Page) -> None:
        await expect(page).to_have_title("CryptoTracker")

    run_async_test("test_page_title_correct", scenario)


@pytest.mark.e2e
def test_responsive_mobile(live_server):
    async def scenario(page: Page) -> None:
        await expect(page.locator(".app-header")).to_be_visible()
        no_horizontal_scroll = await page.evaluate(
            "() => document.body.scrollWidth <= window.innerWidth + 1"
        )
        assert no_horizontal_scroll

    run_async_test(
        "test_responsive_mobile",
        scenario,
        viewport=MOBILE_VIEWPORT,
    )
