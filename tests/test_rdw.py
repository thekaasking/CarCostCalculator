import src.web.rdw as rdw_module


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_get_vehicle_returns_first_row(monkeypatch):
    monkeypatch.setattr(
        rdw_module.requests,
        "get",
        lambda url, params: FakeResponse([{"kenteken": "ZT026P", "merk": "SEAT"}]),
    )

    assert rdw_module.get_vehicle("ZT-026-P") == {"kenteken": "ZT026P", "merk": "SEAT"}


def test_get_vehicle_returns_none_when_not_found(monkeypatch):
    monkeypatch.setattr(
        rdw_module.requests, "get", lambda url, params: FakeResponse([])
    )

    assert rdw_module.get_vehicle("ZT-026-P") is None


def test_get_fuel_rows_sorted_by_volgnummer(monkeypatch):
    unordered = [
        {"brandstof_volgnummer": "2", "brandstof_omschrijving": "Elektriciteit"},
        {"brandstof_volgnummer": "1", "brandstof_omschrijving": "Benzine"},
    ]
    monkeypatch.setattr(
        rdw_module.requests, "get", lambda url, params: FakeResponse(unordered)
    )

    rows = rdw_module.get_fuel_rows("ZT-026-P")

    assert [row["brandstof_omschrijving"] for row in rows] == ["Benzine", "Elektriciteit"]


def test_compact_strips_dashes_and_spaces_and_uppercases():
    assert rdw_module._compact("zt-026-p") == "ZT026P"
    assert rdw_module._compact("ZT 026 P") == "ZT026P"


def test_get_vehicle_info_combines_vehicle_and_primary_fuel(monkeypatch):
    def fake_get(url, params):
        if url == rdw_module.VEHICLE_URL:
            return FakeResponse(
                [
                    {
                        "merk": "SEAT",
                        "handelsbenaming": "LEON ST",
                        "voertuigsoort": "Personenauto",
                        "datum_eerste_toelating": "20140508",
                        "zuinigheidsclassificatie": "A",
                        "catalogusprijs": "31591",
                    }
                ]
            )
        return FakeResponse(
            [
                {
                    "brandstof_volgnummer": "1",
                    "brandstof_omschrijving": "Benzine",
                    "brandstofverbruik_gecombineerd": "5.30",
                    "co2_uitstoot_gecombineerd": "121",
                }
            ]
        )

    monkeypatch.setattr(rdw_module.requests, "get", fake_get)

    info = rdw_module.get_vehicle_info("ZT-026-P")

    assert info.kenteken == "ZT-026-P"
    assert info.merk == "SEAT"
    assert info.model == "LEON ST"
    assert info.datum_eerste_toelating == "08-05-2014"
    assert info.brandstof == "Benzine"
    assert info.brandstofverbruik_gecombineerd == 5.3
    assert info.co2_uitstoot_gecombineerd == 121
    assert info.zuinigheidsclassificatie == "A"
    assert info.catalogusprijs == 31591


def test_get_vehicle_info_combines_multiple_fuel_rows(monkeypatch):
    def fake_get(url, params):
        if url == rdw_module.VEHICLE_URL:
            return FakeResponse([{"merk": "TOYOTA", "handelsbenaming": "PRIUS"}])
        return FakeResponse(
            [
                {"brandstof_volgnummer": "1", "brandstof_omschrijving": "Benzine"},
                {
                    "brandstof_volgnummer": "2",
                    "brandstof_omschrijving": "Elektriciteit",
                },
            ]
        )

    monkeypatch.setattr(rdw_module.requests, "get", fake_get)

    info = rdw_module.get_vehicle_info("11-AB-11")

    assert info.brandstof == "Benzine + Elektriciteit"


def test_get_vehicle_info_tolerates_missing_data(monkeypatch):
    monkeypatch.setattr(
        rdw_module.requests, "get", lambda url, params: FakeResponse([])
    )

    info = rdw_module.get_vehicle_info("ZT-026-P")

    assert info.kenteken == "ZT-026-P"
    assert info.merk is None
    assert info.brandstofverbruik_gecombineerd is None
    assert info.catalogusprijs is None
