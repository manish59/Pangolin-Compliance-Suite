# test_protocols/verifiers/base.py

class BaseVerifier:
    """Base class for all verification methods"""

    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        """
        Verify the actual value against expected value.

        Args:
            actual_value: The value to verify
            expected_value: The expected value to verify against
            comparison_method: The comparison method to use (if applicable)
            config: Additional configuration parameters

        Returns:
            dict: Verification result containing success flag, message, etc.
        """
        raise NotImplementedError("Subclasses must implement verify method")

    def get_comparison_operator(self, comparison_method):
        """Convert comparison method string to function"""
        if not comparison_method:
            return None

        # Map of comparison operators to functions
        operators = {
            'eq': lambda a, b: a == b,
            'neq': lambda a, b: a != b,
            'gt': lambda a, b: a > b,
            'gte': lambda a, b: a >= b,
            'lt': lambda a, b: a < b,
            'lte': lambda a, b: a <= b,
            'contains': lambda a, b: b in a,
            'not_contains': lambda a, b: b not in a,
            'starts_with': lambda a, b: a.startswith(b) if hasattr(a, 'startswith') else False,
            'ends_with': lambda a, b: a.endswith(b) if hasattr(a, 'endswith') else False,
            'matches': self._regex_match,
            'in': lambda a, b: a in b,
            'not_in': lambda a, b: a not in b,
        }

        return operators.get(comparison_method)

    def _regex_match(self, value, pattern):
        """Helper for regex matching"""
        import re
        try:
            return bool(re.match(pattern, value))
        except Exception as e:
            return False

    def format_result(self, success, message, actual_value, expected_value, method, **kwargs):
        """Format the verification result"""
        result = {
            'success': success,
            'message': message,
            'actual_value': actual_value,
            'expected_value': expected_value,
            'method': method
        }
        # Add any additional data
        result.update(kwargs)
        return result