import time
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

from src.utils import timer
from src.models import InsuranceResult, InsuranceRequest


def get_webdriver(debug: bool = False) -> webdriver:
    """Initializes a Chrome WebDriver instance.

    Args:
        debug (bool, optional): If False, launches headless. Defaults to False.

    Returns:
        webdriver: The Chrome WebDriver instance.
    """
    logging.debug("Initializing Chrome WebDriver")
    chrome_options = Options()
    if not debug:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)

    return driver


@timer
def fill_insurance_form(
    request: InsuranceRequest,
) -> InsuranceResult:
    """
    Fills in the car insurance comparison form on Independer.nl, navigates to the next page, and fills additional details.

    Args:
        request (InsuranceRequest): The request object containing the user's details.

    Returns:
        InsuranceResult: The result object containing the extracted insurance data.

    Raises:
        Exception: If an error occurs during the process.
    """
    logging.debug(f"Getting insurance data from Independer.nl for {request=}")
    kenteken: str = request.kenteken
    postcode: str = request.postcode
    huisnummer: str = request.huisnummer
    toevoeging: str = request.toevoeging
    dob: str = request.geboortedatum
    schadevrije_jaren: int = request.schadevrije_jaren

    # Initialize the Chrome WebDriver (ensure chromedriver is in your PATH)
    driver: webdriver.Chrome = get_webdriver()
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to the first webpage
        url = "https://www.independer.nl/autoverzekering/intro.aspx"
        driver.get(url)
        logging.debug(f"Opened {url}")

        cookie_button = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Liever niet')]"
        )
        cookie_button.click()
        logging.debug("Clicked on the cookie button")

        kenteken_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='kenteken']"))
        )
        kenteken_field.send_keys(kenteken)
        logging.debug(f"Filled in the kenteken field with {kenteken}")

        postcode_field = driver.find_element(By.CSS_SELECTOR, "input[name='postcode']")
        postcode_field.send_keys(postcode)
        logging.debug(f"Filled in the postcode field with {postcode}")

        huisnummer_field = driver.find_element(
            By.CSS_SELECTOR, "input[name='huisnummer']"
        )
        huisnummer_field.send_keys(huisnummer)
        logging.debug(f"Filled in the huisnummer field with {huisnummer}")

        toevoeging_field = driver.find_element(
            By.CSS_SELECTOR, "input[name='huisnummertoevoeging']"
        )
        toevoeging_field.send_keys(toevoeging)
        logging.debug(f"Filled in the toevoeging field with {toevoeging}")

        vergelijk_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[@aria-label='klik op deze knop om verzekeringen te vergelijken']",
                )
            )
        )
        driver.execute_script("arguments[0].click();", vergelijk_button)
        sleep_after_compare: int = 5
        logging.debug(
            f"Clicked on the 'Vergelijk' button. Sleeping for {sleep_after_compare} seconds"
        )
        time.sleep(
            sleep_after_compare
        )  # Small pause before waiting for the next element

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//h1[contains(text(), 'Vul je gegevens in')]")
            )
        )
        logging.debug("Navigated to the next page with the form")

        dob_field = driver.find_element(
            By.CSS_SELECTOR, "input[placeholder='bijv. 15-01-1981']"
        )
        dob_field.send_keys(dob)
        logging.debug(f"Filled in the geboortedatum field with {dob}")

        vandaag_label = driver.find_element(
            By.CSS_SELECTOR, "label[for='radio-5'] span.radio--inner--content"
        )
        driver.execute_script("arguments[0].click();", vandaag_label)
        logging.debug("Clicked on the 'Vandaag' radio button")

        nee_radio = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//span[contains(@class, 'radio--inner--content') and text()='Nee']/ancestor::label",
                )
            )
        )
        nee_radio.click()
        logging.debug("Clicked on the 'Nee' radio button")

        schadevrije_field = driver.find_element(
            By.CSS_SELECTOR, "input[placeholder='-5 t/m 99']"
        )
        schadevrije_field.send_keys(str(schadevrije_jaren))
        logging.debug(f"Filled in the schadevrije jaren field with {schadevrije_jaren}")

        kilometers_dropdown = driver.find_element(By.CSS_SELECTOR, "select")
        select = Select(kilometers_dropdown)
        select.select_by_visible_text("Tot en met 7.500")
        logging.debug("Selected 'Tot en met 7.500' from the dropdown")

        # Click on the 'Ga verder' button
        ga_verder_button = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Ga verder')]"
        )
        driver.execute_script("arguments[0].click();", ga_verder_button)

        sleep_after_ga_verder: int = 5
        logging.debug(
            f"Clicked on the 'Ga verder' button. Sleeping for {sleep_after_ga_verder} seconds"
        )
        time.sleep(sleep_after_ga_verder)

        logging.debug("Extracting insurance price data...")
        # Extract counts and prices for WA
        wa_count = driver.find_element(
            By.XPATH, "//strong[contains(@class, 'ng-tns-c12299694-13')]/span"
        ).text
        wa_price = driver.find_element(
            By.XPATH, "//strong[contains(@class, 'price ng-tns-c12299694-13')]"
        ).text

        # Extract counts and prices for WA+
        wa_plus_count = driver.find_element(
            By.XPATH, "//strong[contains(@class, 'ng-tns-c12299694-15')]/span"
        ).text
        wa_plus_price = driver.find_element(
            By.XPATH, "//strong[contains(@class, 'price ng-tns-c12299694-15')]"
        ).text

        # Extract counts and prices for All Risk
        all_risk_count = driver.find_element(
            By.XPATH, "//strong[contains(@class, 'ng-tns-c12299694-17')]/span"
        ).text
        all_risk_price = driver.find_element(
            By.XPATH, "//strong[contains(@class, 'price ng-tns-c12299694-17')]"
        ).text

        logging.debug("Successfully extracted insurance data!")
        logging.debug(f"WA: {wa_count} verzekeringen, vanaf €{wa_price}")
        logging.debug(f"WA+: {wa_plus_count} verzekeringen, vanaf €{wa_plus_price}")
        logging.debug(
            f"All Risk: {all_risk_count} verzekeringen, vanaf €{all_risk_price}"
        )
        return InsuranceResult(
            wa_count=wa_count,
            wa_price=wa_price,
            wa_plus_count=wa_plus_count,
            wa_plus_price=wa_plus_price,
            all_risk_count=all_risk_count,
            all_risk_price=all_risk_price,
        )

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise e

    finally:
        driver.quit()
