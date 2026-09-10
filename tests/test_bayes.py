from __future__ import annotations

import math

import pytest

from bedside_brief.bayes import post_test, sens_spec_to_lr


def test_post_test_known_values():
    assert post_test(0.5, 1.0) == pytest.approx(0.5)
    assert post_test(0.2, 4.0) == pytest.approx(0.5)  # odds 0.25 * 4 = 1 -> 0.5
    assert post_test(0.1, 10.0) == pytest.approx(10 / 19)
    assert post_test(0.3, 0.1) == pytest.approx(0.3 / 0.7 * 0.1 / (1 + 0.3 / 0.7 * 0.1))
    assert post_test(0.0, 5.0) == 0.0 and post_test(1.0, 0.1) == 1.0


def test_sens_spec_to_lr_known_values():
    lr_pos, lr_neg = sens_spec_to_lr(0.9, 0.8)
    assert lr_pos == pytest.approx(4.5) and lr_neg == pytest.approx(0.125)
    lr_pos, lr_neg = sens_spec_to_lr(0.5, 1.0)
    assert math.isinf(lr_pos) and lr_neg == pytest.approx(0.5)
    assert math.isinf(sens_spec_to_lr(0.5, 0.0)[1])


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        post_test(1.2, 1.0)
    with pytest.raises(ValueError):
        post_test(0.5, -1.0)
    with pytest.raises(ValueError):
        sens_spec_to_lr(0.5, 1.5)
