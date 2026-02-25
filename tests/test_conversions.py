"""Tests for unit conversion utilities."""

import pytest

from watersvc.utils.conversions import (
    convert_from_oz,
    convert_to_oz,
    validate_unit,
)


class TestConvertToOz:
    """Tests for converting various units to ounces."""

    def test_oz_to_oz(self):
        """Test converting oz to oz (identity)."""
        assert convert_to_oz(10, "oz") == 10.0

    def test_ml_to_oz(self):
        """Test converting ml to oz."""
        result = convert_to_oz(100, "ml")
        assert pytest.approx(result, rel=0.01) == 3.3814

    def test_liters_to_oz(self):
        """Test converting liters to oz."""
        result = convert_to_oz(1, "l")
        assert pytest.approx(result, rel=0.01) == 33.814

    def test_cups_to_oz(self):
        """Test converting cups to oz."""
        assert convert_to_oz(2, "cups") == 16.0

    def test_invalid_unit_raises_error(self):
        """Test that invalid unit raises ValueError."""
        with pytest.raises(ValueError, match="Invalid unit"):
            convert_to_oz(10, "gallons")


class TestConvertFromOz:
    """Tests for converting ounces to various units."""

    def test_oz_to_oz(self):
        """Test converting oz to oz (identity)."""
        assert convert_from_oz(10, "oz") == 10.0

    def test_oz_to_ml(self):
        """Test converting oz to ml."""
        result = convert_from_oz(10, "ml")
        assert pytest.approx(result, rel=0.01) == 295.735

    def test_oz_to_liters(self):
        """Test converting oz to liters."""
        result = convert_from_oz(33.814, "l")
        assert pytest.approx(result, rel=0.01) == 1.0

    def test_oz_to_cups(self):
        """Test converting oz to cups."""
        assert convert_from_oz(16, "cups") == 2.0

    def test_invalid_unit_raises_error(self):
        """Test that invalid unit raises ValueError."""
        with pytest.raises(ValueError, match="Invalid unit"):
            convert_from_oz(10, "pints")


class TestRoundTripConversions:
    """Test round-trip conversions to ensure accuracy."""

    def test_oz_round_trip(self):
        """Test oz -> oz round trip."""
        original = 64.0
        converted = convert_from_oz(convert_to_oz(original, "oz"), "oz")
        assert pytest.approx(converted) == original

    def test_ml_round_trip(self):
        """Test ml -> oz -> ml round trip."""
        original = 500.0
        converted = convert_from_oz(convert_to_oz(original, "ml"), "ml")
        assert pytest.approx(converted) == original

    def test_liters_round_trip(self):
        """Test L -> oz -> L round trip."""
        original = 2.0
        converted = convert_from_oz(convert_to_oz(original, "l"), "l")
        assert pytest.approx(converted) == original

    def test_cups_round_trip(self):
        """Test cups -> oz -> cups round trip."""
        original = 8.0
        converted = convert_from_oz(convert_to_oz(original, "cups"), "cups")
        assert pytest.approx(converted) == original


class TestValidateUnit:
    """Tests for unit validation."""

    def test_valid_units(self):
        """Test that all supported units are valid."""
        assert validate_unit("oz") is True
        assert validate_unit("ml") is True
        assert validate_unit("l") is True
        assert validate_unit("cups") is True

    def test_invalid_units(self):
        """Test that unsupported units are invalid."""
        assert validate_unit("gallons") is False
        assert validate_unit("pints") is False
        assert validate_unit("") is False
        assert validate_unit("OZ") is False  # Case sensitive


class TestEdgeCases:
    """Test edge cases and special values."""

    def test_zero_conversion(self):
        """Test converting zero values."""
        assert convert_to_oz(0, "ml") == 0.0
        assert convert_from_oz(0, "cups") == 0.0

    def test_large_values(self):
        """Test converting large values."""
        result = convert_to_oz(10000, "ml")
        assert result > 0
        assert pytest.approx(result, rel=0.01) == 338.14

    def test_decimal_precision(self):
        """Test decimal precision in conversions."""
        result = convert_to_oz(250.5, "ml")
        assert isinstance(result, float)
        assert result > 0
