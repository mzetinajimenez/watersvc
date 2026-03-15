"""Unit conversion utilities for water intake measurements."""

# Conversion factors to/from ounces (oz)
# All values represent how many oz are in 1 unit of the measurement
_OZ_PER_ML = 1 / 29.5735295625  # exact SI: 1 fl oz = 29.5735295625 ml

UNIT_CONVERSIONS = {
    "oz": 1.0,
    "ml": _OZ_PER_ML,
    "l": _OZ_PER_ML * 1000,
    "cups": 8.0,  # exact: 1 cup = 8 fl oz
}

VALID_UNITS = set(UNIT_CONVERSIONS.keys())


def convert_to_oz(amount: float, unit: str) -> float:
    """
    Convert from any unit to ounces (base unit).

    Args:
        amount: The amount to convert
        unit: The unit of the amount (oz, ml, l, cups)

    Returns:
        The amount in ounces

    Raises:
        ValueError: If the unit is not supported
    """
    if unit not in UNIT_CONVERSIONS:
        raise ValueError(f"Invalid unit: {unit}. Supported units: {', '.join(VALID_UNITS)}")
    return amount * UNIT_CONVERSIONS[unit]


def convert_from_oz(amount_oz: float, unit: str) -> float:
    """
    Convert from ounces to any unit.

    Args:
        amount_oz: The amount in ounces
        unit: The target unit (oz, ml, l, cups)

    Returns:
        The amount in the target unit

    Raises:
        ValueError: If the unit is not supported
    """
    if unit not in UNIT_CONVERSIONS:
        raise ValueError(f"Invalid unit: {unit}. Supported units: {', '.join(VALID_UNITS)}")
    return amount_oz / UNIT_CONVERSIONS[unit]


def validate_unit(unit: str) -> bool:
    """
    Validate if a unit is supported.

    Args:
        unit: The unit to validate

    Returns:
        True if the unit is valid, False otherwise
    """
    return unit in VALID_UNITS
