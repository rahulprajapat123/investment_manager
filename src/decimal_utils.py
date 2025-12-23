"""
Decimal precision utilities for monetary calculations.
All money values use Decimal type to avoid floating point errors.
"""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union


# Quantizer for 2 decimal places
TWO_PLACES = Decimal("0.01")


def to_decimal(value: Union[str, int, float, Decimal, None]) -> Decimal:
    """
    Convert a value to Decimal safely.
    
    Args:
        value: Value to convert (can be string, int, float, Decimal, or None)
    
    Returns:
        Decimal value
    
    Raises:
        ValueError: If value cannot be converted to Decimal
    """
    if value is None or value == "":
        return Decimal("0")
    
    if isinstance(value, Decimal):
        return value
    
    try:
        # Convert to string first to avoid float precision issues
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Cannot convert {value} to Decimal: {e}")


def round_decimal(value: Decimal, places: int = 2) -> Decimal:
    """
    Round a Decimal to specified decimal places using ROUND_HALF_UP.
    
    Args:
        value: Decimal value to round
        places: Number of decimal places (default: 2)
    
    Returns:
        Rounded Decimal
    """
    if places == 2:
        return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
    
    quantizer = Decimal(10) ** -places
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)


def multiply_decimal(value: Decimal, multiplier: Decimal) -> Decimal:
    """
    Multiply two Decimal values and round to 2 places.
    
    Args:
        value: First Decimal
        multiplier: Second Decimal
    
    Returns:
        Rounded product
    """
    result = value * multiplier
    return round_decimal(result)


def divide_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    """
    Divide two Decimal values and round to 2 places.
    
    Args:
        numerator: Numerator
        denominator: Denominator
    
    Returns:
        Rounded quotient
    
    Raises:
        ZeroDivisionError: If denominator is zero
    """
    if denominator == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    
    result = numerator / denominator
    return round_decimal(result)


def sum_decimals(*values: Decimal) -> Decimal:
    """
    Sum multiple Decimal values.
    
    Args:
        *values: Variable number of Decimal values
    
    Returns:
        Sum of all values
    """
    return sum(values, Decimal("0"))


def subtract_decimal(value1: Decimal, value2: Decimal) -> Decimal:
    """
    Subtract two Decimal values.
    
    Args:
        value1: First Decimal (minuend)
        value2: Second Decimal (subtrahend)
    
    Returns:
        Difference (value1 - value2)
    """
    return value1 - value2


def weighted_average(values: list[Decimal], weights: list[Decimal]) -> Decimal:
    """
    Calculate weighted average of values.
    
    Args:
        values: List of values
        weights: List of weights (must be same length as values)
    
    Returns:
        Weighted average rounded to 2 decimal places
    
    Raises:
        ValueError: If lists have different lengths or weights sum to zero
    """
    if len(values) != len(weights):
        raise ValueError("Values and weights must have same length")
    
    if not values:
        return Decimal("0")
    
    total_weight = sum_decimals(*weights)
    if total_weight == 0:
        raise ValueError("Total weight cannot be zero")
    
    weighted_sum = sum_decimals(*[v * w for v, w in zip(values, weights)])
    return divide_decimal(weighted_sum, total_weight)


def to_minor_units(value: Decimal, scale: int = 100) -> int:
    """
    Convert Decimal to integer minor units (e.g., paise, cents).
    
    Args:
        value: Decimal value
        scale: Scaling factor (100 for cents/paise, 1000 for mils)
    
    Returns:
        Integer in minor units
    """
    return int(value * scale)


def from_minor_units(value: int, scale: int = 100) -> Decimal:
    """
    Convert integer minor units back to Decimal.
    
    Args:
        value: Integer in minor units
        scale: Scaling factor (100 for cents/paise, 1000 for mils)
    
    Returns:
        Decimal value rounded to 2 places
    """
    result = Decimal(value) / Decimal(scale)
    return round_decimal(result)
