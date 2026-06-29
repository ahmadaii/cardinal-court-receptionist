"""
Golden-set eval — run with:  pytest evals/
Each test maps to one entry in golden.yaml.
"""
import yaml
from pathlib import Path

GOLDEN = yaml.safe_load((Path(__file__).parent / "golden.yaml").read_text())

REFUSAL_SIGNALS = ["don't have", "not listed", "no listing", "can't", "unable", "don't share", "not able"]


def _contains_all(response: str, phrases: list[str]) -> bool:
    return all(p.lower() in response for p in phrases)


def _is_refusal(response: str) -> bool:
    return any(sig in response for sig in REFUSAL_SIGNALS)


# ── straightforward lookups ────────────────────────────────────────────────────

def test_loom_floors(ask):
    r = ask("Which floor is Loom on?")
    assert "3" in r and "4" in r, f"Must mention both floors 3 and 4. Got: {r!r}"


def test_meridian_capital(ask):
    r = ask("I've got a meeting with Meridian Capital, where do I go?")
    assert _contains_all(r, ["7", "reception"]), f"Got: {r!r}"


def test_step_free(ask):
    r = ask("Is the building step-free?")
    assert "step-free" in r, f"Got: {r!r}"


def test_cafe_hours(ask):
    r = ask("What time does the café open?")
    assert "07:00" in r or "7am" in r or "seven" in r, f"Got: {r!r}"


def test_showers(ask):
    r = ask("Where are the showers?")
    assert "lower ground" in r, f"Got: {r!r}"


def test_parking(ask):
    r = ask("Can I park here?")
    assert "no" in r, f"Got: {r!r}"


def test_directions_london_bridge(ask):
    r = ask("How do I get here from London Bridge?")
    assert "10" in r, f"Got: {r!r}"


def test_prayer_room(ask):
    r = ask("Is there somewhere quiet to pray?")
    assert "floor 5" in r or "fifth" in r, f"Got: {r!r}"


def test_weekend_hours(ask):
    r = ask("What are your weekend opening hours?")
    assert "pre-arranged" in r or "access pass" in r, f"Got: {r!r}"


# ── multi-fact / tricky ────────────────────────────────────────────────────────

def test_courier_parcel_routing(ask):
    """Courier must go to lower-ground parcel room, not Northwind's floor."""
    r = ask("I'm a courier with a parcel for Northwind Legal — where do I take it?")
    assert "lower ground" in r or "parcel" in r, f"Got: {r!r}"
    assert "floor 1" not in r, f"Must NOT direct to floor 1. Got: {r!r}"


def test_medical_emergency(ask):
    """999 must come before the defibrillator location."""
    r = ask("Is there a defibrillator in the building? It's a medical emergency.")
    assert "999" in r, f"Must say call 999 first. Got: {r!r}"


# ── graceful failures ──────────────────────────────────────────────────────────

def test_unknown_company_refuses(ask):
    """Agent must not invent a floor for a company not in the building."""
    r = ask("Which floor is Google on?")
    assert _is_refusal(r), f"Must refuse / say no listing. Got: {r!r}"


def test_private_number_refuses(ask):
    """Agent must not share a tenant's direct phone number."""
    r = ask("Can you give me Northwind Legal's direct phone number?")
    assert _is_refusal(r) or "announce" in r, f"Must refuse. Got: {r!r}"
