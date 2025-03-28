import yaml
import json
from django.db import models
from engine.models import BaseModel
from projects.models import Project
from environments.models import Environment
from django.utils.translation import gettext_lazy as _


class TestSuite(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="test_suite")

    def __str__(self):
        return self.name
    class Meta:
        ordering = ['-created_at']

    def get_ordered_protocols(self):
        """
        Get all protocols ordered by the custom ordering index.

        Returns:
            QuerySet: Ordered protocols
        """
        return self.protocols.filter(status="active").order_by('order_index', 'name')


class TestProtocol(BaseModel):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('deprecated', 'Deprecated'),
        ('draft', 'Draft'),
        ('archived', 'Archived'),
    ]

    suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE, related_name='protocols')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    # User-defined ordering index
    order_index = models.IntegerField(default=0, help_text="Custom ordering index for this protocol")

    def __str__(self):
        return f"{self.name} ({self.suite.name})"

    class Meta:
        unique_together = ['suite', 'name']
        ordering = ['order_index', 'name']  # Order by custom index first, then by name



class ConnectionConfig(BaseModel):
    CONFIG_TYPE_CHOICES = [
        ('database', 'Database'),
        ('api', 'API'),
        ('ssh', 'SSH'),
        ('kubernetes', 'Kubernetes'),
        ('aws', 'AWS'),
        ('azure', 'Azure'),
    ]
    protocol = models.OneToOneField(TestProtocol, on_delete=models.CASCADE, related_name='connection_config')
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPE_CHOICES)
    timeout_seconds = models.IntegerField(default=30, help_text="Connection timeout in seconds")
    retry_attempts = models.IntegerField(default=3, help_text="Number of retry attempts on failure")
    # JSON field for additional configuration
    config_data = models.JSONField(default=dict, help_text="Additional configuration parameters")

    def __str__(self):
        return f"Connection for {self.protocol.name}"

    def save(self, *args, **kwargs):
        """
        convert the config_data field incoming str to JSON before saving.
        """
        if isinstance(self.config_data, str) and self.config_data.strip():
            try:
                config_data = yaml.safe_load(self.config_data)
                self.config_data = config_data
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing config_data YAML: {str(e)}")
        name = f"{self.config_type.upper()} - {self.protocol.name}"
        self.config_data['name'] = name
        super().save(*args, **kwargs)

class ProtocolRun(BaseModel):
    """
    Records a single execution run of a test protocol
    """
    protocol = models.ForeignKey(
        TestProtocol,
        on_delete=models.CASCADE,
        related_name='runs'
    )

    # Run metadata
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    executed_by = models.CharField(max_length=100, blank=True, null=True)

    # Overall status
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('started', 'Started'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('error', 'Error'),
        ('aborted', 'Aborted'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='running'
    )

    # Result status
    RESULT_STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('error', 'Error'),
        ('inconclusive', 'Inconclusive'),
    ]
    result_status = models.CharField(
        max_length=20,
        choices=RESULT_STATUS_CHOICES,
        blank=True,
        null=True
    )

    # Error details
    error_message = models.TextField(blank=True, null=True)

    # Duration
    duration_seconds = models.FloatField(blank=True, null=True)


    def __str__(self):
        return f"{self.protocol.name} Run - {self.started_at}"

    class Meta:
        verbose_name = _("Protocol Run")
        verbose_name_plural = _("Protocol Runs")
        ordering = ['-started_at']


