"""Command-line interface for quickly comparing monthly car costs.

Usage:
    uv run .\\run.py ZT-026-P                  # one plate, non-interactive
    uv run .\\run.py ZT-026-P PJ-VP-22          # compare multiple plates
    uv run .\\run.py                            # REPL: prompts for plates
    uv run .\\run.py ZT-026-P --coverage all_risk --export costs.csv
"""

import argparse
import logging
import sys
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table

# Windows consoles/terminals often report a non-UTF-8 encoding (e.g. cp1252)
# even though the terminal itself expects UTF-8 (Git Bash, Windows Terminal),
# which garbles the euro sign. Force UTF-8 so output is consistent.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from src.config import Profile, load_or_prompt_profile
from src.models import InsuranceRequest, VehicleInfo
from src.utils import normalize_kenteken, parse_euro_amount
from src.web.independer import fill_insurance_form
from src.web.rdw import get_vehicle_info
from src.web.wegenbelasting import get_wegenbelastingen

COVERAGE_FIELDS = {
    "wa": "wa_price",
    "wa_plus": "wa_plus_price",
    "all_risk": "all_risk_price",
}
DEFAULT_COVERAGE = "wa_plus"

console = Console()


@dataclass
class CostRow:
    kenteken: str
    coverage: str
    insurance_monthly: float
    road_tax_monthly: float

    @property
    def total_monthly(self) -> float:
        return self.insurance_monthly + self.road_tax_monthly


def compute_costs(raw_kenteken: str, profile: Profile, coverage: str) -> CostRow:
    """Fetch insurance and road-tax data for one kenteken and combine them.

    Args:
        raw_kenteken: The license plate, with or without dashes.
        profile: The requester's personal details.
        coverage: Which insurance tier's price counts toward the total.

    Returns:
        CostRow: The combined monthly cost breakdown.
    """
    kenteken = normalize_kenteken(raw_kenteken)

    request = InsuranceRequest(
        kenteken=kenteken,
        postcode=profile.postcode,
        huisnummer=profile.huisnummer,
        toevoeging=profile.toevoeging,
        geboortedatum=profile.geboortedatum,
        schadevrije_jaren=profile.schadevrije_jaren,
    )
    insurance_result = fill_insurance_form(request=request)
    insurance_monthly = parse_euro_amount(
        getattr(insurance_result, COVERAGE_FIELDS[coverage])
    )

    # Independer's "vanaf" price and wegenbelasting.net's "P/m" figure are
    # both already per-month, so no further conversion is needed here.
    road_tax_monthly = parse_euro_amount(
        get_wegenbelastingen(kenteken=kenteken, timeframe="P/m")
    )

    return CostRow(
        kenteken=kenteken,
        coverage=coverage,
        insurance_monthly=insurance_monthly,
        road_tax_monthly=road_tax_monthly,
    )


def compute_vehicle_info(raw_kenteken: str) -> VehicleInfo:
    """Fetch RDW vehicle + fuel data for one kenteken.

    Args:
        raw_kenteken: The license plate, with or without dashes.

    Returns:
        VehicleInfo: The combined RDW summary (fields are None where RDW has
        no data for this vehicle).
    """
    kenteken = normalize_kenteken(raw_kenteken)
    return get_vehicle_info(kenteken)


def lookup(
    raw_kenteken: str, profile: Profile, coverage: str
) -> tuple[CostRow, VehicleInfo]:
    """Fetch both the cost breakdown and the RDW vehicle info for one plate."""
    cost = compute_costs(raw_kenteken, profile, coverage)
    vehicle = compute_vehicle_info(cost.kenteken)
    return cost, vehicle


def print_results(rows: list[CostRow]) -> None:
    table = Table(title="Monthly car costs")
    table.add_column("Kenteken")
    table.add_column("Coverage")
    table.add_column("Insurance/mo", justify="right")
    table.add_column("Road tax/mo", justify="right")
    table.add_column("Total/mo", justify="right", style="bold")

    for row in rows:
        table.add_row(
            row.kenteken,
            row.coverage,
            f"€{row.insurance_monthly:.2f}",
            f"€{row.road_tax_monthly:.2f}",
            f"€{row.total_monthly:.2f}",
        )
    console.print(table)


def print_vehicle_table(rows: list[VehicleInfo]) -> None:
    table = Table(title="Vehicle info (RDW)")
    table.add_column("Kenteken")
    table.add_column("Merk/model")
    table.add_column("Brandstof")
    table.add_column("Verbruik", justify="right")
    table.add_column("CO2", justify="right")
    table.add_column("Zuinigheid")
    table.add_column("Cat.prijs", justify="right")

    for row in rows:
        merk_model = " ".join(part for part in (row.merk, row.model) if part) or "—"
        verbruik = (
            f"{row.brandstofverbruik_gecombineerd:.1f} L/100km"
            if row.brandstofverbruik_gecombineerd is not None
            else "—"
        )
        co2 = (
            f"{row.co2_uitstoot_gecombineerd} g/km"
            if row.co2_uitstoot_gecombineerd is not None
            else "—"
        )
        catalogusprijs = (
            f"€{row.catalogusprijs:,}".replace(",", ".")
            if row.catalogusprijs is not None
            else "—"
        )
        table.add_row(
            row.kenteken,
            merk_model,
            row.brandstof or "—",
            verbruik,
            co2,
            row.zuinigheidsclassificatie or "—",
            catalogusprijs,
        )
    console.print(table)


