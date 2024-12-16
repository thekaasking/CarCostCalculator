import pandas as pd
from src.models import InsuranceResult, InsuranceRequest

from src.web.independer import fill_insurance_form
from src.web.wegenbelasting import get_wegenbelastingen


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

    # insuranse_result: InsuranceResult = fill_insurance_form(request=car_request)
    # print(insuranse_result)
    wegenbelastingen_data_kwartaal = get_wegenbelastingen(
        kenteken=kenteken, province="Zuid-Holland"
    )
    print(wegenbelastingen_data_kwartaal)


if __name__ == "__main__":
    import sys

    print("Please run from run.py! Exiting...")
    sys.exit(1)
