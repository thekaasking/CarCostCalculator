import re
import logging
from functools import wraps
from time import time
import pandas as pd
from bs4 import BeautifulSoup


def timer(func):
    """Print the runtime of the decorated function."""

    @wraps(func)
    def wrapper_timer(*args, **kwargs):
        logging.debug(f"Started {func.__name__}...")
        start_time = time()
        value = func(*args, **kwargs)
        end_time = time()
        logging.debug(f"Finished {func.__name__} in {end_time - start_time:.2f}s.")
        return value

    return wrapper_timer


def check_valid_dob(dob: str) -> None:
    """Check if the given date of birth is valid.

    Checks for format DD-MM-YYYY and if the date is valid.

    Args:
        dob (str): The date of birth.

    Raises:
        ValueError: If the date is invalid.
    """
    logging.debug(f"Checking date of birth: {dob}")
    try:
        day, month, year = dob.split("-")
        day, month, year = int(day), int(month), int(year)
    except ValueError:
        raise ValueError(f"Invalid date of birth: {dob}")

    # Check each part of the date
    if not (1 <= day <= 31):
        raise ValueError(f"Invalid day: {day}")

    if not (1 <= month <= 12):
        raise ValueError(f"Invalid month: {month}")

    if not (1900 <= year <= 2021):
        raise ValueError(f"Invalid year: {year}")

    logging.info(f"Date of birth {dob} is valid!")


def check_valid_kenteken(kenteken: str) -> None:
    """Check if the given Dutch kenteken is valid.

    Args:
        kenteken (str): The Dutch license plate number.

    Raises:
        ValueError: If the kenteken is invalid.
    """
    logging.debug(f"Checking kenteken: {kenteken}")
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
            logging.info(f"Kenteken {kenteken} is valid!")
            return

    raise ValueError(f"Invalid kenteken: {kenteken}")


@timer
def extract_wegenbelastingen_data(html: str) -> pd.DataFrame:
    """Extract the wegenbelastingen data from the given HTML content.

    Args:
        html (str): The HTML content of the wegenbelastingen.net response.

    Returns:
        pd.DataFrame: dataframe containing the extracted data.
    """
    logging.debug("Extracting wegenbelastingen data...")
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

    if df_cleaned.empty:
        logging.warning(
            "Found empty DF. Trying alternative extraction method for wegenbelastingen data with 4 columns ..."
        )
        data = [row for row in data if len(row) == 4]
        columns = [
            "Provincie",
            "P/m*",
            "P/k",
            "P/j",
        ]
        df_cleaned = pd.DataFrame(data, columns=columns)

    logging.debug("Data extracted successfully from the HTML content.")

    return df_cleaned
