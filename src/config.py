"""Personal defaults for the CLI, stored in config.toml at the project root.

These are the InsuranceRequest fields that rarely change between lookups
(address, date of birth, no-claims years) so the CLI only has to ask for the
kenteken each time. config.toml is gitignored since it holds personal
details; config.example.toml documents the expected fields.
"""

import logging
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.toml"


@dataclass
class Profile:
    postcode: str
    huisnummer: str
    toevoeging: str
    geboortedatum: str
    schadevrije_jaren: int


def load_profile() -> Profile | None:
    """Load the saved profile, or None if it hasn't been created yet."""
    if not CONFIG_PATH.exists():
        return None
    with CONFIG_PATH.open("rb") as f:
        data = tomllib.load(f)
    return Profile(**data)


def save_profile(profile: Profile) -> None:
    """Write the profile to CONFIG_PATH as flat TOML key/value pairs."""
    lines = []
    for field in fields(Profile):
        value = getattr(profile, field.name)
        rendered = str(value) if field.type is int else f'"{value}"'
        lines.append(f"{field.name} = {rendered}")
    CONFIG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logging.info(f"Saved profile to {CONFIG_PATH}")


def prompt_profile() -> Profile:
    """Interactively ask for each profile field and save the result."""
    print(f"No saved profile found. Let's set up your defaults ({CONFIG_PATH}).")
    profile = Profile(
        postcode=input("Postcode (e.g. 2562 HX): ").strip(),
        huisnummer=input("Huisnummer: ").strip(),
        toevoeging=input("Toevoeging (blank if none): ").strip(),
        geboortedatum=input("Geboortedatum (DD-MM-YYYY): ").strip(),
        schadevrije_jaren=int(input("Schadevrije jaren: ").strip()),
    )
    save_profile(profile)
    return profile


def load_or_prompt_profile() -> Profile:
    return load_profile() or prompt_profile()
