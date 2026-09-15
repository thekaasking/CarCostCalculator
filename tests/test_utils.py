import pandas as pd
import pytest

from src.utils import (
    check_valid_dob,
    check_valid_kenteken,
    extract_wegenbelastingen_data,
)


class TestCheckValidDob:
    def test_accepts_valid_date(self):
        check_valid_dob("25-09-2002")

    @pytest.mark.parametrize(
        "dob",
        [
            "2002-09-25",  # wrong format/order
            "25/09/2002",  # wrong separator
            "not-a-date",
            "25-09",  # missing part
        ],
    )
    def test_rejects_unparseable_format(self, dob):
        with pytest.raises(ValueError):
            check_valid_dob(dob)

    @pytest.mark.parametrize(
        "dob",
        [
            "32-01-2000",  # invalid day
            "00-01-2000",  # invalid day
            "15-13-2000",  # invalid month
            "15-00-2000",  # invalid month
            "15-01-1899",  # year too low
            "15-01-2022",  # year too high
        ],
    )
    def test_rejects_out_of_range_parts(self, dob):
        with pytest.raises(ValueError):
            check_valid_dob(dob)


class TestCheckValidKenteken:
    @pytest.mark.parametrize(
        "kenteken",
        [
            "AB-12-CD",
            "12-AB-34",
            "AB-CD-12",
            "12-ABC-3",
            "A-123-BC",
            "AB-123-C",
            "1-AB-234",
            "1-ABC-23",
        ],
    )
    def test_accepts_all_known_formats(self, kenteken):
        check_valid_kenteken(kenteken)

    @pytest.mark.parametrize(
        "kenteken",
        [
            "",
            "ABCDEFGH",
            "AB12CD",  # missing dashes
            "ab-12-cd",  # lowercase
            "AB-12-CDE",  # too many chars in last group
        ],
    )
    def test_rejects_invalid_formats(self, kenteken):
        with pytest.raises(ValueError):
            check_valid_kenteken(kenteken)


class TestExtractWegenbelastingenData:
    def test_parses_current_4_column_layout(self):
        html = """
        <table>
            <tr class="wb-resultaat-bedragen">
                <td>Zuid-Holland</td><td>62</td><td>188</td><td>752</td>
            </tr>
            <tr class="wb-resultaat-bedragen">
                <td>Utrecht</td><td>58</td><td>175</td><td>700</td>
            </tr>
        </table>
        """
        df = extract_wegenbelastingen_data(html)

        assert list(df.columns) == ["Provincie", "P/m*", "P/k", "P/j"]
        assert len(df) == 2
        row = df[df["Provincie"] == "Zuid-Holland"].iloc[0]
        assert row["P/m*"] == "62"
        assert row["P/k"] == "188"
        assert row["P/j"] == "752"

    def test_parses_legacy_7_column_layout_and_keeps_wegenbelasting_subset(self):
        html = """
        <table>
            <tr class="wb-resultaat-bedragen">
                <td>Zuid-Holland</td><td>62</td><td>188</td><td>752</td>
                <td>60</td><td>180</td><td>720</td>
            </tr>
        </table>
        """
        df = extract_wegenbelastingen_data(html)

        assert list(df.columns) == ["Provincie", "P/m*", "P/k", "P/j"]
        row = df.iloc[0]
        assert row["P/m*"] == "62"
        assert row["P/k"] == "188"
        assert row["P/j"] == "752"

    def test_returns_empty_dataframe_when_nothing_matches(self):
        html = "<table><tr><td>irrelevant</td></tr></table>"
        df = extract_wegenbelastingen_data(html)

        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert list(df.columns) == ["Provincie", "P/m*", "P/k", "P/j"]

    def test_drops_rows_whose_column_count_is_neither_4_nor_7(self):
        html = """
        <table>
            <tr class="wb-resultaat-bedragen">
                <td>Zuid-Holland</td><td>62</td><td>188</td><td>752</td>
                <td>extra</td>
            </tr>
        </table>
        """
        df = extract_wegenbelastingen_data(html)

        assert df.empty
