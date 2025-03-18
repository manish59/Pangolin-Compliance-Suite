# test_protocols/verifiers/api_verifiers.py
from .base import BaseVerifier


class ApiStatusCodeVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value is an integer or can be converted to one
            try:
                status_code = int(actual_value)
            except (ValueError, TypeError):
                # If actual_value is a response object with a status_code attribute (like requests.Response)
                if hasattr(actual_value, 'status_code'):
                    status_code = actual_value.status_code
                else:
                    return self.format_result(
                        success=False,
                        message="Actual value is not a valid status code or response object",
                        actual_value=actual_value,
                        expected_value=expected_value,
                        method="api_status_code"
                    )

            # Expected value can be a single status code or a list of valid codes
            if isinstance(expected_value, list):
                success = status_code in expected_value
                if success:
                    message = f"Status code {status_code} is in the list of expected codes: {expected_value}"
                else:
                    message = f"Status code {status_code} is not in the list of expected codes: {expected_value}"
            else:
                try:
                    expected_code = int(expected_value)
                except (ValueError, TypeError):
                    return self.format_result(
                        success=False,
                        message="Expected value is not a valid status code",
                        actual_value=status_code,
                        expected_value=expected_value,
                        method="api_status_code"
                    )

                # Use comparison operator if provided, otherwise check for equality
                if comparison_method:
                    operator = self.get_comparison_operator(comparison_method)
                    if not operator:
                        return self.format_result(
                            success=False,
                            message=f"Invalid comparison method: {comparison_method}",
                            actual_value=status_code,
                            expected_value=expected_code,
                            method="api_status_code"
                        )
                    success = operator(status_code, expected_code)
                    if success:
                        message = f"Status code {status_code} satisfies {comparison_method} {expected_code}"
                    else:
                        message = f"Status code {status_code} does not satisfy {comparison_method} {expected_code}"
                else:
                    # Default: check for equality
                    success = status_code == expected_code
                    if success:
                        message = f"Status code {status_code} matches expected code {expected_code}"
                    else:
                        message = f"Status code {status_code} does not match expected code {expected_code}"

            return self.format_result(
                success=success,
                message=message,
                actual_value=status_code,
                expected_value=expected_value,
                method="api_status_code"
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"API status code verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="api_status_code",
                error=str(e)
            )


class ApiResponseTimeVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value is a number or can be converted to one
            try:
                response_time = float(actual_value)
            except (ValueError, TypeError):
                # If actual_value is a response object with an elapsed attribute (like requests.Response)
                if hasattr(actual_value, 'elapsed'):
                    # Convert timedelta to seconds
                    response_time = actual_value.elapsed.total_seconds()
                else:
                    return self.format_result(
                        success=False,
                        message="Actual value is not a valid response time or response object",
                        actual_value=actual_value,
                        expected_value=expected_value,
                        method="api_response_time"
                    )

            # Expected value is the maximum acceptable response time
            try:
                expected_time = float(expected_value)
            except (ValueError, TypeError):
                return self.format_result(
                    success=False,
                    message="Expected value is not a valid response time threshold",
                    actual_value=response_time,
                    expected_value=expected_value,
                    method="api_response_time"
                )

            # Use comparison operator if provided, otherwise check if response_time <= expected_time
            if comparison_method:
                operator = self.get_comparison_operator(comparison_method)
                if not operator:
                    return self.format_result(
                        success=False,
                        message=f"Invalid comparison method: {comparison_method}",
                        actual_value=response_time,
                        expected_value=expected_time,
                        method="api_response_time"
                    )
                success = operator(response_time, expected_time)
                if success:
                    message = f"Response time {response_time:.3f}s satisfies {comparison_method} {expected_time:.3f}s"
                else:
                    message = f"Response time {response_time:.3f}s does not satisfy {comparison_method} {expected_time:.3f}s"
            else:
                # Default: check if response_time <= expected_time
                success = response_time <= expected_time
                if success:
                    message = f"Response time {response_time:.3f}s is within the expected threshold of {expected_time:.3f}s"
                else:
                    message = f"Response time {response_time:.3f}s exceeds the expected threshold of {expected_time:.3f}s"

            return self.format_result(
                success=success,
                message=message,
                actual_value=response_time,
                expected_value=expected_time,
                method="api_response_time"
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"API response time verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="api_response_time",
                error=str(e)
            )


class ApiHeadersVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Check if actual_value is a dict or can be accessed as one
            headers = None
            if isinstance(actual_value, dict):
                headers = actual_value
            elif hasattr(actual_value, 'headers'):
                # If actual_value is a response object with headers attribute (like requests.Response)
                headers = actual_value.headers
            else:
                return self.format_result(
                    success=False,
                    message="Actual value is not a valid headers dict or response object",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="api_headers"
                )

            # Convert headers to lowercase dict for case-insensitive comparison
            # This is because HTTP headers are case-insensitive
            headers_lower = {k.lower(): v for k, v in headers.items()}

            # Expected value should be a dict of headers to check
            if not isinstance(expected_value, dict):
                return self.format_result(
                    success=False,
                    message="Expected value is not a valid headers dict",
                    actual_value=headers,
                    expected_value=expected_value,
                    method="api_headers"
                )

            # Convert expected headers to lowercase for case-insensitive comparison
            expected_headers_lower = {k.lower(): v for k, v in expected_value.items()}

            # Check if all expected headers are present and match values
            missing_headers = []
            mismatched_headers = []

            for header_name, expected_value in expected_headers_lower.items():
                if header_name not in headers_lower:
                    missing_headers.append(header_name)
                elif headers_lower[header_name] != expected_value:
                    mismatched_headers.append(header_name)

            success = len(missing_headers) == 0 and len(mismatched_headers) == 0

            if success:
                message = "All expected headers are present with matching values"
            else:
                message = "Header verification failed"
                if missing_headers:
                    message += f". Missing headers: {missing_headers}"
                if mismatched_headers:
                    message += f". Mismatched header values: {mismatched_headers}"

            return self.format_result(
                success=success,
                message=message,
                actual_value=headers,
                expected_value=expected_value,
                method="api_headers",
                missing_headers=missing_headers,
                mismatched_headers=mismatched_headers
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"API headers verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="api_headers",
                error=str(e)
            )


class ApiContentTypeVerifier(BaseVerifier):
    def verify(self, actual_value, expected_value, comparison_method=None, config=None):
        try:
            # Extract content type from actual_value
            content_type = None

            if isinstance(actual_value, str):
                # If actual_value is already a content type string
                content_type = actual_value.lower()
            elif isinstance(actual_value, dict) and 'content-type' in actual_value:
                # If actual_value is a headers dict
                content_type = actual_value['content-type'].lower()
            elif isinstance(actual_value, dict) and 'Content-Type' in actual_value:
                # Check with capitalized header name
                content_type = actual_value['Content-Type'].lower()
            elif hasattr(actual_value, 'headers'):
                # If actual_value is a response object with headers (like requests.Response)
                headers = actual_value.headers

                # Headers object might be case-sensitive or case-insensitive based on implementation
                if isinstance(headers, dict):
                    content_type = headers.get('content-type') or headers.get('Content-Type')
                    if content_type:
                        content_type = content_type.lower()

            if content_type is None:
                return self.format_result(
                    success=False,
                    message="Could not extract Content-Type from the provided value",
                    actual_value=actual_value,
                    expected_value=expected_value,
                    method="api_content_type"
                )

            # Expected value should be a string or list of strings
            if isinstance(expected_value, str):
                expected_content_types = [expected_value.lower()]
            elif isinstance(expected_value, list):
                expected_content_types = [ct.lower() for ct in expected_value]
            else:
                return self.format_result(
                    success=False,
                    message="Expected value is not a valid content type or list of content types",
                    actual_value=content_type,
                    expected_value=expected_value,
                    method="api_content_type"
                )

            # Check for exact match or contains, based on comparison_method
            if comparison_method == 'contains':
                # Check if any expected content type is contained in the actual content type
                success = any(exp_ct in content_type for exp_ct in expected_content_types)
                if success:
                    message = f"Content-Type '{content_type}' contains one of the expected types"
                else:
                    message = f"Content-Type '{content_type}' does not contain any of the expected types: {expected_content_types}"
            else:
                # Default: Check for exact match
                success = content_type in expected_content_types
                if success:
                    message = f"Content-Type '{content_type}' matches one of the expected types"
                else:
                    message = f"Content-Type '{content_type}' does not match any of the expected types: {expected_content_types}"

            return self.format_result(
                success=success,
                message=message,
                actual_value=content_type,
                expected_value=expected_value,
                method="api_content_type"
            )
        except Exception as e:
            return self.format_result(
                success=False,
                message=f"API content type verification error: {str(e)}",
                actual_value=actual_value,
                expected_value=expected_value,
                method="api_content_type",
                error=str(e)
            )