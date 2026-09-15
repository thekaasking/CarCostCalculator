import logging
import re
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
        r"^[A-Z]{2}-\d{3}-[A-Z]{1}$",  # Format: XX-999-X
        r"^\d{1}-[A-Z]{2}-\d{3}$",  # Format: 9-XX-999
        r"^\d{1}-[A-Z]{3}-\d{2}$",  # Format: 9-XXX-99
    ]

    # Check if the plate matches any of the patterns
    for pattern in patterns:
        if re.match(pattern, kenteken):
            logging.info(f"Kenteken {kenteken} is valid!")
            return

    raise ValueError(f"Invalid kenteken: {kenteken}")


# Dutch kentekens are always 6 alphanumeric characters, grouped into 3 dashed
# parts. The letter/digit "shape" of those 6 characters uniquely identifies
# which of the 8 group-length patterns applies, e.g. "JFN60N" has shape
# "LLLLDD" -> groups (2, 2, 2) -> "JFN-60-N". Kept in sync with the regexes
# in check_valid_kenteken().
_KENTEKEN_SHAPES: dict[str, tuple[int, ...]] = {
    "LLDDLL": (2, 2, 2),  # XX-99-XX
    "DDLLDD": (2, 2, 2),  # 99-XX-99
    "LLLLDD": (2, 2, 2),  # XX-XX-99
    "DDLLLD": (2, 3, 1),  # 99-XXX-9
    "LDDDLL": (1, 3, 2),  # X-999-XX
    "LLDDDL": (2, 3, 1),  # XX-999-X
    "DLLDDD": (1, 2, 3),  # 9-XX-999
    "DLLLDD": (1, 3, 2),  # 9-XXX-99
}


def normalize_kenteken(kenteken: str) -> str:
    """Normalize a Dutch kenteken to its canonical dashed form.

    Accepts the plate with or without dashes/spaces, in any case, e.g.
    "jfn60n" or "JFN 60 N", and returns "JFN-60-N".

    Args:
        kenteken (str): The raw kenteken, with or without separators.

    Returns:
        str: The canonical dashed kenteken.

    Raises:
        ValueError: If the kenteken doesn't match any known format.
    """
    compact = re.sub(r"[\s-]", "", kenteken).upper()
    shape = "".join(
        "L" if ch.isalpha() else "D" if ch.isdigit() else "?" for ch in compact
    )
    groups = _KENTEKEN_SHAPES.get(shape)
    if groups is None:
        raise ValueError(f"Invalid kenteken: {kenteken}")

    parts = []
    pos = 0
    for size in groups:
        parts.append(compact[pos : pos + size])
        pos += size
    normalized = "-".join(parts)

    check_valid_kenteken(normalized)
    return normalized


def parse_euro_amount(value: str) -> float:
    """Parse a Dutch-formatted euro amount into a float.

    Handles a comma decimal separator and an optional "." thousands
    separator or "€" sign, e.g. "75,71" -> 75.71, "€ 1.234,56" -> 1234.56.

    Args:
        value (str): The amount as shown on the source website.

    Returns:
        float: The parsed amount.
    """
    cleaned = value.replace("€", "").strip().replace(".", "").replace(",", ".")
    return float(cleaned)


def parse_rdw_date(value: str | None) -> str | None:
    """Parse an RDW "YYYYMMDD" date string into "DD-MM-YYYY".

    Args:
        value (str | None): The raw RDW date field, e.g. "20140508".

    Returns:
        str | None: "08-05-2014", or None if value is missing/blank.
    """
    if not value:
        return None
    return f"{value[6:8]}-{value[4:6]}-{value[:4]}"


def parse_rdw_number(value: str | None) -> float | None:
    """Parse a numeric RDW field into a float.

    Unlike the Dutch-formatted prices on wegenbelasting.net/Independer, RDW's
    open data API uses a plain "." decimal separator, e.g. "5.30".

    Args:
        value (str | None): The raw RDW numeric field.

    Returns:
        float | None: The parsed number, or None if value is missing/blank.
    """
    if not value:
        return None
    return float(value)


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

    data_4_columns: list[list[str]] = []
    data_7_columns: list[list[str]] = []
    for row in rows:
        # Only extract direct children, avoiding recursive nesting
        cols = row.find_all("td", recursive=False)
        row_values = [col.get_text(strip=True) for col in cols]
        if len(row_values) == 4:
            data_4_columns.append(row_values)
        elif len(row_values) == 7:
            data_7_columns.append(row_values)

    if data_4_columns:
        columns = ["Provincie", "P/m*", "P/k", "P/j"]
        df_cleaned = pd.DataFrame(data_4_columns, columns=columns)
    elif data_7_columns:
        columns = [
            "Provincie",
            "P/m* (Wegenbelasting)",
            "P/k (Wegenbelasting)",
            "P/j (Wegenbelasting)",
            "P/m* (Schone Auto)",
            "P/k (Schone Auto)",
            "P/j (Schone Auto)",
        ]
        df_cleaned = pd.DataFrame(data_7_columns, columns=columns)
        df_cleaned = df_cleaned[
            [
                "Provincie",
                "P/m* (Wegenbelasting)",
                "P/k (Wegenbelasting)",
                "P/j (Wegenbelasting)",
            ]
        ].rename(
            columns={
                "P/m* (Wegenbelasting)": "P/m*",
                "P/k (Wegenbelasting)": "P/k",
                "P/j (Wegenbelasting)": "P/j",
            }
        )
    else:
        logging.warning("No wegenbelastingen rows with 4 or 7 columns were found.")
        df_cleaned = pd.DataFrame(columns=["Provincie", "P/m*", "P/k", "P/j"])

    logging.debug("Data extracted successfully from the HTML content.")

    return df_cleaned
