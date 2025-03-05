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
        return self.protocols.all().order_by('order_index', 'name')


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
    host = models.CharField(max_length=255, blank=True, null=True)
    port = models.IntegerField(blank=True, null=True)
    # Environment variables for sensitive data
    username = models.ForeignKey(
        Environment,
        on_delete=models.SET_NULL,
        related_name="username_configs",
        blank=True,
        null=True,
        help_text="Environment variable for username"
    )
    password = models.ForeignKey(
        Environment,
        on_delete=models.SET_NULL,
        related_name="password_configs",
        blank=True,
        null=True,
        help_text="Environment variable for password"
    )
    secret_key = models.ForeignKey(
        Environment,
        on_delete=models.SET_NULL,
        related_name="secret_key_configs",
        blank=True,
        null=True,
        help_text="Environment variable for secret key/token"
    )

    timeout_seconds = models.IntegerField(default=30, help_text="Connection timeout in seconds")
    retry_attempts = models.IntegerField(default=3, help_text="Number of retry attempts on failure")

    # JSON field for additional configuration
    config_data = models.JSONField(default=dict, help_text="Additional configuration parameters")

    def __str__(self):
        return f"Connection for {self.protocol.name}"


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


class ProtocolResult(BaseModel):
    """
    A single unified result for a protocol run
    """
    # One-to-one relationship with ProtocolRun
    run = models.OneToOneField(
        ProtocolRun,
        on_delete=models.CASCADE,
        related_name='result'
    )

    # Success flag
    success = models.BooleanField(default=False)

    # JSON data for structured results
    result_data = models.JSONField(
        blank=True,
        null=True,
        help_text=_("Structured result data in JSON format")
    )

    # Text results for when JSON isn't appropriate
    result_text = models.TextField(
        blank=True,
        null=True,
        help_text=_("Unstructured result text")
    )

    # Binary data (if needed)
    result_binary = models.BinaryField(
        blank=True,
        null=True,
        help_text=_("Binary result data")
    )
    error_message = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"Result for {self.run.protocol.name} Run"

    class Meta:
        verbose_name = _("Protocol Result")
        verbose_name_plural = _("Protocol Results")



class ResultAttachment(BaseModel):
    """
    File or data attachments for a protocol result
    """
    result = models.ForeignKey(
        ProtocolResult,
        on_delete=models.CASCADE,
        related_name='attachments'
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # File attachment
    file = models.FileField(
        upload_to='protocol_results/attachments/%Y/%m/%d/',
        blank=True,
        null=True
    )

    # Content type
    content_type = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.result}"

    class Meta:
        verbose_name = _("Result Attachment")
        verbose_name_plural = _("Result Attachments")


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


class VerificationMethod(BaseModel):
    """
    A specific method of verification that can be applied to test results
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    method_type = models.CharField(max_length=30, choices=VERIFICATION_METHOD_CHOICES)

    # For methods requiring a comparison operator
    supports_comparison = models.BooleanField(default=False)
    comparison_method = models.CharField(max_length=50, choices=COMPARISON_OPERATOR_CHOICES)
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

    class Meta:
        verbose_name = _("Verification Method")
        verbose_name_plural = _("Verification Methods")
        ordering = ['-created_at']
