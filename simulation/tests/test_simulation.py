"""Tests for synthetic scenario generation and simulation dataset."""

from pathlib import Path

from aegis_sim.generate_sims import generate_dataset
from aegis_sim.scenarios import (
    create_clean_coffee_scenario,
    create_smurfing_scenario,
    create_tor_travel_scenario,
)


def test_scenario_creators() -> None:
    """Verify demo button scenarios create valid Transaction models."""
    coffee = create_clean_coffee_scenario()
    assert coffee.amount == 4.50
    assert coffee.user_id == "USR_4401"

    smurf = create_smurfing_scenario()
    assert smurf.amount == 9800.00
    assert smurf.user_id == "USR_4403"

    tor = create_tor_travel_scenario()
    assert tor.amount == 12500.00
    assert str(tor.ip_address) == "185.220.101.5"


def test_generate_small_dataset(tmp_path: Path) -> None:
    """Verify generate_dataset writes valid CSV with correct headers and rows."""
    output_file = tmp_path / "test_txs.csv"
    generate_dataset(output_file, num_users=10, total_txs=50, seed=123)

    assert output_file.exists()
    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 51  # Header + 50 rows
    assert "tx_id,user_id,ts,amount" in lines[0]
