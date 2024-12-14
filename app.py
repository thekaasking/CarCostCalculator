import re
import requests
from bs4 import BeautifulSoup


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


def extract_table_data(html: str, province_name: str) -> list:
    soup = BeautifulSoup(html, "html.parser")

    # Find the table with class "wb-resultaat"
    table = soup.find("table", class_="wb-resultaat")
    if not table:
        print("Table not found!")
        return None

    # Find all rows in the table
    rows = table.find_all("tr", class_="wb-resultaat-bedragen")

    # Extract data for the specified province
    for row in rows:
        cells = row.find_all("td")
        if cells and cells[0].get_text(strip=True) == province_name:
            # Extract all the values from the row
            values = [cell.get_text(strip=True) for cell in cells[1:]]
            return values

    print(f"Province {province_name} not found!")
    return None


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


# Example usage
if __name__ == "__main__":
    html_content = send_web_request("P-270-JD")
    if html_content:
        results = extract_table_data(html_content, "Noord-Holland")
        if results:
            print(results)
