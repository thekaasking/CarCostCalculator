import pytest

from src.web import wegenbelasting

FIXTURE_HTML = """
<table>
    <tr class="wb-resultaat-bedragen">
        <td>Zuid-Holland</td><td>62</td><td>188</td><td>752</td>
    </tr>
    <tr class="wb-resultaat-bedragen">
        <td>Utrecht</td><td>58</td><td>175</td><td>700</td>
    </tr>
</table>
"""


@pytest.fixture(autouse=True)
def mock_request(monkeypatch):
    """Avoid real network calls: stub out request_wegenbelasting."""
    monkeypatch.setattr(
        wegenbelasting, "request_wegenbelasting", lambda kenteken: FIXTURE_HTML
    )


class TestGetWegenbelastingen:
    def test_returns_full_dataframe_without_filters(self):
        df = wegenbelasting.get_wegenbelastingen(
            kenteken="ZT-026-P", province=None, timeframe=None
        )

        assert len(df) == 2
        assert list(df.columns) == ["Provincie", "P/m*", "P/k", "P/j"]

    def test_filters_by_province_and_default_timeframe(self):
        value = wegenbelasting.get_wegenbelastingen(
            kenteken="ZT-026-P", province="Zuid-Holland"
        )

        assert value == "188"

    @pytest.mark.parametrize(
        "timeframe, expected",
        [
            ("P/m", "62"),
            ("P/k", "188"),
            ("P/j", "752"),
            ("P/m* (Wegenbelasting)", "62"),
            ("P/k (Wegenbelasting)", "188"),
            ("P/j (Wegenbelasting)", "752"),
        ],
    )
    def test_resolves_timeframe_aliases(self, timeframe, expected):
        value = wegenbelasting.get_wegenbelastingen(
            kenteken="ZT-026-P", province="Zuid-Holland", timeframe=timeframe
        )

        assert value == expected

    def test_raises_for_unknown_province(self):
        with pytest.raises(ValueError):
            wegenbelasting.get_wegenbelastingen(
                kenteken="ZT-026-P", province="Nergensland"
            )

    def test_raises_for_invalid_timeframe(self):
        with pytest.raises(AssertionError):
            wegenbelasting.get_wegenbelastingen(
                kenteken="ZT-026-P", timeframe="not-a-real-timeframe"
            )

    def test_returns_none_when_request_fails(self, monkeypatch):
        monkeypatch.setattr(
            wegenbelasting, "request_wegenbelasting", lambda kenteken: None
        )

        result = wegenbelasting.get_wegenbelastingen(kenteken="ZT-026-P")

        assert result is None
