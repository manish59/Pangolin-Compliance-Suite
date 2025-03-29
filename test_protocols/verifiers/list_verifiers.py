# test_protocols/verifiers/list_verifiers.py
from .base import BaseVerifier


class ListLengthVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value is iterable
            try:
                actual_length = len(actual_value)
            except (TypeError, AttributeError):
                return self.format_result(
                    success=False,
                    message="Actual value is not a list or doesn't support length calculation",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="list_length",
                )

            # Expected value can be a single length value or a range dict
            if isinstance(expected_value, (int, float)):
                # Single value - exact length check
                expected_length = int(expected_value)
                comparison = comparison_method if comparison_method else "eq"
                operator = self.get_comparison_operator(comparison)

                if not operator:
                    return self.format_result(
                        success=False,
                        message=f"Invalid comparison method: {comparison}",
                        actual_value=actual_length,
                        expected_value=expected_length,
                        method="list_length",
                    )

                success = operator(actual_length, expected_length)

                if success:
                    message = f"List length ({actual_length}) meets the {comparison} condition with expected value {expected_length}"
                else:
                    message = f"List length ({actual_length}) does not meet the {comparison} condition with expected value {expected_length}"

            elif (
                isinstance(expected_value, dict)
                and "min" in expected_value
                and "max" in expected_value
            ):
                # Range check
                min_length = expected_value.get("min")
                max_length = expected_value.get("max")

                success = min_length <= actual_length <= max_length

                if success:
                    message = f"List length ({actual_length}) is within range [{min_length}, {max_length}]"
                else:
                    message = f"List length ({actual_length}) is outside range [{min_length}, {max_length}]"
            else:
                return self.format_result(
                    success=False,
                    message=f"Invalid expected value for list length verification: {expected_value}",
                    actual_value=actual_length,
                    expected_value=expected_value,
                    method="list_length",
                )

            return self.format_result(
                success=success,
                message=message,
                actual_value=actual_length,
                expected_value=expected_value,
                method="list_length",
                list_value=actual_value,
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"List length verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="list_length",
                error=str(e),
            )


class ListContainsVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value is iterable
            try:
                _ = iter(actual_value)
            except (TypeError, AttributeError):
                return self.format_result(
                    success=False,
                    message="Actual value is not a list or iterable",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="list_contains",
                )

            # Handle different types of expected_value
            if isinstance(expected_value, list):
                # Check if all elements in expected_value are in actual_value
                missing_elements = [
                    item for item in expected_value if item not in actual_value
                ]
                success = len(missing_elements) == 0

                if success:
                    message = f"List contains all expected elements"
                else:
                    message = f"List is missing expected elements: {missing_elements}"

                return self.format_result(
                    success=success,
                    message=message,
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="list_contains",
                    missing_elements=missing_elements,
                )
            else:
                # Single element check
                success = expected_value in actual_value

                if success:
                    message = f"List contains the expected element"
                else:
                    message = f"List does not contain the expected element"

                return self.format_result(
                    success=success,
                    message=message,
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="list_contains",
                )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"List contains verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="list_contains",
                error=str(e),
            )


class ListUniqueVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value is iterable
            try:
                # Convert to list to ensure we can iterate multiple times
                actual_list = list(actual_value)
            except (TypeError, AttributeError):
                return self.format_result(
                    success=False,
                    message="Actual value is not a list or iterable",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="list_unique",
                )

            # Find duplicate elements
            seen = set()
            duplicates = []

            for item in actual_list:
                # Try to make the item hashable if it's not already
                try:
                    hashable_item = item
                    if isinstance(item, list):
                        hashable_item = tuple(item)
                    elif isinstance(item, dict):
                        hashable_item = frozenset(item.items())

                    if hashable_item in seen:
                        duplicates.append(item)
                    else:
                        seen.add(hashable_item)
                except TypeError:
                    # If item cannot be made hashable
                    duplicates.append(item)

            success = len(duplicates) == 0

            if success:
                message = "List contains only unique elements"
            else:
                message = f"List contains duplicate elements"

            return self.format_result(
                success=success,
                message=message,
                actual_value=actual_list,
                expected_value=expected_value,  # Not used for this verifier
                method="list_unique",
                duplicate_elements=duplicates,
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"List uniqueness verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="list_unique",
                error=str(e),
            )


class ListSortedVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value is iterable
            try:
                # Convert to list to ensure we can iterate multiple times
                actual_list = list(actual_value)
            except (TypeError, AttributeError):
                return self.format_result(
                    success=False,
                    message="Actual value is not a list or iterable",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="list_sorted",
                )

            if len(actual_list) <= 1:
                # Lists with 0 or 1 elements are always sorted
                return self.format_result(
                    success=True,
                    message="List is sorted (has 0 or 1 elements)",
                    actual_value=actual_list,
                    expected_value=expected_value,
                    method="list_sorted",
                )

            # Check if the list is sorted
            sort_order = (
                expected_value if isinstance(expected_value, str) else "ascending"
            )

            # Get comparison function based on sort order
            if sort_order.lower() in ("desc", "descending", "reverse"):
                # Check if list is sorted in descending order
                is_sorted = all(
                    actual_list[i] >= actual_list[i + 1]
                    for i in range(len(actual_list) - 1)
                )
                order_text = "descending"
            else:
                # Default: Check if list is sorted in ascending order
                is_sorted = all(
                    actual_list[i] <= actual_list[i + 1]
                    for i in range(len(actual_list) - 1)
                )
                order_text = "ascending"

            if is_sorted:
                message = f"List is sorted in {order_text} order"
            else:
                # Find the first out-of-order element
                for i in range(len(actual_list) - 1):
                    if (
                        sort_order.lower() in ("desc", "descending", "reverse")
                        and actual_list[i] < actual_list[i + 1]
                    ) or (
                        sort_order.lower() not in ("desc", "descending", "reverse")
                        and actual_list[i] > actual_list[i + 1]
                    ):
                        message = f"List is not sorted in {order_text} order (first unsorted elements at indices {i} and {i + 1})"
                        break
                else:
                    message = f"List is not sorted in {order_text} order"

            return self.format_result(
                success=is_sorted,
                message=message,
                actual_value=actual_list,
                expected_value=sort_order,
                method="list_sorted",
                sort_order=order_text,
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"List sorting verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="list_sorted",
                error=str(e),
            )


class ListAllMatchVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value is iterable
            try:
                # Convert to list to ensure we can iterate multiple times
                actual_list = list(actual_value)
            except (TypeError, AttributeError):
                return self.format_result(
                    success=False,
                    message="Actual value is not a list or iterable",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="list_all_match",
                )

            if not actual_list:
                # Empty list - technically all elements match any criteria
                return self.format_result(
                    success=True,
                    message="List is empty (all elements trivially match the criteria)",
                    actual_value=actual_list,
                    expected_value=expected_value,
                    method="list_all_match",
                )

            # The expected_value should be a criterion to apply to each element
            if isinstance(expected_value, dict) and "predicate" in expected_value:
                # Advanced predicate-based matching
                # Not implemented here - would require safe eval or a DSL
                return self.format_result(
                    success=False,
                    message="Predicate-based matching is not implemented",
                    actual_value=actual_list,
                    expected_value=expected_value,
                    method="list_all_match",
                )
            else:
                # Simple equality-based matching
                # Check if all elements match the expected value
                all_match = all(item == expected_value for item in actual_list)

                if all_match:
                    message = f"All list elements match the expected value"
                else:
                    non_matching = [
                        item for item in actual_list if item != expected_value
                    ]
                    message = f"Not all list elements match the expected value ({len(non_matching)} non-matching elements)"

                return self.format_result(
                    success=all_match,
                    message=message,
                    actual_value=actual_list,
                    expected_value=expected_value,
                    method="list_all_match",
                    non_matching_elements=[] if all_match else non_matching,
                )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"List all-match verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="list_all_match",
                error=str(e),
            )
