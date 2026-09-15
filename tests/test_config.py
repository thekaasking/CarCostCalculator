import src.config as config_module
from src.config import Profile, load_profile, prompt_profile, save_profile


def make_profile(**overrides):
    defaults = dict(
        postcode="2562 HX",
        huisnummer="414",
        toevoeging="",
        geboortedatum="25-09-2002",
        schadevrije_jaren=3,
    )
    defaults.update(overrides)
    return Profile(**defaults)


class TestProfilePersistence:
    def test_load_profile_returns_none_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_module, "CONFIG_PATH", tmp_path / "missing.toml")

        assert load_profile() is None

    def test_save_and_load_round_trip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_module, "CONFIG_PATH", tmp_path / "profile.toml")
        profile = make_profile()

        save_profile(profile)
        loaded = load_profile()

        assert loaded == profile

    def test_round_trip_preserves_int_type_for_schadevrije_jaren(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(config_module, "CONFIG_PATH", tmp_path / "profile.toml")
        save_profile(make_profile(schadevrije_jaren=5))

        loaded = load_profile()

        assert loaded.schadevrije_jaren == 5
        assert isinstance(loaded.schadevrije_jaren, int)

    def test_prompt_profile_reads_input_and_saves(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_module, "CONFIG_PATH", tmp_path / "profile.toml")
        answers = iter(["2562 HX", "414", "", "25-09-2002", "3"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

        profile = prompt_profile()

        assert profile == make_profile()
        assert load_profile() == profile
