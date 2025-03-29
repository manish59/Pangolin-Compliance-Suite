# test_protocols/verifiers/dict_verifiers.py
import jsonschema
from .base import BaseVerifier


class DictHasKeysVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value is a dictionary
            if not isinstance(actual_value, dict):
                return self.format_result(
                    success=False,
                    message="Actual value is not a dictionary",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="dict_has_keys",
                )

            # expected_value should be a list of keys
            if not isinstance(expected_value, list):
                expected_keys = [expected_value]  # Convert single key to list
            else:
                expected_keys = expected_value

            # Check if all expected keys are in the dictionary
            missing_keys = [key for key in expected_keys if key not in actual_value]
            success = len(missing_keys) == 0

            if success:
                message = f"Dictionary contains all expected keys: {expected_keys}"
            else:
                message = f"Dictionary is missing keys: {missing_keys}"

            return self.format_result(
                success=success,
                message=message,
                actual_value=list(actual_value.keys()),
                expected_value=expected_keys,
                method="dict_has_keys",
                missing_keys=missing_keys,
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"Dictionary keys verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="dict_has_keys",
                error=str(e),
            )


class DictSchemaVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value is a dictionary
            if not isinstance(actual_value, dict):
                return self.format_result(
                    success=False,
                    message="Actual value is not a dictionary",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="dict_schema_valid",
                )

            # expected_value should be a JSON schema
            if not isinstance(expected_value, dict):
                return self.format_result(
                    success=False,
                    message="Expected value is not a valid JSON schema (not a dictionary)",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="dict_schema_valid",
                )

            # Validate against JSON schema
            try:
                jsonschema.validate(instance=actual_value, schema=expected_value)
                success = True
                message = "Dictionary matches JSON schema"
                validation_error = None
            except jsonschema.exceptions.ValidationError as ve:
                success = False
                message = f"Dictionary does not match JSON schema: {ve.message}"
                validation_error = {
                    "message": str(ve),
                    "path": list(ve.path) if ve.path else [],
                    "schema_path": list(ve.schema_path) if ve.schema_path else [],
                }
            except jsonschema.exceptions.SchemaError as se:
                return self.format_result(
                    success=False,
                    message=f"Invalid JSON schema: {str(se)}",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="dict_schema_valid",
                    error=str(se),
                )

            return self.format_result(
                success=success,
                message=message,
                actual_value=actual_value,
                expected_value=expected_value,
                method="dict_schema_valid",
                validation_error=validation_error,
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"Dictionary schema verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="dict_schema_valid",
                error=str(e),
            )


class DictSubsetVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value is a dictionary
            if not isinstance(actual_value, dict):
                return self.format_result(
                    success=False,
                    message="Actual value is not a dictionary",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="dict_subset",
                )

            # expected_value should be a dictionary (subset)
            if not isinstance(expected_value, dict):
                return self.format_result(
                    success=False,
                    message="Expected value is not a dictionary",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="dict_subset",
                )

            # Check if actual_value contains all key-value pairs from expected_value
            missing_keys = []
            mismatched_values = []

            for key, expected_val in expected_value.items():
                if key not in actual_value:
                    missing_keys.append(key)
                elif actual_value[key] != expected_val:
                    mismatched_values.append(key)

            success = len(missing_keys) == 0 and len(mismatched_values) == 0

            if success:
                message = "Dictionary contains all expected key-value pairs"
            else:
                message = "Dictionary does not contain the expected subset"
                if missing_keys:
                    message += f". Missing keys: {missing_keys}"
                if mismatched_values:
                    message += f". Mismatched values for keys: {mismatched_values}"

            return self.format_result(
                success=success,
                message=message,
                actual_value=actual_value,
                expected_value=expected_value,
                method="dict_subset",
                missing_keys=missing_keys,
                mismatched_values=mismatched_values,
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"Dictionary subset verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="dict_subset",
                error=str(e),
            )
