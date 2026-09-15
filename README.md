# CarCostCalculator

Small Python project for comparing car-related costs in the Netherlands.

It currently provides two scrapers:

- `src/web/independer.py` automates Independer to collect car insurance comparison data.
- `src/web/wegenbelasting.py` posts a license plate to wegenbelasting.net and extracts road-tax results per province.

## Project layout

- `run.py` is the entry point.
- `src/app.py` contains the local demo flow.
- `src/models.py` defines the request and result dataclasses.
- `src/utils.py` contains validation, timing helpers, and HTML parsing.

## Requirements

- Python 3.11+
- `requests`
- `pandas`
- `beautifulsoup4`
- `selenium` (needs a matching Chrome + chromedriver; Selenium Manager fetches
  the driver automatically)

## Usage

Run the project from the root with:

```bash
uv run .\run.py
```

The current demo in `src/app.py` validates the license plate and date of birth, fills in Independer's car insurance comparison flow, and fetches wegenbelasting data for a chosen province.

## Testing

Unit tests cover validation, HTML parsing, and the wegenbelasting request/filter
logic (network calls are mocked, so they run offline and fast):

```bash
uv run pytest
```

There are no automated tests for `src/web/independer.py`: it drives a real
Chrome session against Independer's live site, which is too slow/flaky for a
test suite and breaks whenever Independer changes their form. Verify it by
running `run.py` and checking the printed `InsuranceResult`.

## Notes

- `InsuranceRequest` performs basic input validation in `src/models.py`.
- `get_wegenbelastingen()` accepts both the current table columns (`P/m*`, `P/k`, `P/j`) and the older wegenbelasting.net labels.
- Independer's insurance flow now shows WA/WA+/All Risk price quotes inline on
  the "Vul je gegevens in" page (no separate results page), so
  `fill_insurance_form()` reads all three coverage cards directly off that
  page instead of navigating further.
