"""Tests for synthetic scenario generation and simulation dataset."""

from pathlib import Path

import pytest
from aegis_sim.build_eval_set import build_and_save, generate_eval_cases
from aegis_sim.generate_sims import generate_dataset
from aegis_sim.run_adversarial_test import generate_markdown_report, run_benchmark
from aegis_sim.scenarios import (
    create_clean_coffee_scenario,
    create_smurfing_scenario,
    create_tor_travel_scenario,
)


def test_scenario_creators() -> None:
    """Verify demo button scenarios create valid Transaction models."""
    coffee = create_clean_coffee_scenario()
    assert coffee.amount == 4.50
    assert coffee.user_id in ("USR_MARCUS712", "USR_4401")

    smurf = create_smurfing_scenario()
    assert smurf.amount == 9800.00
    assert smurf.user_id in ("USR_SARAH840", "USR_4403")

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


def test_build_eval_set(tmp_path: Path) -> None:
    """Verify build_eval_set produces balanced seeded dataset and valid sha256."""
    eval_file = tmp_path / "eval_test.json"
    sha = build_and_save(eval_file, count=40, seed=99)

    assert eval_file.exists()
    assert len(sha) == 64
    cases = generate_eval_cases(count=40, seed=99)
    assert len(cases) == 40
    # 75% benign, 25% fraud
    benign = [c for c in cases if not c["is_fraud"]]
    fraud = [c for c in cases if c["is_fraud"]]
    assert len(benign) == 30
    assert len(fraud) == 10


@pytest.mark.asyncio
async def test_run_benchmark_small_sample() -> None:
    """Verify red-team benchmark runner evaluates cases and generates report."""
    cases = generate_eval_cases(count=10, seed=42)
    report = await run_benchmark(cases, concurrency=4)

    assert report["total_cases"] == 10
    assert "confusion_matrix" in report
    assert "metrics" in report
    md = generate_markdown_report(report)
    assert "# Aegis Red-Team Evaluation Report" in md
    assert "Confusion Matrix" in md