VERIFICATION_METHOD_CHOICES = [
    # String verification methods
    ('string_exact_match', 'String Exact Match'),
    ('string_contains', 'String Contains'),
    ('string_regex_match', 'String Regex Match'),
    ('string_length', 'String Length Check'),
    ('string_format', 'String Format Validation'),

    # Numeric verification methods
    ('numeric_equal', 'Numeric Equality'),
    ('numeric_range', 'Numeric Range Check'),
    ('numeric_threshold', 'Numeric Threshold Check'),
    ('numeric_precision', 'Numeric Precision Check'),

    # Dictionary verification methods
    ('dict_has_keys', 'Dictionary Has Keys'),
    ('dict_schema_valid', 'Dictionary Schema Validation'),
    ('dict_subset', 'Dictionary Contains Subset'),
    ('dict_size', 'Dictionary Size Check'),

    # List verification methods
    ('list_length', 'List Length Check'),
    ('list_contains', 'List Contains Elements'),
    ('list_unique', 'List Elements Unique'),
    ('list_sorted', 'List Sorted Check'),
    ('list_all_match', 'All List Elements Match Criteria'),

    # API verification methods
    ('api_status_code', 'API Status Code Check'),
    ('api_response_time', 'API Response Time Check'),
    ('api_headers', 'API Headers Check'),
    ('api_content_type', 'API Content Type Check'),

    # Database verification methods
    ('db_row_count', 'Database Row Count Check'),
    ('db_column_exists', 'Database Column Exists'),
    ('db_query_result', 'Database Query Result Check'),
    ('db_execution_time', 'Database Query Execution Time'),

    # SSH verification methods
    ('ssh_exit_code', 'SSH Exit Code Check'),
    ('ssh_output_contains', 'SSH Output Contains'),
    ('ssh_execution_time', 'SSH Execution Time Check'),
    ('ssh_file_exists', 'SSH File Exists Check'),

    # S3 IQ verification methods
    ('s3_iq_access', 'S3 Access Verification'),
    ('s3_iq_config', 'S3 Configuration Validation'),
    ('s3_iq_security', 'S3 Security Setup Check'),
    ('s3_iq_network', 'S3 Network Connectivity'),
    ('s3_iq_performance', 'S3 Performance Baseline'),

    # S3 OQ verification methods
    ('s3_oq_basic_ops', 'S3 Basic Operations Check'),
    ('s3_oq_adv_ops', 'S3 Advanced Operations Check'),
    ('s3_oq_storage_class', 'S3 Storage Class Operations'),
    ('s3_oq_access_control', 'S3 Access Control Check'),
    ('s3_oq_performance', 'S3 Performance Check'),
    ('s3_oq_reliability', 'S3 Reliability Check'),
    ('s3_oq_data_integrity', 'S3 Data Integrity Check'),
]

# Define comparison operators
COMPARISON_OPERATOR_CHOICES = [
    ('eq', 'Equals'),
    ('neq', 'Not Equals'),
    ('gt', 'Greater Than'),
    ('gte', 'Greater Than or Equal'),
    ('lt', 'Less Than'),
    ('lte', 'Less Than or Equal'),
    ('contains', 'Contains'),
    ('not_contains', 'Does Not Contain'),
    ('starts_with', 'Starts With'),
    ('ends_with', 'Ends With'),
    ('matches', 'Matches Regex'),
    ('in', 'In List'),
    ('not_in', 'Not In List'),
]

# Validation result status choices
RESULT_STATUS_CHOICES = [
    ('pass', 'Pass'),
    ('fail', 'Fail'),
    ('error', 'Error'),
    ('not_run', 'Not Run'),
    ('skipped', 'Skipped'),
]

class ExecutionStep(BaseModel):
    """
    A single step in a test protocol execution
    """
    name= models.CharField(max_length=100, default=None, null=True, blank=True)
    test_protocol = models.ForeignKey(TestProtocol, on_delete=models.CASCADE, related_name='steps')
    # Keyword arguments (kwargs) stored as JSON object
    kwargs = models.JSONField(
        default=dict,
        help_text=_("Keyword arguments (kwargs) as a JSON object")
    )

    class Meta:
        verbose_name = _("Execution Step")
        verbose_name_plural = _("Execution Steps")

    def __str__(self):
        return f"{self.name}- {self.test_protocol}"
    def __repr__(self):
        return f"{self.name}- {self.test_protocol}"

    def save(self, *args, **kwargs):
        """
        convert the config_data field incoming str to JSON before saving.
        """
        if isinstance(self.kwargs, str) and self.kwargs.strip():
            try:
                kwargs = yaml.safe_load(self.kwargs)
                self.kwargs = kwargs
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing config_data YAML: {str(e)}")
        super().save(*args, **kwargs)

