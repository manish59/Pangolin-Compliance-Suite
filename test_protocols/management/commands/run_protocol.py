# test_protocols/management/commands/run_protocol.py
import uuid
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from test_protocols.models import TestProtocol
from test_protocols.services import trigger_protocol_run


class Command(BaseCommand):
    help = "Run a test protocol by ID"

    def add_arguments(self, parser):
        parser.add_argument(
            "protocol_id", type=str, help="The UUID of the protocol to run"
        )
        parser.add_argument("--user", type=str, help="Username to attribute the run to")

    def handle(self, *args, **options):
        protocol_id = options["protocol_id"]
        username = options.get("user")

        try:
            # Parse the protocol ID as a UUID
            protocol_id = uuid.UUID(protocol_id)
        except ValueError:
            raise CommandError(f"Invalid protocol ID: {protocol_id}")

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
            # Get the protocol
            protocol = TestProtocol.objects.get(id=protocol_id)
            self.stdout.write(self.style.SUCCESS(f"Found protocol: {protocol.name}"))

            # Trigger the protocol run
            protocol_run = trigger_protocol_run(protocol_id, user)

            self.stdout.write(
                self.style.SUCCESS(f"Protocol run initiated with ID: {protocol_run.id}")
            )

        except TestProtocol.DoesNotExist:
            raise CommandError(f"Protocol with ID {protocol_id} not found")
        except Exception as e:
            raise CommandError(f"Failed to run protocol: {str(e)}")
