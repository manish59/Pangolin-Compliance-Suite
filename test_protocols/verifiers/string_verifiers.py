# test_protocols/verifiers/string_verifiers.py
import re
from .base import BaseVerifier


class StringExactMatchVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Convert values to strings if they're not already
            actual_str = str(actual_value) if actual_value is not None else ""
            expected_str = str(expected_value) if expected_value is not None else ""

            success = actual_str == expected_str

            if success:
                message = f"String exact match successful"
            else:
                message = f"String does not match expected value"

            return self.format_result(
                success=success,
                message=message,
                actual_value=actual_str,
                expected_value=expected_str,
                method="string_exact_match"
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"String exact match verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="string_exact_match",
                error=str(e)
            )


class StringContainsVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Convert values to strings if they're not already
            actual_str = str(actual_value) if actual_value is not None else ""
            expected_str = str(expected_value) if expected_value is not None else ""

            success = expected_str in actual_str

            if success:
                message = f"String contains the expected substring"
            else:
                message = f"String does not contain the expected substring"

            return self.format_result(
                success=success,
                message=message,
                actual_value=actual_str,
                expected_value=expected_str,
                method="string_contains"
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"String contains verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="string_contains",
                error=str(e)
            )


class StringRegexMatchVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Convert actual value to string if it's not already
            actual_str = str(actual_value) if actual_value is not None else ""

            # expected_value should be a regex pattern
            pattern = expected_value

            try:
                match = re.search(pattern, actual_str)
                success = bool(match)
            except re.error as regex_error:
                return self.format_result(
                    success=False,
                    message=f"Invalid regex pattern: {str(regex_error)}",
                    actual_value=actual_str,
                    expected_value=pattern,
                    method="string_regex_match",
                    error=str(regex_error)
                )

            if success:
                message = f"String matches the regex pattern"
            else:
                message = f"String does not match the regex pattern"

            return self.format_result(
                success=success,
                message=message,
                actual_value=actual_str,
                expected_value=pattern,
                method="string_regex_match",
                match_groups=match.groups() if success and match.groups() else None
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"String regex match verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="string_regex_match",
                error=str(e)
            )


class StringLengthVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Convert actual value to string if it's not already
            actual_str = str(actual_value) if actual_value is not None else ""
            actual_length = len(actual_str)

            # The expected_value should be a length or a range
            if isinstance(expected_value, (int, float)):
                # Single value - exact length check
                expected_length = int(expected_value)
                comparison = comparison_method if comparison_method else 'eq'
                operator = self.get_comparison_operator(comparison)

                if not operator:
                    return self.format_result(
                        success=False,
                        message=f"Invalid comparison method: {comparison}",
                        actual_value=actual_length,
                        expected_value=expected_length,
                        method="string_length"
                    )

                success = operator(actual_length, expected_length)

                if success:
                    message = f"String length ({actual_length}) meets the {comparison} condition with expected value {expected_length}"
                else:
                    message = f"String length ({actual_length}) does not meet the {comparison} condition with expected value {expected_length}"

            elif isinstance(expected_value, dict) and 'min' in expected_value and 'max' in expected_value:
                # Range check
                min_length = expected_value.get('min')
                max_length = expected_value.get('max')

                success = min_length <= actual_length <= max_length

                if success:
                    message = f"String length ({actual_length}) is within range [{min_length}, {max_length}]"
                else:
                    message = f"String length ({actual_length}) is outside range [{min_length}, {max_length}]"
            else:
                return self.format_result(
                    success=False,
                    message=f"Invalid expected value for string length verification: {expected_value}",
                    actual_value=actual_length,
                    expected_value=expected_value,
                    method="string_length"
                )

            return self.format_result(
                success=success,
                message=message,
                actual_value=actual_length,
                expected_value=expected_value,
                method="string_length",
                string_value=actual_str
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"String length verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="string_length",
                error=str(e)
            )