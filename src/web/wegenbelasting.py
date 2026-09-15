import logging
from typing import Optional

import pandas as pd
import requests

from src.utils import extract_wegenbelastingen_data, timer


def get_wegenbelastingen(
    kenteken: str,
    province: Optional[str] = None,
    timeframe: Optional[str] = "P/k",
) -> pd.DataFrame | float:
    """Get the wegenbelastingen data for the given kenteken.

    Can source from: columns = [
        "Provincie",
        "P/m* (Wegenbelasting)",
        "P/k (Wegenbelasting)",
        "P/j (Wegenbelasting)",
        "P/m* (Schone Auto)",
        "P/k (Schone Auto)",
        "P/j (Schone Auto)",
    ]

    Args:
        kenteken (str): The Dutch license plate number.
        province (str, optional): The province to filter by. Defaults to None.
        timeframe (str, optional): The timeframe to filter by. Defaults to None.

    Returns:
        pd.DataFrame: The extracted data.
        float: The wegenbelastingen value for the given province and timeframe.
    """
    logging.debug(
        f"Getting wegenbelastingen data for {kenteken=}, {province=}, {timeframe=}"
    )
    timeframe_aliases = {
        "P/m": "P/m*",
        "P/k": "P/k",
        "P/j": "P/j",
        "P/m* (Wegenbelasting)": "P/m*",
        "P/k (Wegenbelasting)": "P/k",
        "P/j (Wegenbelasting)": "P/j",
    }
    if timeframe is not None:
        assert timeframe in timeframe_aliases, "Invalid timeframe"
    # Send the request to wegenbelasting.net
    html_content = request_wegenbelasting(kenteken)

    if html_content:
        df = extract_wegenbelastingen_data(html_content)
        if timeframe is not None:
            timeframe = timeframe_aliases[timeframe]
        if province:
            # check if the province exists in the dataframe
            if province in df["Provincie"].unique():
                df = df[df["Provincie"] == province]
                if timeframe:
                    return df[timeframe].values[0]
            else:
                raise ValueError(f"Province {province} not found in the dataframe")
        elif timeframe:
            return df[timeframe].values[0]

        return df

    else:
        return None


@timer
def request_wegenbelasting(kenteken: str):
    """Send a POST request to wegenbelasting.net with the given kenteken.

    Args:
        kenteken (str): The Dutch license plate number. Assumes format is already checked.

    Returns:
        str: The HTML content of the response.
    """

    # Define the URL and payload
    url = "https://wegenbelasting.net/kenteken-check/"
    payload = {"submit_berekenen_kenteken": "1", "k": kenteken}

    # Define the headers
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
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
        logging.debug(
            f"Sending POST request to {url} with payload {payload} and headers {headers}"
        )

        # Send the POST request
        response = requests.post(url, data=payload, headers=headers)

        # Log the response status
        logging.debug(
            f"Response received from {url=} with status code: {response.status_code}"
        )

        # Return the response HTML
        return response.text
    except requests.RequestException as e:
        logging.debug(f"An error occurred: {e}")
        return None
