from pathlib import Path

from h3c.control.validation import VALIDATION_STAGES


def test_runtime_constraint_inventory_matches_the_single_admission_owner(
    repository_root: Path,
) -> None:
    assert VALIDATION_STAGES == (
        "program_validation",
        "causal_admissibility",
        "consistent_program_direction_proof",
        "energy_budget_validation",
    )
    validation = (repository_root / "src/h3c/control/validation.py").read_text(encoding="utf-8")
    assurance = (repository_root / "src/h3c/assurance/action.py").read_text(encoding="utf-8")
    assert "reward" not in validation.lower()
    assert "reward" not in assurance.lower()


def test_terminal_reward_criteria_are_not_imported_by_runtime_control(
    repository_root: Path,
) -> None:
    forbidden_roots = (
        repository_root / "src/h3c/control",
        repository_root / "src/h3c/assurance",
        repository_root / "src/h3c/causal",
        repository_root / "src/h3c/runtime",
    )
    needle = "reward_pmv_release_criteria"
    owners = []
    for root in forbidden_roots:
        for path in root.rglob("*.py"):
            if needle in path.read_text(encoding="utf-8"):
                owners.append(path.relative_to(repository_root).as_posix())
    assert owners == []
