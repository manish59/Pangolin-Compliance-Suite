# Generated by Django 5.1.6 on 2025-03-15 19:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_protocols', '0002_verificationmethod_run'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='verificationmethod',
            name='run',
        ),
        migrations.AddField(
            model_name='testprotocol',
            name='verification_methods',
            field=models.ManyToManyField(blank=True, default=None, related_name='test_protocols', to='test_protocols.verificationmethod'),
        ),
    ]
