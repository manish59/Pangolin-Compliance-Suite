# Generated by Django 5.1.6 on 2025-03-15 20:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("test_protocols", "0003_remove_verificationmethod_run_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="testprotocol",
            name="verification_methods",
        ),
        migrations.AddField(
            model_name="verificationmethod",
            name="test_protocol",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="verification_methods",
                to="test_protocols.testprotocol",
            ),
        ),
    ]
