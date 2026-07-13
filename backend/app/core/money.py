"""Decimal-safe primitives for financial values.

Financial values cross API, database, import, and accounting boundaries.  This
module centralizes the rules that must remain identical at each boundary:

* never construct a financial Decimal from a binary float;
* reject NaN and infinities;
* make rounding mode and precision explicit;
* serialize Decimals as fixed-point JSON strings; and
* allocate rounded units with a deterministic largest-remainder rule.

Existing schemas are intentionally not migrated here.  New financial schemas
can use :data:`FinancialDecimal`, while existing code can adopt the functions
incrementally.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation, localcontext
from fractions import Fraction
from typing import Annotated, Final, cast

from pydantic import BeforeValidator, PlainSerializer

CENT: Final = Decimal("0.01")
"""The default storage and calculation quantum for USD amounts."""


class FinancialDecimalError(ValueError):
    """Raised when a value cannot safely participate in financial arithmetic."""


def parse_decimal(value: object) -> Decimal:
    """Convert an exact input into a finite :class:`~decimal.Decimal`.

    Strings, integers, and existing Decimals are accepted.  Floats are rejected
    even when they appear exact because accepting them makes it easy for a
    binary approximation to leak into accounting calculations.  Callers must
    explicitly convert external floats to their source string first.
    """

    if isinstance(value, bool | float):
        raise FinancialDecimalError("financial decimals must not be created from floats")

    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise FinancialDecimalError("financial decimal cannot be empty")
        try:
            result = Decimal(stripped)
        except InvalidOperation as exc:
            raise FinancialDecimalError(f"invalid financial decimal: {value!r}") from exc
    else:
        raise FinancialDecimalError(
            "financial decimal must be supplied as a Decimal, integer, or string"
        )

    if not result.is_finite():
        raise FinancialDecimalError("financial decimal must be finite")
    return result


def decimal_to_json(value: Decimal) -> str:
    """Return a JSON-safe fixed-point string without scientific notation.

    JSON numbers are commonly decoded as binary floats.  A string therefore
    forms the lossless API contract for financial values.  Significant trailing
    zeroes are retained, and negative zero is canonicalized to positive zero.
    """

    parsed = parse_decimal(value)
    if parsed.is_zero():
        parsed = parsed.copy_abs()
    return format(parsed, "f")


FinancialDecimal = Annotated[
    Decimal,
    BeforeValidator(parse_decimal),
    PlainSerializer(decimal_to_json, return_type=str, when_used="json"),
]
"""Pydantic financial value: Decimal in Python and fixed-point string in JSON."""


def quantize_decimal(
    value: object,
    *,
    quantum: object = CENT,
    rounding: str = ROUND_HALF_EVEN,
) -> Decimal:
    """Round ``value`` to a power-of-ten quantum using an explicit mode.

    ``ROUND_HALF_EVEN`` is the default because it avoids systematically biasing
    repeated calculations.  Use another :mod:`decimal` rounding constant only
    when a governing document or external accounting contract requires it.
    """

    amount = parse_decimal(value)
    unit = _parse_quantum(quantum)
    precision = max(28, _required_precision(amount, unit))
    try:
        with localcontext() as context:
            context.prec = precision
            result = amount.quantize(unit, rounding=rounding)
    except (InvalidOperation, ValueError) as exc:
        raise FinancialDecimalError("unable to quantize financial decimal") from exc

    return result.copy_abs() if result.is_zero() else result


def allocate_money(
    total: object,
    weights: list[object] | tuple[object, ...],
    *,
    quantum: object = CENT,
    rounding: str = ROUND_HALF_EVEN,
) -> list[Decimal]:
    """Allocate a rounded total proportionally with deterministic remainders.

    The total is rounded once to ``quantum``.  Each recipient first receives its
    whole-unit floor; leftover units go to the largest fractional remainders.
    Ties are resolved by original input order, making retries and audit replay
    stable.  Negative totals use the same allocation over their magnitude and
    then negate every result.
    """

    if not weights:
        raise FinancialDecimalError("at least one allocation weight is required")

    parsed_weights = [parse_decimal(weight) for weight in weights]
    if any(weight < 0 for weight in parsed_weights):
        raise FinancialDecimalError("allocation weights cannot be negative")

    fractional_weights = [Fraction(weight) for weight in parsed_weights]
    weight_sum = sum(fractional_weights, start=Fraction(0))
    if weight_sum == 0:
        raise FinancialDecimalError("allocation weights must have a positive sum")

    unit = _parse_quantum(quantum)
    rounded_total = quantize_decimal(total, quantum=unit, rounding=rounding)
    is_negative = rounded_total < 0
    absolute_total = rounded_total.copy_abs()
    unit_count = int(Fraction(absolute_total) / Fraction(unit))

    exact_units = [
        Fraction(unit_count) * weight / weight_sum for weight in fractional_weights
    ]
    whole_units = [share.numerator // share.denominator for share in exact_units]
    units_left = unit_count - sum(whole_units)

    ranking = sorted(
        range(len(parsed_weights)),
        key=lambda index: (-(exact_units[index] - whole_units[index]), index),
    )
    for index in ranking[:units_left]:
        whole_units[index] += 1

    sign = Decimal(-1) if is_negative else Decimal(1)
    largest_unit_count = max(whole_units)
    unit_exponent = cast(int, unit.as_tuple().exponent)
    precision = max(28, len(str(largest_unit_count)) + abs(unit_exponent) + 2)
    with localcontext() as context:
        context.prec = precision
        allocations = [sign * units * unit for units in whole_units]
    return [
        allocation.copy_abs() if allocation.is_zero() else allocation
        for allocation in allocations
    ]


def _parse_quantum(value: object) -> Decimal:
    quantum = parse_decimal(value)
    normalized = quantum.normalize()
    if quantum <= 0 or normalized.as_tuple().digits != (1,):
        raise FinancialDecimalError("quantum must be a positive power of ten")
    return normalized


def _required_precision(value: Decimal, quantum: Decimal) -> int:
    value_tuple = value.as_tuple()
    value_exponent = cast(int, value_tuple.exponent)
    quantum_exponent = cast(int, quantum.as_tuple().exponent)
    integer_digits = max(len(value_tuple.digits) + value_exponent, 1)
    fractional_digits = max(-quantum_exponent, 0)
    return integer_digits + fractional_digits + 2
