# Generated by Django 5.1.6 on 2025-03-05 07:09

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("environments", "0001_initial"),
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProtocolRun",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when the record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when the record was last updated",
                    ),
                ),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "executed_by",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("running", "Running"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("error", "Error"),
                            ("aborted", "Aborted"),
                        ],
                        default="running",
                        max_length=20,
                    ),
                ),
                (
                    "result_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("pass", "Pass"),
                            ("fail", "Fail"),
                            ("error", "Error"),
                            ("inconclusive", "Inconclusive"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                ("error_message", models.TextField(blank=True, null=True)),
                ("duration_seconds", models.FloatField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Protocol Run",
                "verbose_name_plural": "Protocol Runs",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="TestProtocol",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when the record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when the record was last updated",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("deprecated", "Deprecated"),
                            ("draft", "Draft"),
                            ("archived", "Archived"),
                        ],
                        default="active",
                        max_length=50,
                    ),
                ),
                (
                    "order_index",
                    models.IntegerField(
                        default=0, help_text="Custom ordering index for this protocol"
                    ),
                ),
            ],
            options={
                "ordering": ["order_index", "name"],
            },
        ),
        migrations.CreateModel(
            name="VerificationMethod",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when the record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when the record was last updated",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "method_type",
                    models.CharField(
                        choices=[
                            ("string_exact_match", "String Exact Match"),
                            ("string_contains", "String Contains"),
                            ("string_regex_match", "String Regex Match"),
                            ("string_length", "String Length Check"),
                            ("string_format", "String Format Validation"),
                            ("numeric_equal", "Numeric Equality"),
                            ("numeric_range", "Numeric Range Check"),
                            ("numeric_threshold", "Numeric Threshold Check"),
                            ("numeric_precision", "Numeric Precision Check"),
                            ("dict_has_keys", "Dictionary Has Keys"),
                            ("dict_schema_valid", "Dictionary Schema Validation"),
                            ("dict_subset", "Dictionary Contains Subset"),
                            ("dict_size", "Dictionary Size Check"),
                            ("list_length", "List Length Check"),
                            ("list_contains", "List Contains Elements"),
                            ("list_unique", "List Elements Unique"),
                            ("list_sorted", "List Sorted Check"),
                            ("list_all_match", "All List Elements Match Criteria"),
                            ("api_status_code", "API Status Code Check"),
                            ("api_response_time", "API Response Time Check"),
                            ("api_headers", "API Headers Check"),
                            ("api_content_type", "API Content Type Check"),
                            ("db_row_count", "Database Row Count Check"),
                            ("db_column_exists", "Database Column Exists"),
                            ("db_query_result", "Database Query Result Check"),
                            ("db_execution_time", "Database Query Execution Time"),
                            ("ssh_exit_code", "SSH Exit Code Check"),
                            ("ssh_output_contains", "SSH Output Contains"),
                            ("ssh_execution_time", "SSH Execution Time Check"),
                            ("ssh_file_exists", "SSH File Exists Check"),
                            ("s3_iq_access", "S3 Access Verification"),
                            ("s3_iq_config", "S3 Configuration Validation"),
                            ("s3_iq_security", "S3 Security Setup Check"),
                            ("s3_iq_network", "S3 Network Connectivity"),
                            ("s3_iq_performance", "S3 Performance Baseline"),
                            ("s3_oq_basic_ops", "S3 Basic Operations Check"),
                            ("s3_oq_adv_ops", "S3 Advanced Operations Check"),
                            ("s3_oq_storage_class", "S3 Storage Class Operations"),
                            ("s3_oq_access_control", "S3 Access Control Check"),
                            ("s3_oq_performance", "S3 Performance Check"),
                            ("s3_oq_reliability", "S3 Reliability Check"),
                            ("s3_oq_data_integrity", "S3 Data Integrity Check"),
                        ],
                        max_length=30,
                    ),
                ),
                ("supports_comparison", models.BooleanField(default=False)),
                (
                    "comparison_method",
                    models.CharField(
                        choices=[
                            ("eq", "Equals"),
                            ("neq", "Not Equals"),
                            ("gt", "Greater Than"),
                            ("gte", "Greater Than or Equal"),
                            ("lt", "Less Than"),
                            ("lte", "Less Than or Equal"),
                            ("contains", "Contains"),
                            ("not_contains", "Does Not Contain"),
                            ("starts_with", "Starts With"),
                            ("ends_with", "Ends With"),
                            ("matches", "Matches Regex"),
                            ("in", "In List"),
                            ("not_in", "Not In List"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "config_schema",
                    models.JSONField(
                        default=dict,
                        help_text="JSON schema for configuration parameters",
                    ),
                ),
                (
                    "requires_expected_value",
                    models.BooleanField(
                        default=True,
                        help_text="Whether this method requires an expected value",
                    ),
                ),
                (
                    "supports_dynamic_expected",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this method supports dynamic expected values from environment variables",
                    ),
                ),
            ],
            options={
                "verbose_name": "Verification Method",
                "verbose_name_plural": "Verification Methods",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ProtocolResult",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when the record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when the record was last updated",
                    ),
                ),
                ("success", models.BooleanField(default=False)),
                (
                    "result_data",
                    models.JSONField(
                        blank=True,
                        help_text="Structured result data in JSON format",
                        null=True,
                    ),
                ),
                (
                    "result_text",
                    models.TextField(
                        blank=True, help_text="Unstructured result text", null=True
                    ),
                ),
                (
                    "result_binary",
                    models.BinaryField(
                        blank=True, help_text="Binary result data", null=True
                    ),
                ),
                ("error_message", models.TextField(blank=True, null=True)),
                (
                    "run",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="result",
                        to="test_protocols.protocolrun",
                    ),
                ),
            ],
            options={
                "verbose_name": "Protocol Result",
                "verbose_name_plural": "Protocol Results",
            },
        ),
        migrations.CreateModel(
            name="ResultAttachment",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when the record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when the record was last updated",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "file",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="protocol_results/attachments/%Y/%m/%d/",
                    ),
                ),
                (
                    "content_type",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "result",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="test_protocols.protocolresult",
                    ),
                ),
            ],
            options={
                "verbose_name": "Result Attachment",
                "verbose_name_plural": "Result Attachments",
            },
        ),
        migrations.AddField(
            model_name="protocolrun",
            name="protocol",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="runs",
                to="test_protocols.testprotocol",
            ),
        ),
        migrations.CreateModel(
            name="ConnectionConfig",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when the record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when the record was last updated",
                    ),
                ),
                (
                    "config_type",
                    models.CharField(
                        choices=[
                            ("database", "Database"),
                            ("api", "API"),
                            ("ssh", "SSH"),
                            ("kubernetes", "Kubernetes"),
                            ("aws", "AWS"),
                            ("azure", "Azure"),
                        ],
                        max_length=20,
                    ),
                ),
                ("host", models.CharField(blank=True, max_length=255, null=True)),
                ("port", models.IntegerField(blank=True, null=True)),
                (
                    "timeout_seconds",
                    models.IntegerField(
                        default=30, help_text="Connection timeout in seconds"
                    ),
                ),
                (
                    "retry_attempts",
                    models.IntegerField(
                        default=3, help_text="Number of retry attempts on failure"
                    ),
                ),
                (
                    "config_data",
                    models.JSONField(
                        default=dict, help_text="Additional configuration parameters"
                    ),
                ),
                (
                    "password",
                    models.ForeignKey(
                        blank=True,
                        help_text="Environment variable for password",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="password_configs",
                        to="environments.environment",
                    ),
                ),
                (
                    "secret_key",
                    models.ForeignKey(
                        blank=True,
                        help_text="Environment variable for secret key/token",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="secret_key_configs",
                        to="environments.environment",
                    ),
                ),
                (
                    "username",
                    models.ForeignKey(
                        blank=True,
                        help_text="Environment variable for username",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="username_configs",
                        to="environments.environment",
                    ),
                ),
                (
                    "protocol",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="connection_config",
                        to="test_protocols.testprotocol",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="TestSuite",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when the record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when the record was last updated",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="test_suite",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="testprotocol",
            name="suite",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="protocols",
                to="test_protocols.testsuite",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="testprotocol",
            unique_together={("suite", "name")},
        ),
    ]
