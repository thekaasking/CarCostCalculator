# CarCostCalculator

Small Python CLI for quickly comparing car-related monthly costs in the Netherlands.

It combines two scrapers into one monthly figure per license plate:

- `src/web/independer.py` automates Independer to collect car insurance comparison data.
- `src/web/wegenbelasting.py` posts a license plate to wegenbelasting.net and extracts road-tax results per province.

## Project layout

- `run.py` is the entry point.
- `src/cli.py` is the command-line interface: argument parsing, the REPL, and combining/printing/exporting results.
- `src/config.py` stores your personal defaults (address, date of birth, no-claims years) in `config.toml` at the project root (gitignored; see `config.example.toml`).
- `src/models.py` defines the request and result dataclasses.
- `src/utils.py` contains validation, kenteken/price parsing, timing helpers, and HTML parsing.

## Requirements

- Python 3.11+
- `requests`
- `pandas`
- `beautifulsoup4`
- `selenium` (needs a matching Chrome + chromedriver; Selenium Manager fetches
  the driver automatically)
- `rich`

## Usage

Run the project from the root with `uv run .\run.py`, either as a direct command or with no
arguments to get a REPL:

```bash
# One plate, non-interactive. Dashes are optional: PJVP22 works too.
uv run .\run.py ZT-026-P

# Compare multiple plates side by side
uv run .\run.py ZT-026-P PJ-VP-22

# No plate given -> prompts for one at a time until you enter a blank line
uv run .\run.py

# Override a saved default for this run only, and export the results
uv run .\run.py ZT-026-P --coverage all_risk --export costs.csv
```

On first run (or whenever `config.toml` doesn't exist) it asks for your
postcode, huisnummer, toevoeging, date of birth, and no-claims years once and
saves them to `config.toml`, so later runs only need the kenteken. You can
also create it upfront with `cp config.example.toml config.toml` and edit it
directly. Either way it's gitignored, since it holds personal details. Any
field can be overridden per-run with `--postcode`, `--huisnummer`,
`--toevoeging`, `--dob`, or `--schadevrije-jaren` without touching the saved
file.

The "Total/mo" column adds the chosen insurance tier's monthly premium
(`--coverage wa|wa_plus|all_risk`, default `wa_plus`) to the road tax's
monthly (`P/m`) figure.

## Testing

Unit tests cover validation, kenteken/price parsing, HTML parsing, and the
wegenbelasting request/filter logic (network calls are mocked, so they run
offline and fast):

```bash
uv run pytest
```

There are no automated tests for `src/web/independer.py`: it drives a real
Chrome session against Independer's live site, which is too slow/flaky for a
test suite and breaks whenever Independer changes their form. Verify it by
running `run.py` and checking the printed results.

## Notes

- `InsuranceRequest` performs basic input validation in `src/models.py`.
- `normalize_kenteken()` accepts a plate with or without dashes/spaces, in
  any case (e.g. `pjvp22`), and reinserts dashes at the right spots based on
  the plate's letter/digit shape.
- `get_wegenbelastingen()` accepts both the current table columns (`P/m*`, `P/k`, `P/j`) and the older wegenbelasting.net labels.
- Independer's insurance flow shows WA/WA+/All Risk price quotes inline on
  the "Vul je gegevens in" page (no separate results page), so
  `fill_insurance_form()` reads all three coverage cards directly off that
  page instead of navigating further.
