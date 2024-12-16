import pandas as pd
from src.models import InsuranceResult, InsuranceRequest

from src.utils import check_valid_kenteken, extract_wegenbelastingen_data
from src.web.independer import fill_insurance_form
from src.web.wegenbelasting import request_wegenbelasting


def main():
    kenteken: str = "N-214-JD"

    car_request: InsuranceRequest = InsuranceRequest(
        kenteken=kenteken,
        postcode="2562 HX",
        huisnummer="414",
        toevoeging="",
        geboortedatum="25-09-2002",
        schadevrije_jaren=3,
    )

    fill_insurance_form(request=car_request)

    return
    # html_content = send_web_request("P-270-JD")
    # if html_content:
    #     df: pd.DataFrame = extract_wegenbelastingen_data(html_content)


if __name__ == "__main__":
    import sys

    print("Please run from run.py! Exiting...")
    sys.exit(1)
