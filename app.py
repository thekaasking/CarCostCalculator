import re
import requests
import pandas as pd

from pprint import pprint
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def get_webdriver() -> webdriver:
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)

    return driver


def fill_insurance_form(
    kenteken: str,
    postcode: str,
    huisnummer: str,
    toevoeging: str,
    dob: str,
    schadevrije_jaren: int,
):
    """
    Fills in the car insurance comparison form on Independer.nl, navigates to the next page, and fills additional details.

    Args:
        kenteken (str): License plate number.
        postcode (str): Postal code.
        huisnummer (str): House number.
        toevoeging (str): Address addition (optional).
        dob (str): Date of birth (format: DD-MM-YYYY).
        schadevrije_jaren (int): Number of claim-free years.
    """
    # Initialize the Chrome WebDriver (ensure chromedriver is in your PATH)
    driver = get_webdriver()
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to the first webpage
        url = "https://www.independer.nl/autoverzekering/intro.aspx"
        driver.get(url)

        # Fill in the 'Kenteken' field
        kenteken_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='kenteken']"))
        )
        kenteken_field.send_keys(kenteken)

        # Fill in the 'Postcode' field
        postcode_field = driver.find_element(
            By.CSS_SELECTOR, "input[placeholder='bijv. 3563 HH']"
        )
        postcode_field.send_keys(postcode)

        # Fill in the 'Huisnummer' field
        huisnummer_field = driver.find_element(
            By.CSS_SELECTOR, "input[placeholder='Huisnummer']"
        )
        huisnummer_field.send_keys(huisnummer)

        # Fill in the 'Toevoeging' field (optional)
        toevoeging_field = driver.find_element(
            By.CSS_SELECTOR, "input[placeholder='toev.']"
        )
        toevoeging_field.send_keys(toevoeging)

        # Click on the 'Vergelijk autoverzekeringen' button
        vergelijk_button = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Vergelijk autoverzekeringen')]"
        )
        vergelijk_button.click()

        # Wait for the next page to load
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//h1[contains(text(), 'Vul je gegevens in')]")
            )
        )

        # Fill in the date of birth
        dob_field = driver.find_element(
            By.CSS_SELECTOR, "input[placeholder='bijv. 15-01-1981']"
        )
        dob_field.send_keys(dob)

        # Select 'Vandaag' for 'Wanneer wil je je verzekering in laten gaan?'
        vandaag_radio = driver.find_element(
            By.XPATH, "//label[contains(text(), 'Vandaag')]"
        )
        vandaag_radio.click()

        # Select 'Nee' for 'Heb je al een verzekering voor deze auto?'
        nee_radio = driver.find_element(By.XPATH, "//label[contains(text(), 'Nee')]")
        nee_radio.click()

        # Fill in the 'Hoeveel schadevrije jaren heb je?' field
        schadevrije_field = driver.find_element(
            By.CSS_SELECTOR, "input[placeholder='-5 t/m 99']"
        )
        schadevrije_field.send_keys(str(schadevrije_jaren))

        # Select 'Tot en met 7.500' in the dropdown for 'Hoeveel kilometers rij je per jaar?'
        kilometers_dropdown = driver.find_element(By.CSS_SELECTOR, "select")
        select = Select(kilometers_dropdown)
        select.select_by_visible_text("Tot en met 7.500")

        # Click on the 'Ga verder' button
        ga_verder_button = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Ga verder')]"
        )
        ga_verder_button.click()

        # Optional: Wait to observe results before closing
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#some-results-selector"))
        )
        print("Form submitted successfully and results loaded.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()


def check_valid_kenteken(kenteken: str) -> None:
    """Check if the given Dutch kenteken is valid. If not, raise a ValueError."""
    patterns = [
        r"^[A-Z]{2}-\d{2}-[A-Z]{2}$",  # Format: XX-99-XX
        r"^\d{2}-[A-Z]{2}-\d{2}$",  # Format: 99-XX-99
        r"^[A-Z]{2}-[A-Z]{2}-\d{2}$",  # Format: XX-XX-99
        r"^\d{2}-[A-Z]{3}-\d{1}$",  # Format: 99-XXX-9
        r"^[A-Z]{1}-\d{3}-[A-Z]{2}$",  # Format: X-999-XX
        r"^\d{1}-[A-Z]{2}-\d{3}$",  # Format: 9-XX-999
    ]

    # Check if the plate matches any of the patterns
    for pattern in patterns:
        if re.match(pattern, kenteken):
            print(f"Kenteken {kenteken} is valid!")
            return

    raise ValueError(f"Invalid kenteken: {kenteken}")


def extract_wegenbelastingen_data(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")

    rows = soup.find_all("tr", class_="wb-resultaat-bedragen")

    data = []
    for row in rows:
        # Only extract direct children, avoiding recursive nesting
        cols = row.find_all("td", recursive=False)
        cols = [col.get_text(strip=True) for col in cols]
        data.append(cols)

    data = [row for row in data if len(row) == 7]
    columns = [
        "Provincie",
        "P/m* (Wegenbelasting)",
        "P/k (Wegenbelasting)",
        "P/j (Wegenbelasting)",
        "P/m* (Schone Auto)",
        "P/k (Schone Auto)",
        "P/j (Schone Auto)",
    ]

    df_cleaned = pd.DataFrame(data, columns=columns)

    return df_cleaned


def send_web_request(kenteken: str):
    check_valid_kenteken(kenteken)

    # Define the URL and payload
    url = "https://wegenbelasting.net/kenteken-check/"
    payload = {"submit_berekenen_kenteken": "1", "k": kenteken}

    # Define the headers
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "nl-NL,nl;q=0.6",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "wegenbelasting.net",
        "Origin": "https://wegenbelasting.net",
        "Referer": "https://wegenbelasting.net/kenteken-check/",
        "Sec-Ch-Ua": '"Brave";v="131", "Chromium";v="131", "Not_A_Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    try:
        # Log the request being sent
        print(
            f"Sending POST request to {url} with payload {payload} and headers {headers}"
        )

        # Send the POST request
        response = requests.post(url, data=payload, headers=headers)

        # Log the response status
        print(f"Response received with status code: {response.status_code}")

        # Return the response HTML
        return response.text
    except requests.RequestException as e:
        # Log any errors encountered
        print(f"An error occurred: {e}")
        return None


def main():
    fill_insurance_form("XX-123-YY", "3563 HH", "12", "A", "15-01-1981", 5)

    return
    html_content = send_web_request("P-270-JD")
    if html_content:
        df: pd.DataFrame = extract_wegenbelastingen_data(html_content)

        # Save the DataFrame to a CSV file
        df.to_csv("output.csv", index=False)


# Example usage
if __name__ == "__main__":
    main()
