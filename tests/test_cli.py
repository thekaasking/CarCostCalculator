import pytest

import src.cli as cli_module
from src.config import Profile
from src.models import InsuranceResult


@pytest.fixture
def profile():
    return Profile(
        postcode="2562 HX",
        huisnummer="414",
        toevoeging="",
        geboortedatum="25-09-2002",
        schadevrije_jaren=3,
    )


@pytest.fixture(autouse=True)
def mock_scrapers(monkeypatch):
    monkeypatch.setattr(
        cli_module,
        "fill_insurance_form",
        lambda request: InsuranceResult(
            wa_count="12",
            wa_price="75,71",
            wa_plus_count="15",
            wa_plus_price="80,36",
            all_risk_count="15",
            all_risk_price="110,45",
        ),
    )
    monkeypatch.setattr(
        cli_module,
        "get_wegenbelastingen",
        lambda kenteken, timeframe=None: "62",
    )


class TestComputeCosts:
    def test_normalizes_kenteken_and_combines_costs(self, profile):
        row = cli_module.compute_costs("zt026p", profile, "wa_plus")

        assert row.kenteken == "ZT-026-P"
        assert row.coverage == "wa_plus"
        assert row.insurance_monthly == 80.36
        assert row.road_tax_monthly == 62.0
        assert row.total_monthly == pytest.approx(142.36)

    @pytest.mark.parametrize(
        "coverage, expected_price",
        [("wa", 75.71), ("wa_plus", 80.36), ("all_risk", 110.45)],
    )
    def test_coverage_selects_the_right_price_field(
        self, profile, coverage, expected_price
    ):
        row = cli_module.compute_costs("ZT-026-P", profile, coverage)

        assert row.insurance_monthly == expected_price


class TestParseArgs:
    def test_defaults(self):
        args = cli_module.parse_args([])

        assert args.kentekens == []
        assert args.coverage == cli_module.DEFAULT_COVERAGE
        assert args.postcode is None
        assert args.export is None

    def test_multiple_kentekens_and_flags(self):
        args = cli_module.parse_args(
            [
                "ZT-026-P",
                "PJ-VP-22",
                "--coverage",
                "all_risk",
                "--dob",
                "01-01-1990",
                "--export",
                "costs.csv",
            ]
        )

        assert args.kentekens == ["ZT-026-P", "PJ-VP-22"]
        assert args.coverage == "all_risk"
        assert args.geboortedatum == "01-01-1990"
        assert args.export == "costs.csv"
