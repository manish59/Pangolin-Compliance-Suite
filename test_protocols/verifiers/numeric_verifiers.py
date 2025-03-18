# test_protocols/verifiers/numeric_verifiers.py
from .base import BaseVerifier


class NumericEqualVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Convert values to numeric if they're not already
            try:
                actual_num = float(actual_value)
                expected_num = float(expected_value)
            except (ValueError, TypeError):
                return self.format_result(
                    success=False,
                    message="One or both values could not be converted to a number",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="numeric_equal"
                )

            # If both are integers, compare as integers
            if isinstance(actual_value, int) and isinstance(expected_value, int):
                actual_num = int(actual_num)
                expected_num = int(expected_num)

            # Use comparison method if provided, otherwise default to equality
            comparison = comparison_method if comparison_method else 'eq'
            operator = self.get_comparison_operator(comparison)

            if not operator:
                return self.format_result(
                    success=False,
                    message=f"Invalid comparison method: {comparison}",
                    actual_value=actual_num,
                    expected_value=expected_num,
                    method="numeric_equal"
                )

            success = operator(actual_num, expected_num)

            if success:
                message = f"Numeric comparison ({comparison}) successful: {actual_num} {comparison} {expected_num}"
            else:
                message = f"Numeric comparison ({comparison}) failed: {actual_num} {comparison} {expected_num}"

            return self.format_result(
                success=success,
                message=message,
                actual_value=actual_num,
                expected_value=expected_num,
                method="numeric_equal",
                comparison=comparison
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"Numeric comparison verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="numeric_equal",
                error=str(e)
            )


class NumericRangeVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Convert actual value to numeric
            try:
                actual_num = float(actual_value)
            except (ValueError, TypeError):
                return self.format_result(
                    success=False,
                    message="Actual value could not be converted to a number",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="numeric_range"
                )

            # Expected value should be a dict with min and max keys
            if not isinstance(expected_value, dict) or 'min' not in expected_value or 'max' not in expected_value:
                return self.format_result(
                    success=False,
                    message="Expected value must be a dict with 'min' and 'max' keys",
                    actual_value=actual_num,
                    expected_value=expected_value,
                    method="numeric_range"
                )

            try:
                min_value = float(expected_value['min'])
                max_value = float(expected_value['max'])
            except (ValueError, TypeError):
                return self.format_result(
                    success=False,
                    message="Min or max values could not be converted to numbers",
                    actual_value=actual_num,
                    expected_value=expected_value,
                    method="numeric_range"
                )

            # Check if value is in range (inclusive)
            success = min_value <= actual_num <= max_value

            if success:
                message = f"Value {actual_num} is in range [{min_value}, {max_value}]"
            else:
                message = f"Value {actual_num} is outside range [{min_value}, {max_value}]"

            return self.format_result(
                success=success,
                message=message,
                actual_value=actual_num,
                expected_value=expected_value,
                method="numeric_range"
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"Numeric range verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="numeric_range",
                error=str(e)
            )


class NumericThresholdVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Convert actual value to numeric
            try:
                actual_num = float(actual_value)
            except (ValueError, TypeError):
                return self.format_result(
                    success=False,
                    message="Actual value could not be converted to a number",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="numeric_threshold"
                )

            # Expected value is the threshold
            try:
                threshold = float(expected_value)
            except (ValueError, TypeError):
                return self.format_result(
                    success=False,
                    message="Threshold value could not be converted to a number",
                    actual_value=actual_num,
                    expected_value=expected_value,
                    method="numeric_threshold"
                )

            # Use comparison method to determine which threshold check to apply
            comparison = comparison_method if comparison_method else 'lte'  # Default to less than or equal
            operator = self.get_comparison_operator(comparison)

            if not operator:
                return self.format_result(
                    success=False,
                    message=f"Invalid comparison method: {comparison}",
                    actual_value=actual_num,
                    expected_value=threshold,
                    method="numeric_threshold"
                )

            success = operator(actual_num, threshold)

            if success:
                message = f"Value {actual_num} meets the threshold condition ({comparison} {threshold})"
            else:
                message = f"Value {actual_num} does not meet the threshold condition ({comparison} {threshold})"

            return self.format_result(
                success=success,
                message=message,
                actual_value=actual_num,
                expected_value=threshold,
                method="numeric_threshold",
                comparison=comparison
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"Numeric threshold verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="numeric_threshold",
                error=str(e)
            )