"""Tests for deterministic Decimal financial primitives."""

from __future__ import annotations

import random
from decimal import ROUND_HALF_UP, Decimal

import pytest
from pydantic import BaseModel, ValidationError

from app.core.money import (
    CENT,
    FinancialDecimal,
    FinancialDecimalError,
    allocate_money,
    decimal_to_json,
    parse_decimal,
    quantize_decimal,
)


class FinancialPayload(BaseModel):
    amount: FinancialDecimal


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (Decimal("12.3400"), Decimal("12.3400")),
        (" 12.3400 ", Decimal("12.3400")),
        (12, Decimal("12")),
        ("-0.01", Decimal("-0.01")),
    ],
)
def test_parse_decimal_accepts_only_exact_finite_inputs(raw: object, expected: Decimal) -> None:
    assert parse_decimal(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [1.1, True, False, "", "not-a-number", "NaN", "Infinity", Decimal("-Infinity"), None],
)
def test_parse_decimal_rejects_unsafe_inputs(raw: object) -> None:
    with pytest.raises(FinancialDecimalError):
        parse_decimal(raw)


def test_quantize_decimal_uses_half_even_and_supports_explicit_policy() -> None:
    assert quantize_decimal("1.005") == Decimal("1.00")
    assert quantize_decimal("1.015") == Decimal("1.02")
    assert quantize_decimal("1.005", rounding=ROUND_HALF_UP) == Decimal("1.01")
    assert quantize_decimal("1234", quantum="1") == Decimal("1234")
    assert quantize_decimal("0.00015", quantum="0.0001") == Decimal("0.0002")


def test_quantize_decimal_handles_values_larger_than_default_decimal_context() -> None:
    value = "123456789012345678901234567890123456789.995"
    assert quantize_decimal(value) == Decimal("123456789012345678901234567890123456790.00")


@pytest.mark.parametrize("quantum", ["0", "-0.01", "0.05", "NaN"])
def test_quantize_decimal_rejects_invalid_quantum(quantum: str) -> None:
    with pytest.raises(FinancialDecimalError):
        quantize_decimal("1", quantum=quantum)


def test_decimal_json_convention_is_lossless_fixed_point_string() -> None:
    assert decimal_to_json(Decimal("1E+6")) == "1000000"
    assert decimal_to_json(Decimal("12.3400")) == "12.3400"
    assert decimal_to_json(Decimal("-0.00")) == "0.00"

    payload = FinancialPayload(amount="12.3400")
    assert payload.amount == Decimal("12.3400")
    assert payload.model_dump() == {"amount": Decimal("12.3400")}
    assert payload.model_dump(mode="json") == {"amount": "12.3400"}
    assert payload.model_dump_json() == '{"amount":"12.3400"}'


@pytest.mark.parametrize("raw", [1.1, "NaN", "Infinity"])
def test_financial_decimal_pydantic_type_rejects_unsafe_values(raw: object) -> None:
    with pytest.raises(ValidationError):
        FinancialPayload(amount=raw)  # type: ignore[arg-type]


def test_allocate_money_uses_stable_input_order_for_equal_remainders() -> None:
    assert allocate_money("1.00", [1, 1, 1]) == [
        Decimal("0.34"),
        Decimal("0.33"),
        Decimal("0.33"),
    ]
    assert allocate_money("0.02", [1, 1, 1]) == [
        Decimal("0.01"),
        Decimal("0.01"),
        Decimal("0.00"),
    ]


def test_allocate_money_supports_zero_weights_negative_totals_and_custom_scale() -> None:
    assert allocate_money("-10.005", [0, 1, 3]) == [
        Decimal("0.00"),
        Decimal("-2.50"),
        Decimal("-7.50"),
    ]
    assert allocate_money("1.000", [1, 1, 1], quantum="0.001") == [
        Decimal("0.334"),
        Decimal("0.333"),
        Decimal("0.333"),
    ]


def test_allocate_money_is_exact_beyond_the_default_decimal_context() -> None:
    assert allocate_money("123456789012345678901234567890.01", [1, 1]) == [
        Decimal("61728394506172839450617283945.01"),
        Decimal("61728394506172839450617283945.00"),
    ]


@pytest.mark.parametrize(
    "weights",
    [[], [0, 0], [1, -1], [Decimal("NaN"), 1], [1.0, 2]],
)
def test_allocate_money_rejects_invalid_weight_sets(weights: list[object]) -> None:
    with pytest.raises(FinancialDecimalError):
        allocate_money("10", weights)


def test_allocation_properties_hold_over_many_seeded_examples() -> None:
    """Property-style coverage without adding Hypothesis as a dependency."""

    randomizer = random.Random(1829)
    for _ in range(500):
        recipient_count = randomizer.randint(1, 12)
        weights = [Decimal(randomizer.randint(0, 10_000)) for _ in range(recipient_count)]
        if not any(weights):
            weights[0] = Decimal(1)
        total = Decimal(randomizer.randint(-10_000_000, 10_000_000)).scaleb(-3)

        first = allocate_money(total, weights)
        second = allocate_money(total, weights)

        assert first == second
        assert sum(first, start=Decimal(0)) == quantize_decimal(total)
        assert all(value.as_tuple().exponent == CENT.as_tuple().exponent for value in first)

        # Largest-remainder allocation is always within one quantum of each
        # unrounded proportional share of the already-rounded total.
        rounded_total = quantize_decimal(total)
        weight_sum = sum(weights, start=Decimal(0))
        for allocation, weight in zip(first, weights, strict=True):
            exact_share = rounded_total * weight / weight_sum
            assert abs(allocation - exact_share) < CENT
