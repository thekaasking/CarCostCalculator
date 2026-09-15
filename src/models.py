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
class VehicleInfo:
    """Basic vehicle + fuel data from the RDW open data API.

    Fields are Optional because the RDW dataset is sparse: not every
    field is populated for every vehicle (this varies a lot between fuel
    types, e.g. electric vehicles rarely carry a combined-consumption
    figure in the same field a petrol car does).
    """

    kenteken: str
    merk: str | None
    model: str | None
    voertuigsoort: str | None
    datum_eerste_toelating: str | None  # DD-MM-YYYY
    brandstof: str | None
    brandstofverbruik_gecombineerd: float | None  # L/100km
    co2_uitstoot_gecombineerd: int | None  # g/km
    zuinigheidsclassificatie: str | None  # efficiency class, e.g. "A"
    catalogusprijs: int | None  # list price when new, EUR


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