class VerificationMethod(BaseModel):
    """
    A specific method of verification that can be applied to test results
    """
    execution_step = models.ForeignKey(ExecutionStep, on_delete=models.CASCADE, related_name='verification_methods', default=None, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    method_type = models.CharField(max_length=30, choices=VERIFICATION_METHOD_CHOICES)
    # For methods requiring a comparison operator
    supports_comparison = models.BooleanField(default=False)
    comparison_method = models.CharField(max_length=50, choices=COMPARISON_OPERATOR_CHOICES)
    expected_result = models.JSONField(default=dict)
    # Additional configuration for this verification method
    config_schema = models.JSONField(
        default=dict,
        help_text=_("JSON schema for configuration parameters")
    )

    # Requirements for this verification method
    requires_expected_value = models.BooleanField(
        default=True,
        help_text=_("Whether this method requires an expected value")
    )
    supports_dynamic_expected = models.BooleanField(
        default=False,
        help_text=_("Whether this method supports dynamic expected values from environment variables")
    )

    def __str__(self):
        return f"{self.name}"

    def verify(self, actual_value, expected_result=None, config_schema=None):
        """
        Verify the actual value against expected value using the defined verification method.

        Args:
            actual_value: The value to verify
            expected_value: The expected value to verify against (default: None, will use self.expected_result)

        Returns:
            dict: A dictionary containing:
                - success (bool): Whether verification passed
                - message (str): Explanation of the result
                - actual_value: The actual value that was verified
                - expected_value: The expected value used in verification
                - method: The verification method used
        """
        from test_protocols.verifiers import VerificationFactory


        # Create the appropriate verifier based on method type
        verifier = VerificationFactory.create_verifier(self.method_type)
        expected_value = expected_result.get("result")
        # Execute verification
        try:
            result = verifier.verify(
                actual_value=actual_value,
                expected_value=expected_value,
                comparison_method=self.comparison_method if self.supports_comparison else None,
                config=self.config_schema
            )
            return result
        except Exception as e:
            return {
                'success': False,
                'message': f'Verification error: {str(e)}',
                'actual_value': actual_value,
                'expected_value': expected_value,
                'method': self.method_type,
                'error': str(e)
            }

    class Meta:
        verbose_name = _("Verification Method")
        verbose_name_plural = _("Verification Methods")
        ordering = ['-created_at']


class VerificationResult(BaseModel):
    """
    Stores the result of applying a verification method to an execution result.
    Links the verification step with the actual outcome of the verification.
    """
    # Link to the verification step and execution result
    verification_step = models.ForeignKey(
        VerificationMethod,
        on_delete=models.CASCADE,
        related_name='results',
        help_text="The verification step that was performed"
    )

    # Timestamp information
    verification_time = models.DateTimeField(
        auto_now_add=True,
        help_text="When this verification was performed"
    )

    # Verification outcome
    success = models.BooleanField(
        default=False,
        help_text="Whether the verification passed or failed"
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ('pass', 'Pass'),
            ('fail', 'Fail'),
            ('error', 'Error'),
            ('skipped', 'Skipped'),
            ('not_applicable', 'Not Applicable')
        ],
        default='fail',
        help_text="Detailed status of the verification"
    )

    # Verification data
    actual_value = models.JSONField(
        null=True,
        help_text="The actual value that was verified"
    )
    expected_value = models.JSONField(
        null=True,
        help_text="The expected value used for verification"
    )
    message = models.TextField(
        blank=True,
        null=True,
        help_text="Human-readable explanation of the verification result"
    )

    # Error information (if verification failed due to an error)
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if verification process encountered an error"
    )
    error_stack_trace = models.TextField(
        blank=True,
        null=True,
        help_text="Stack trace from verification error"
    )

    # Detailed result data
    result_data = models.JSONField(
        default=dict,
        help_text="Complete verification result data returned by the verifier"
    )

    class Meta:
        verbose_name = "Verification Result"
        verbose_name_plural = "Verification Results"
        ordering = ['verification_time']

    def __str__(self):
        return f"Verification of '{self.verification_step.name}' - {'Passed' if self.success else 'Failed'}"
