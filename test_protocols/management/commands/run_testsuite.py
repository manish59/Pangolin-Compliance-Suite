# test_protocols/management/commands/run_testsuite.py
import uuid
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from test_protocols.models import TestSuite
from test_protocols.services import run_test_suite


class Command(BaseCommand):
    help = "Run all protocols in a test suite"

    def add_arguments(self, parser):
        parser.add_argument(
            "suite_id", type=str, help="The UUID of the test suite to run"
        )
        parser.add_argument(
            "--user", type=str, help="Username to attribute the runs to"
        )

    def handle(self, *args, **options):
        suite_id = options["suite_id"]
        username = options.get("user")

        try:
            # Parse the suite ID as a UUID
            suite_id = uuid.UUID(suite_id)
        except ValueError:
            raise CommandError(f"Invalid test suite ID: {suite_id}")

        # Get the user if specified
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"User {username} not found, proceeding with system user"
                    )
                )

        try:
            # Get the test suite
            suite = TestSuite.objects.get(id=suite_id)
            self.stdout.write(self.style.SUCCESS(f"Found test suite: {suite.name}"))

            # Run the test suite
            runs = run_test_suite(suite_id, user)

            if runs:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Started {len(runs)} protocol runs in test suite {suite.name}"
                    )
                )
                for run in runs:
                    self.stdout.write(
                        f"  - Protocol: {run.protocol.name}, Run ID: {run.id}"
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"No active protocols found in test suite {suite.name}"
                    )
                )

        except TestSuite.DoesNotExist:
            raise CommandError(f"Test suite with ID {suite_id} not found")
        except Exception as e:
            raise CommandError(f"Failed to run test suite: {str(e)}")
