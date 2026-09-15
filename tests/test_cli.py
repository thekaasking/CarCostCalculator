import pytest

import src.cli as cli_module
from src.config import Profile
from src.models import InsuranceResult, VehicleInfo


@pytest.fixture
def profile():
    return Profile(
        postcode="2562 HX",
        huisnummer="414",
        toevoeging="",
        geboortedatum="25-09-2002",
        schadevrije_jaren=3,
    )


def make_vehicle_info(**overrides):
    defaults = dict(
        kenteken="ZT-026-P",
        merk="SEAT",
        model="LEON ST",
        voertuigsoort="Personenauto",
        datum_eerste_toelating="08-05-2014",
        brandstof="Benzine",
        brandstofverbruik_gecombineerd=5.3,
        co2_uitstoot_gecombineerd=121,
        zuinigheidsclassificatie="A",
        catalogusprijs=31591,
    )
    defaults.update(overrides)
    return VehicleInfo(**defaults)


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
    monkeypatch.setattr(
        cli_module,
        "get_vehicle_info",
        lambda kenteken: make_vehicle_info(kenteken=kenteken),
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


class TestComputeVehicleInfo:
    def test_normalizes_kenteken_before_lookup(self):
        info = cli_module.compute_vehicle_info("zt026p")

        assert info.kenteken == "ZT-026-P"
        assert info.merk == "SEAT"


class TestLookup:
    def test_returns_cost_and_vehicle_info_for_the_same_plate(self, profile):
        cost, vehicle = cli_module.lookup("zt026p", profile, "wa_plus")

        assert cost.kenteken == "ZT-026-P"
        assert vehicle.kenteken == "ZT-026-P"
        assert vehicle.merk == "SEAT"


class TestTryLookup:
    def test_returns_result_for_a_valid_plate(self, profile):
        result = cli_module._try_lookup("zt026p", profile, "wa_plus")

        assert result is not None
        cost, vehicle = result
        assert cost.kenteken == "ZT-026-P"

    def test_returns_none_and_prints_error_for_an_invalid_plate(self, profile):
        result = cli_module._try_lookup("not-a-plate", profile, "wa_plus")

        assert result is None

    def test_one_bad_plate_does_not_stop_the_rest_from_resolving(self, profile):
        # Regression test: a stray/invalid token among several plates used to
        # crash the whole compare-mode run instead of just being skipped.
        results = [
            cli_module._try_lookup(raw, profile, "wa_plus")
            for raw in ["kentekens", "ZT-026-P"]
        ]

        assert results[0] is None
        assert results[1] is not None
        assert results[1][0].kenteken == "ZT-026-P"


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
