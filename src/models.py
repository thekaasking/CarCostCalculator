from dataclasses import dataclass

from src.utils import check_valid_kenteken, check_valid_dob


@dataclass
class InsuranceResult:
    wa_count: str
    wa_price: str
    wa_plus_count: str
    wa_plus_price: str
    all_risk_count: str
    all_risk_price: str


@dataclass
class InsuranceRequest:
    kenteken: str
    postcode: str
    huisnummer: str
    toevoeging: str
    geboortedatum: str
    schadevrije_jaren: int

    # post init:
    def __post_init__(self):
        check_valid_kenteken(self.kenteken)
        check_valid_dob(self.geboortedatum)


# class WegenbelastingenResult:
