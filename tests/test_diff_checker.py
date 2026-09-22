"""Headless browser tests for Diff Checker (Playwright + pytest)."""
import os
import time
import urllib.request

import pytest
from playwright.sync_api import expect, sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000").rstrip("/")
EXPECTED_ENV = os.environ.get("EXPECTED_APP_ENV", "development")


@pytest.fixture(scope="session", autouse=True)
def wait_for_app():
    """Wait up to 30 seconds until /health answers."""
    for _ in range(30):
        try:
            urllib.request.urlopen(f"{BASE_URL}/health", timeout=2)
            return
        except Exception:
            time.sleep(1)
    pytest.fail(f"Application did not start at {BASE_URL}")


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)  # headless = no visible window
        yield b
        b.close()


@pytest.fixture
def page(browser):
    pg = browser.new_page()
    yield pg
    pg.close()


def test_homepage_loads(page):
    response = page.goto(BASE_URL)
    assert response.status == 200


def test_page_title(page):
    page.goto(BASE_URL)
    expect(page).to_have_title("Diff Checker")


def test_ui_elements_exist(page):
    page.goto(BASE_URL)
    expect(page.locator("#text_a")).to_be_visible()
    expect(page.locator("#text_b")).to_be_visible()
    expect(page.locator("#compare")).to_be_visible()


def test_identical_text(page):
    page.goto(BASE_URL)
    page.fill("#text_a", "Hello World")
    page.fill("#text_b", "Hello World")
    page.click("#compare")
    expect(page.locator("#result")).to_contain_text("Texts are identical")


def test_different_text(page):
    page.goto(BASE_URL)
    page.fill("#text_a", "Hello World")
    page.fill("#text_b", "Hello DevOps")
    page.click("#compare")
    expect(page.locator("#result")).to_contain_text("Texts are different")
    expect(page.locator("#diff-output")).to_contain_text("Hello World")
    expect(page.locator("#diff-output")).to_contain_text("Hello DevOps")


def test_health_endpoint(page):
    response = page.request.get(f"{BASE_URL}/health")
    assert response.status == 200
    assert response.json()["status"] == "ok"


def test_environment_value_displayed(page):
    page.goto(BASE_URL)
    expect(page.locator("#app-env")).to_have_text(EXPECTED_ENV)
    expect(page.locator("#app-message")).to_contain_text("Diff Checker")