def export_results(
    cost_rows: list[CostRow], vehicle_rows: list[VehicleInfo], path: str
) -> None:
    import pandas as pd

    records = [
        {
            "kenteken": cost.kenteken,
            "coverage": cost.coverage,
            "insurance_monthly": cost.insurance_monthly,
            "road_tax_monthly": cost.road_tax_monthly,
            "total_monthly": cost.total_monthly,
            "merk": vehicle.merk,
            "model": vehicle.model,
            "voertuigsoort": vehicle.voertuigsoort,
            "datum_eerste_toelating": vehicle.datum_eerste_toelating,
            "brandstof": vehicle.brandstof,
            "brandstofverbruik_gecombineerd": vehicle.brandstofverbruik_gecombineerd,
            "co2_uitstoot_gecombineerd": vehicle.co2_uitstoot_gecombineerd,
            "zuinigheidsclassificatie": vehicle.zuinigheidsclassificatie,
            "catalogusprijs": vehicle.catalogusprijs,
        }
        for cost, vehicle in zip(cost_rows, vehicle_rows)
    ]
    df = pd.DataFrame(records)
    if path.lower().endswith(".json"):
        df.to_json(path, orient="records", indent=2)
    else:
        df.to_csv(path, index=False)
    console.print(f"Exported to {path}")


def repl(
    profile: Profile, coverage: str
) -> tuple[list[CostRow], list[VehicleInfo]]:
    """Prompt for one kenteken at a time, printing each result immediately.

    This is a single-lookup loop, not compare mode: each plate's result is
    shown as soon as it's computed rather than batched up. To compare plates
    side by side, pass them all as CLI arguments instead.
    """
    cost_rows: list[CostRow] = []
    vehicle_rows: list[VehicleInfo] = []
    console.print("Enter a kenteken to look up (blank to quit).")
    while True:
        try:
            raw = input("Kenteken> ").strip()
        except EOFError:
            break
        if not raw:
            break
        try:
            cost, vehicle = lookup(raw, profile, coverage)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            continue
        cost_rows.append(cost)
        vehicle_rows.append(vehicle)
        print_results([cost])
        print_vehicle_table([vehicle])
    return cost_rows, vehicle_rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quickly compare monthly car costs.")
    parser.add_argument(
        "kentekens",
        nargs="*",
        help="One or more license plates. Omit to enter REPL mode.",
    )
    parser.add_argument(
        "--coverage",
        choices=list(COVERAGE_FIELDS),
        default=DEFAULT_COVERAGE,
        help=f"Insurance tier to count toward the total (default: {DEFAULT_COVERAGE}).",
    )
    parser.add_argument("--postcode", help="Override the saved postcode.")
    parser.add_argument("--huisnummer", help="Override the saved huisnummer.")
    parser.add_argument("--toevoeging", help="Override the saved toevoeging.")
    parser.add_argument(
        "--dob",
        dest="geboortedatum",
        help="Override the saved date of birth (DD-MM-YYYY).",
    )
    parser.add_argument(
        "--schadevrije-jaren", type=int, help="Override the saved no-claims years."
    )
    parser.add_argument(
        "--export", metavar="PATH", help="Also write results to a .csv or .json file."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    profile = load_or_prompt_profile()

    # CLI flags override the saved profile for this run only.
    for field_name in (
        "postcode",
        "huisnummer",
        "toevoeging",
        "geboortedatum",
        "schadevrije_jaren",
    ):
        override = getattr(args, field_name)
        if override is not None:
            setattr(profile, field_name, override)

    if args.kentekens:
        # Multiple plates on the command line is the one "compare mode":
        # results are gathered first and shown together in one table.
        results = [lookup(kenteken, profile, args.coverage) for kenteken in args.kentekens]
        cost_rows = [cost for cost, _ in results]
        vehicle_rows = [vehicle for _, vehicle in results]
        print_results(cost_rows)
        print_vehicle_table(vehicle_rows)
    else:
        # REPL mode is a plain one-at-a-time lookup; repl() already prints
        # each result as it's computed, so there's nothing left to print here.
        cost_rows, vehicle_rows = repl(profile, args.coverage)

    if not cost_rows:
        logging.info("No results to show.")
        return

    if args.export:
        export_results(cost_rows, vehicle_rows, args.export)


if __name__ == "__main__":
    import sys

    print("Please run from run.py! Exiting...")
    sys.exit(1)
