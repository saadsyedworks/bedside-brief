"""Deterministic pre/post-test probability helpers. Pure functions, no I/O."""
from __future__ import annotations


def _check_prob(name: str, p: float) -> None:
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"{name} must be in [0, 1], got {p}")


def post_test(pre_prob: float, lr: float) -> float:
    """Post-test probability from a pre-test probability and a likelihood ratio."""
    _check_prob("pre_prob", pre_prob)
    if lr < 0:
        raise ValueError(f"lr must be >= 0, got {lr}")
    if pre_prob == 0.0:
        return 0.0
    if pre_prob == 1.0:
        return 1.0
    post_odds = pre_prob / (1.0 - pre_prob) * lr
    return post_odds / (1.0 + post_odds)


def sens_spec_to_lr(sens: float, spec: float) -> tuple[float, float]:
    """(LR+, LR-) from sensitivity and specificity; infinite where the denominator is zero."""
    _check_prob("sens", sens)
    _check_prob("spec", spec)
    lr_pos = sens / (1.0 - spec) if spec < 1.0 else float("inf")
    lr_neg = (1.0 - sens) / spec if spec > 0.0 else float("inf")
    return lr_pos, lr_neg
