# Generated by Django 5.1.6 on 2025-03-17 07:53

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("test_protocols", "0007_verificationmethod_expected_result"),
    ]

    operations = [
        migrations.AddField(
            model_name="verificationmethod",
            name="execution_step",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="verification_methods",
                to="test_protocols.executionstep",
            ),
        ),
        migrations.CreateModel(
            name="VerificationResult",
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
                    "verification_time",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="When this verification was performed",
                    ),
                ),
                (
                    "success",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the verification passed or failed",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pass", "Pass"),
                            ("fail", "Fail"),
                            ("error", "Error"),
                            ("skipped", "Skipped"),
                            ("not_applicable", "Not Applicable"),
                        ],
                        default="fail",
                        help_text="Detailed status of the verification",
                        max_length=50,
                    ),
                ),
                (
                    "actual_value",
                    models.JSONField(
                        help_text="The actual value that was verified", null=True
                    ),
                ),
                (
                    "expected_value",
                    models.JSONField(
                        help_text="The expected value used for verification", null=True
                    ),
                ),
                (
                    "message",
                    models.TextField(
                        blank=True,
                        help_text="Human-readable explanation of the verification result",
                        null=True,
                    ),
                ),
                (
                    "error_message",
                    models.TextField(
                        blank=True,
                        help_text="Error message if verification process encountered an error",
                        null=True,
                    ),
                ),
                (
                    "error_stack_trace",
                    models.TextField(
                        blank=True,
                        help_text="Stack trace from verification error",
                        null=True,
                    ),
                ),
                (
                    "result_data",
                    models.JSONField(
                        default=dict,
                        help_text="Complete verification result data returned by the verifier",
                    ),
                ),
                (
                    "verification_step",
                    models.OneToOneField(
                        help_text="The verification step that was performed",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="test_protocols.verificationmethod",
                    ),
                ),
            ],
            options={
                "verbose_name": "Verification Result",
                "verbose_name_plural": "Verification Results",
                "ordering": ["verification_time"],
            },
        ),
    ]
