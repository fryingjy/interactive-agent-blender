import pytest

from knowledge_engine.iteration_control import evaluate_iteration_budget


def _attempt(before, after, *, region="blade", action="move_selection"):
    return {
        "stage": "PROPORTION_SILHOUETTE",
        "target_region": region,
        "action": action,
        "status": "committed",
        "before_score": before,
        "after_score": after,
    }


def test_budget_allows_one_improving_local_repair():
    result = evaluate_iteration_budget(
        [_attempt(0.50, 0.60)], stage="PROPORTION_SILHOUETTE", target_region="blade"
    )
    assert result["decision"] == "CONTINUE_BOUNDED_REPAIR"
    assert result["attempts_remaining"] == 2


def test_two_stagnant_repairs_force_strategy_change():
    result = evaluate_iteration_budget(
        [_attempt(0.50, 0.505), _attempt(0.505, 0.507)],
        stage="PROPORTION_SILHOUETTE",
        target_region="blade",
    )
    assert result["decision"] == "CHANGE_STRATEGY"
    assert result["trailing_stagnant_attempts"] == 2


def test_three_attempts_force_change_even_without_metrics():
    attempts = [
        {"stage": "PRIMARY_BLOCKOUT", "target_region": "body", "status": "failed"}
        for _ in range(3)
    ]
    result = evaluate_iteration_budget(attempts, stage="PRIMARY_BLOCKOUT", target_region="body")
    assert result["decision"] == "CHANGE_STRATEGY"


def test_unrelated_regions_and_stages_do_not_consume_budget():
    attempts = [_attempt(0.1, 0.1, region="hilt") for _ in range(3)]
    result = evaluate_iteration_budget(
        attempts, stage="PROPORTION_SILHOUETTE", target_region="blade"
    )
    assert result["attempt_count"] == 0


def test_invalid_limits_fail_closed():
    with pytest.raises(ValueError):
        evaluate_iteration_budget([], stage="PRIMARY_BLOCKOUT", target_region=None, max_attempts=0)
