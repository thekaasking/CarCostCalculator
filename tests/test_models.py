import pytest

from src.models import InsuranceRequest, InsuranceResult


class TestInsuranceRequest:
    def test_constructs_with_valid_fields(self):
        request = InsuranceRequest(
            kenteken="ZT-026-P",
            postcode="2562 HX",
            huisnummer="414",
            toevoeging="",
            geboortedatum="25-09-2002",
            schadevrije_jaren=3,
        )

        assert request.kenteken == "ZT-026-P"
        assert request.schadevrije_jaren == 3

    def test_rejects_invalid_kenteken(self):
        with pytest.raises(ValueError):
            InsuranceRequest(
                kenteken="NOT-A-PLATE",
                postcode="2562 HX",
                huisnummer="414",
                toevoeging="",
                geboortedatum="25-09-2002",
                schadevrije_jaren=3,
            )

    def test_rejects_invalid_date_of_birth(self):
        with pytest.raises(ValueError):
            InsuranceRequest(
                kenteken="ZT-026-P",
                postcode="2562 HX",
                huisnummer="414",
                toevoeging="",
                geboortedatum="31-13-2000",
                schadevrije_jaren=3,
            )


class TestInsuranceResult:
    def test_holds_provided_fields(self):
        result = InsuranceResult(
            wa_count="12",
            wa_price="75,71",
            wa_plus_count="15",
            wa_plus_price="80,36",
            all_risk_count="15",
            all_risk_price="110,45",
        )

        assert result.wa_price == "75,71"
        assert result.all_risk_count == "15"
