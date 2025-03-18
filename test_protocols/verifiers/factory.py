# test_protocols/verifiers/factory.py (updated)
from .string_verifiers import (
    StringExactMatchVerifier, StringContainsVerifier,
    StringRegexMatchVerifier, StringLengthVerifier
)
from .numeric_verifiers import (
    NumericEqualVerifier, NumericRangeVerifier, NumericThresholdVerifier
)
from .dict_verifiers import (
    DictHasKeysVerifier, DictSchemaVerifier, DictSubsetVerifier
)
from .list_verifiers import (
    ListLengthVerifier, ListContainsVerifier,
    ListUniqueVerifier, ListSortedVerifier,
    ListAllMatchVerifier
)
from .api_verifiers import (
    ApiStatusCodeVerifier, ApiResponseTimeVerifier,
    ApiHeadersVerifier, ApiContentTypeVerifier
)
from .db_verifiers import (
    DbRowCountVerifier, DbColumnExistsVerifier,
    DbQueryResultVerifier, DbExecutionTimeVerifier
)


class VerificationFactory:
    """Factory for creating verifier instances based on method type"""

    @staticmethod
    def create_verifier(method_type):
        """
        Create and return the appropriate verifier for the given method type.

        Args:
            method_type (str): The verification method type

        Returns:
            BaseVerifier: An instance of the appropriate verifier

        Raises:
            ValueError: If method_type is not supported
        """
        # Map method types to verifier classes
        verifiers = {
            # String verifiers
            'string_exact_match': StringExactMatchVerifier,
            'string_contains': StringContainsVerifier,
            'string_regex_match': StringRegexMatchVerifier,
            'string_length': StringLengthVerifier,
            'string_format': StringRegexMatchVerifier,  # Can reuse regex verifier for format checking

            # Numeric verifiers
            'numeric_equal': NumericEqualVerifier,
            'numeric_range': NumericRangeVerifier,
            'numeric_threshold': NumericThresholdVerifier,
            'numeric_precision': NumericEqualVerifier,  # Can reuse equal verifier with proper config

            # Dictionary verifiers
            'dict_has_keys': DictHasKeysVerifier,
            'dict_schema_valid': DictSchemaVerifier,
            'dict_subset': DictSubsetVerifier,
            'dict_size': DictHasKeysVerifier,  # Can reuse has_keys verifier for size checking

            # List verifiers
            'list_length': ListLengthVerifier,
            'list_contains': ListContainsVerifier,
            'list_unique': ListUniqueVerifier,
            'list_sorted': ListSortedVerifier,
            'list_all_match': ListAllMatchVerifier,

            # API verifiers
            'api_status_code': ApiStatusCodeVerifier,
            'api_response_time': ApiResponseTimeVerifier,
            'api_headers': ApiHeadersVerifier,
            'api_content_type': ApiContentTypeVerifier,

            # Database verifiers
            'db_row_count': DbRowCountVerifier,
            'db_column_exists': DbColumnExistsVerifier,
            'db_query_result': DbQueryResultVerifier,
            'db_execution_time': DbExecutionTimeVerifier,

            # SSH verifiers could be implemented similarly
            # 'ssh_exit_code': SshExitCodeVerifier,
            # 'ssh_output_contains': SshOutputContainsVerifier,
            # 'ssh_execution_time': SshExecutionTimeVerifier,
            # 'ssh_file_exists': SshFileExistsVerifier,

            # S3 verifiers could be implemented similarly
            # AWS S3 verifiers...
        }

        # Get the verifier class for the method type
        verifier_class = verifiers.get(method_type)

        if not verifier_class:
            raise ValueError(f"Unsupported verification method type: {method_type}")

        # Instantiate and return the verifier
        return verifier_class()