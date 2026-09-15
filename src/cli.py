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
from src.models import InsuranceRequest
from src.utils import normalize_kenteken, parse_euro_amount
from src.web.independer import fill_insurance_form
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


def export_results(rows: list[CostRow], path: str) -> None:
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "kenteken": row.kenteken,
                "coverage": row.coverage,
                "insurance_monthly": row.insurance_monthly,
                "road_tax_monthly": row.road_tax_monthly,
                "total_monthly": row.total_monthly,
            }
            for row in rows
        ]
    )
    if path.lower().endswith(".json"):
        df.to_json(path, orient="records", indent=2)
    else:
        df.to_csv(path, index=False)
    console.print(f"Exported to {path}")


def repl(profile: Profile, coverage: str) -> list[CostRow]:
    """Prompt for one kenteken at a time until the user enters a blank line."""
    rows: list[CostRow] = []
    console.print("Enter a kenteken to look up (blank to quit).")
    while True:
        try:
            raw = input("Kenteken> ").strip()
        except EOFError:
            break
        if not raw:
            break
        try:
            rows.append(compute_costs(raw, profile, coverage))
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
    return rows


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
        rows = [
            compute_costs(kenteken, profile, args.coverage)
            for kenteken in args.kentekens
        ]
    else:
        rows = repl(profile, args.coverage)

    if not rows:
        logging.info("No results to show.")
        return

    print_results(rows)
    if args.export:
        export_results(rows, args.export)


if __name__ == "__main__":
    import sys

    print("Please run from run.py! Exiting...")
    sys.exit(1)
