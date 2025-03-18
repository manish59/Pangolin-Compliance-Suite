# test_protocols/verifiers/db_verifiers.py
from .base import BaseVerifier


class DbRowCountVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value can be interpreted as a row count
            try:
                if isinstance(actual_value, list):
                    row_count = len(actual_value)
                elif hasattr(actual_value, '__len__'):
                    row_count = len(actual_value)
                else:
                    row_count = int(actual_value)
            except (ValueError, TypeError):
                return self.format_result(
                    success=False,
                    message="Actual value cannot be interpreted as a row count",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="db_row_count"
                )

            # Expected value can be a single count or a range dict
            if isinstance(expected_value, dict) and 'min' in expected_value and 'max' in expected_value:
                # Range check
                min_count = int(expected_value['min'])
                max_count = int(expected_value['max'])

                success = min_count <= row_count <= max_count

                if success:
                    message = f"Row count {row_count} is within the expected range [{min_count}, {max_count}]"
                else:
                    message = f"Row count {row_count} is outside the expected range [{min_count}, {max_count}]"
            else:
                # Single value check with comparison operator
                try:
                    expected_count = int(expected_value)
                except (ValueError, TypeError):
                    return self.format_result(
                        success=False,
                        message="Expected value cannot be interpreted as a row count",
                        actual_value=row_count,
                        expected_value=expected_value,
                        method="db_row_count"
                    )

                # Use comparison operator if provided, otherwise check for equality
                if comparison_method:
                    operator = self.get_comparison_operator(comparison_method)
                    if not operator:
                        return self.format_result(
                            success=False,
                            message=f"Invalid comparison method: {comparison_method}",
                            actual_value=row_count,
                            expected_value=expected_count,
                            method="db_row_count"
                        )
                    success = operator(row_count, expected_count)
                    if success:
                        message = f"Row count {row_count} satisfies {comparison_method} {expected_count}"
                    else:
                        message = f"Row count {row_count} does not satisfy {comparison_method} {expected_count}"
                else:
                    # Default: check for equality
                    success = row_count == expected_count
                    if success:
                        message = f"Row count {row_count} matches expected count {expected_count}"
                    else:
                        message = f"Row count {row_count} does not match expected count {expected_count}"

            return self.format_result(
                success=success,
                message=message,
                actual_value=row_count,
                expected_value=expected_value,
                method="db_row_count"
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"Database row count verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="db_row_count",
                error=str(e)
            )

class DbColumnExistsVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Expected value is the column name or list of column names to check
            if isinstance(expected_value, str):
                column_names = [expected_value]
            elif isinstance(expected_value, list):
                column_names = expected_value
            else:
                return self.format_result(
                    success=False,
                    message="Expected value must be a column name or list of column names",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="db_column_exists"
                )

            # Actual value can be various types of database results
            # Try to extract column names from the actual value
            available_columns = []

            if isinstance(actual_value, dict):
                # If it's a dict, use the keys as column names
                available_columns = list(actual_value.keys())
            elif isinstance(actual_value, list) and len(actual_value) > 0:
                # If it's a list of dicts (common DB result format), use keys from first row
                if isinstance(actual_value[0], dict):
                    available_columns = list(actual_value[0].keys())
            elif hasattr(actual_value, 'columns'):
                # If it has a columns attribute (like pandas DataFrame)
                available_columns = list(actual_value.columns)
            elif hasattr(actual_value, 'description') and actual_value.description:
                # If it has a description attribute with column info (like DB cursor)
                available_columns = [col[0] for col in actual_value.description]
            else:
                return self.format_result(
                    success=False,
                    message="Could not extract column names from the provided value",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="db_column_exists"
                )

            # Check if all expected columns exist
            missing_columns = [col for col in column_names if col not in available_columns]
            success = len(missing_columns) == 0

            if success:
                message = f"All expected columns exist: {column_names}"
            else:
                message = f"Missing columns: {missing_columns}"

            return self.format_result(
                success=success,
                message=message,
                actual_value=available_columns,
                expected_value=column_names,
                method="db_column_exists",
                missing_columns=missing_columns
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"Database column existence verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="db_column_exists",
                error=str(e)
            )


class DbQueryResultVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Actual value is the query result
            # Expected value can be a dict with criteria for checking results

            if not isinstance(expected_value, dict):
                return self.format_result(
                    success=False,
                    message="Expected value must be a dictionary with verification criteria",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="db_query_result"
                )

            # Extract verification type from expected value
            verification_type = expected_value.get('type', 'exact_match')

            # Normalize actual value to a consistent format
            query_result = actual_value
            if hasattr(actual_value, 'fetchall'):
                # If it's a cursor, fetch all results
                query_result = actual_value.fetchall()

                # Convert to list of dicts if we have column info
                if hasattr(actual_value, 'description') and actual_value.description:
                    columns = [col[0] for col in actual_value.description]
                    query_result = [dict(zip(columns, row)) for row in query_result]

            # Handle different verification types
            if verification_type == 'exact_match':
                # Expected value should contain 'value' to match exactly
                if 'value' not in expected_value:
                    return self.format_result(
                        success=False,
                        message="Expected value for exact match must contain 'value' key",
                        actual_value=query_result,
                        expected_value=expected_value,
                        method="db_query_result"
                    )

                expected_result = expected_value['value']
                success = query_result == expected_result

                if success:
                    message = "Query result exactly matches expected value"
                else:
                    message = "Query result does not match expected value"

            elif verification_type == 'contains_row':
                # Expected value should contain 'row' to check for in results
                if 'row' not in expected_value:
                    return self.format_result(
                        success=False,
                        message="Expected value for contains_row must contain 'row' key",
                        actual_value=query_result,
                        expected_value=expected_value,
                        method="db_query_result"
                    )

                expected_row = expected_value['row']

                # Check if any row matches the expected row
                if isinstance(query_result, list) and all(isinstance(row, dict) for row in query_result):
                    # If query_result is a list of dicts
                    success = any(
                        all(k in row and row[k] == v for k, v in expected_row.items())
                        for row in query_result
                    )
                elif isinstance(query_result, list):
                    # If query_result is a list of tuples/lists, convert expected_row to set for comparison
                    expected_set = set(expected_row.values() if isinstance(expected_row, dict) else expected_row)
                    success = any(set(row) == expected_set for row in query_result)
                else:
                    success = False

                if success:
                    message = "Query result contains the expected row"
                else:
                    message = "Query result does not contain the expected row"

            elif verification_type == 'no_rows':
                # Check if the query returned no rows
                if isinstance(query_result, list):
                    success = len(query_result) == 0
                else:
                    success = not query_result

                if success:
                    message = "Query returned no rows as expected"
                else:
                    message = "Query returned rows when none were expected"

            elif verification_type == 'custom':
                # Custom verification not implemented - would require DSL or safe eval
                return self.format_result(
                    success=False,
                    message="Custom query result verification is not implemented",
                    actual_value=query_result,
                    expected_value=expected_value,
                    method="db_query_result"
                )
            else:
                return self.format_result(
                    success=False,
                    message=f"Unknown verification type: {verification_type}",
                    actual_value=query_result,
                    expected_value=expected_value,
                    method="db_query_result"
                )

            return self.format_result(
                success=success,
                message=message,
                actual_value=query_result,
                expected_value=expected_value,
                method="db_query_result",
                verification_type=verification_type
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"Database query result verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="db_query_result",
                error=str(e)
            )


class DbExecutionTimeVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value can be interpreted as a execution time (in seconds)
            try:
                execution_time = float(actual_value)
            except (ValueError, TypeError):
                return self.format_result(
                    success=False,
                    message="Actual value cannot be interpreted as an execution time",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="db_execution_time"
                )

            # Expected value is the maximum acceptable execution time (in seconds)
            try:
                max_time = float(expected_value)
            except (ValueError, TypeError):
                return self.format_result(
                    success=False,
                    message="Expected value cannot be interpreted as a maximum execution time",
                    actual_value=execution_time,
                    expected_value=expected_value,
                    method="db_execution_time"
                )

            # Use comparison operator if provided, otherwise check if execution_time <= max_time
            if comparison_method:
                operator = self.get_comparison_operator(comparison_method)
                if not operator:
                    return self.format_result(
                        success=False,
                        message=f"Invalid comparison method: {comparison_method}",
                        actual_value=execution_time,
                        expected_value=max_time,
                        method="db_execution_time"
                    )
                success = operator(execution_time, max_time)
                if success:
                    message = f"Execution time {execution_time:.3f}s satisfies {comparison_method} {max_time:.3f}s"
                else:
                    message = f"Execution time {execution_time:.3f}s does not satisfy {comparison_method} {max_time:.3f}s"
            else:
                # Default: check if execution_time <= max_time
                success = execution_time <= max_time
                if success:
                    message = f"Execution time {execution_time:.3f}s is within the maximum allowed time of {max_time:.3f}s"
                else:
                    message = f"Execution time {execution_time:.3f}s exceeds the maximum allowed time of {max_time:.3f}s"

            return self.format_result(
                success=success,
                message=message,
                actual_value=execution_time,
                expected_value=max_time,
                method="db_execution_time"
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"Database execution time verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="db_execution_time",
                error=str(e)
            )