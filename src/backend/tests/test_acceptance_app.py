"""Tests de aceptación UI con Selenium para la aplicación desplegada."""

# pylint: disable=redefined-outer-name

import os
import time
from collections.abc import Iterator

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait


pytestmark = pytest.mark.acceptance


def _build_driver() -> WebDriver:
    """Crea un driver local o remoto según variables de entorno."""
    browser = os.getenv("SELENIUM_BROWSER", "chrome").lower()
    if browser != "chrome":
        pytest.skip(f"Navegador no soportado para estas pruebas: {browser}")

    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1200")

    remote_url = os.getenv("SELENIUM_REMOTE_URL")
    if remote_url:
        return webdriver.Remote(command_executor=remote_url, options=options)

    driver_path = os.getenv("CHROMEDRIVER_PATH")
    if driver_path:
        return webdriver.Chrome(service=ChromeService(driver_path), options=options)

    return webdriver.Chrome(options=options)


@pytest.fixture(scope="module")
def app_base_url() -> str:
    """Entrega la URL base del frontend bajo prueba."""
    base_url = os.getenv("APP_BASE_URL")
    if not base_url:
        pytest.skip(
            "Define APP_BASE_URL para ejecutar las pruebas de aceptación con Selenium."
        )
    return base_url.rstrip("/")


@pytest.fixture(scope="module")
def browser(app_base_url: str) -> Iterator[WebDriver]:
    """Entrega un navegador Selenium reutilizable para la suite de aceptación."""
    del app_base_url
    try:
        driver = _build_driver()
    except (WebDriverException, OSError) as exc:
        pytest.skip(f"No fue posible iniciar Selenium: {exc}")

    driver.implicitly_wait(1)
    try:
        yield driver
    finally:
        driver.quit()


def _wait(browser: WebDriver) -> WebDriverWait:
    """Construye un wait explícito con timeout razonable."""
    return WebDriverWait(browser, 15)


def _open_create_group_form(browser: WebDriver, base_url: str) -> None:
    """Abre la vista inicial y despliega el formulario de crear grupo."""
    browser.get(base_url)
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "groups-view")))
    browser.find_element(By.ID, "toggle-create-form").click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "create-group-form")))


def _add_member(browser: WebDriver, name: str) -> None:
    """Agrega un miembro usando el input tags del formulario."""
    member_input = browser.find_element(By.ID, "group-members")
    member_input.clear()
    member_input.send_keys(name)
    member_input.send_keys(Keys.ENTER)


def _create_group(browser: WebDriver, base_url: str, group_name: str) -> None:
    """Crea un grupo desde la UI con tres miembros de prueba."""
    _open_create_group_form(browser, base_url)
    browser.find_element(By.ID, "group-name").send_keys(group_name)

    for member in ("Ana", "Beto", "Carla"):
        _add_member(browser, member)

    browser.find_element(
        By.CSS_SELECTOR, "#create-group-form button[type='submit']"
    ).click()
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "group-title")))
    _wait(browser).until(
        lambda drv: drv.find_element(By.ID, "group-title").text == group_name
    )


def test_acceptance_can_create_group_from_ui(browser: WebDriver, app_base_url: str):
    """Verifica que un usuario pueda crear un grupo desde la interfaz."""
    group_name = f"Aceptacion Grupo {int(time.time() * 1000)}"

    _create_group(browser, app_base_url, group_name)

    assert browser.find_element(By.ID, "group-title").text == group_name
    members = browser.find_elements(By.CSS_SELECTOR, "#members-bar .badge")
    assert [member.text for member in members] == ["👤 Ana", "👤 Beto", "👤 Carla"]


def test_acceptance_can_register_expense_and_see_balances(
    browser: WebDriver, app_base_url: str
):
    """Verifica el flujo UI de crear grupo, registrar gasto y ver balances."""
    group_name = f"Aceptacion Gasto {int(time.time() * 1000)}"
    _create_group(browser, app_base_url, group_name)

    browser.find_element(By.ID, "expense-desc").send_keys("Hotel")
    browser.find_element(By.ID, "expense-amount").send_keys("90")
    Select(browser.find_element(By.ID, "expense-paid-by")).select_by_visible_text("Ana")
    browser.find_element(
        By.CSS_SELECTOR, "#add-expense-form button[type='submit']"
    ).click()

    _wait(browser).until(
        ec.visibility_of_element_located((By.CSS_SELECTOR, ".expense-item"))
    )
    expense_desc = browser.find_element(By.CSS_SELECTOR, ".expense-desc").text
    expense_paid_by = browser.find_element(By.CSS_SELECTOR, ".expense-meta strong").text
    assert expense_desc == "Hotel"
    assert expense_paid_by == "Ana"

    browser.find_element(By.CSS_SELECTOR, ".tab[data-tab='balances']").click()
    _wait(browser).until(
        ec.visibility_of_element_located(
            (By.CSS_SELECTOR, "#balances-list .balance-card")
        )
    )
    balance_texts = [
        card.text
        for card in browser.find_elements(
            By.CSS_SELECTOR, "#balances-list .balance-card"
        )
    ]
    assert any("Ana" in text and "60" in text for text in balance_texts)
    assert any("Beto" in text and "30" in text for text in balance_texts)
    assert any("Carla" in text and "30" in text for text in balance_texts)


def test_acceptance_can_delete_group_from_ui(browser: WebDriver, app_base_url: str):
    """Verifica que un usuario pueda eliminar un grupo desde la vista detalle."""
    group_name = f"Aceptacion Borrado {int(time.time() * 1000)}"
    _create_group(browser, app_base_url, group_name)

    browser.find_element(By.ID, "delete-group-btn").click()
    browser.switch_to.alert.accept()

    _wait(browser).until(ec.visibility_of_element_located((By.ID, "groups-view")))
    _wait(browser).until(ec.visibility_of_element_located((By.ID, "group-list")))

    group_cards = browser.find_elements(By.CSS_SELECTOR, "#group-list .group-card h3")
    assert all(card.text != group_name for card in group_cards)
