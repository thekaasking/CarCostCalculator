"""RDW (Dutch vehicle authority) open data: base vehicle + fuel datasets.

Two datasets, joined on kenteken:
- "Gekentekende_voertuigen" (m9d7-ebf2): make/model, weight, list price, etc.
- "Gekentekende_voertuigen_brandstof" (8ys7-d773): fuel type, consumption,
  CO2. A vehicle can have more than one fuel row (hybrids); each row carries
  a brandstof_volgnummer, where 1 is the primary fuel.

Field availability varies a lot between vehicles -- this only reads fields
with `.get(...)`, never indexes directly, since RDW's data is sparse.
"""

import logging
from typing import Any

import requests

from src.models import VehicleInfo
from src.utils import parse_rdw_date, parse_rdw_number, timer

VEHICLE_URL = "https://opendata.rdw.nl/resource/m9d7-ebf2.json"
FUEL_URL = "https://opendata.rdw.nl/resource/8ys7-d773.json"


def _compact(kenteken: str) -> str:
    """RDW's API expects the kenteken without dashes or spaces."""
    return kenteken.replace("-", "").replace(" ", "").upper()


@timer
def get_vehicle(kenteken: str) -> dict[str, Any] | None:
    """Fetch the base vehicle record for a kenteken.

    Args:
        kenteken (str): The Dutch license plate number.

    Returns:
        dict | None: The raw RDW record, or None if the plate isn't found.
    """
    logging.debug(f"Fetching RDW vehicle data for {kenteken=}")
    response = requests.get(VEHICLE_URL, params={"kenteken": _compact(kenteken)})
    response.raise_for_status()
    rows = response.json()
    return rows[0] if rows else None


@timer
def get_fuel_rows(kenteken: str) -> list[dict[str, Any]]:
    """Fetch all fuel rows for a kenteken, ordered by brandstof_volgnummer.

    Args:
        kenteken (str): The Dutch license plate number.

    Returns:
        list[dict]: The raw RDW fuel rows (empty if none found). Row 0, if
        present, is the primary fuel.
    """
    logging.debug(f"Fetching RDW fuel data for {kenteken=}")
    response = requests.get(FUEL_URL, params={"kenteken": _compact(kenteken)})
    response.raise_for_status()
    rows = response.json()
    return sorted(rows, key=lambda row: int(row.get("brandstof_volgnummer", 0)))


def get_vehicle_info(kenteken: str) -> VehicleInfo:
    """Combine the base vehicle record and fuel row(s) into one summary.

    Args:
        kenteken (str): The Dutch license plate number.

    Returns:
        VehicleInfo: The combined summary. Fields are None where RDW has no
        data for this vehicle.
    """
    vehicle = get_vehicle(kenteken) or {}
    fuel_rows = get_fuel_rows(kenteken)
    primary_fuel = fuel_rows[0] if fuel_rows else {}

    # Hybrids/dual-fuel vehicles have more than one fuel row, e.g.
    # "Benzine + Elektriciteit"; show all of them rather than just the
    # primary one.
    fuel_description = " + ".join(
        row["brandstof_omschrijving"]
        for row in fuel_rows
        if row.get("brandstof_omschrijving")
    ) or None

    return VehicleInfo(
        kenteken=kenteken,
        merk=vehicle.get("merk"),
        model=vehicle.get("handelsbenaming"),
        voertuigsoort=vehicle.get("voertuigsoort"),
        datum_eerste_toelating=parse_rdw_date(vehicle.get("datum_eerste_toelating")),
        brandstof=fuel_description,
        brandstofverbruik_gecombineerd=parse_rdw_number(
            primary_fuel.get("brandstofverbruik_gecombineerd")
        ),
        co2_uitstoot_gecombineerd=(
            int(primary_fuel["co2_uitstoot_gecombineerd"])
            if primary_fuel.get("co2_uitstoot_gecombineerd")
            else None
        ),
        zuinigheidsclassificatie=vehicle.get("zuinigheidsclassificatie"),
        catalogusprijs=(
            int(vehicle["catalogusprijs"]) if vehicle.get("catalogusprijs") else None
        ),
    )
