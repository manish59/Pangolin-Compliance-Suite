# Generated by Django 5.1.6 on 2025-03-17 06:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("test_protocols", "0006_executionstep"),
    ]

    operations = [
        migrations.AddField(
            model_name="verificationmethod",
            name="expected_result",
            field=models.JSONField(default=dict),
        ),
    ]
