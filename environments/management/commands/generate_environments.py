from django.core.management.base import BaseCommand
import random
import uuid
from environments.models import Environment
from projects.models import Project


class Command(BaseCommand):
    help = "Generate test environment variables for existing projects"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=20,
            help="Number of environment variables to create per project",
        )
        parser.add_argument(
            "--project-id",
            type=str,
            help="Specific project ID to generate environments for",
        )

    def handle(self, *args, **options):
        count = options["count"]
        project_id = options.get("project_id")

        # Variable types available in the Environment model
        VARIABLE_TYPES = ["text", "number", "boolean", "secret", "json", "url", "file"]

        if project_id:
            try:
                projects = [Project.objects.get(pk=project_id)]
                self.stdout.write(
                    f"Generating environments for specific project: {projects[0].name}"
                )
            except Project.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Project with ID {project_id} not found")
                )
                return
        else:
            projects = Project.objects.all()
            if not projects.exists():
                self.stdout.write(
                    self.style.ERROR(
                        "No projects found. Please create a project first."
                    )
                )
                return

        total_created = 0

        for project in projects:
            self.stdout.write(
                f"Generating {count} environment variables for project: {project.name}"
            )

            for i in range(count):
                variable_type = random.choice(VARIABLE_TYPES)
                key = f"ENV_VAR_{variable_type.upper()}_{uuid.uuid4().hex[:8]}"

                # Generate different values based on type
                if variable_type == "text":
                    value = f"text_value_{uuid.uuid4().hex[:8]}"
                elif variable_type == "number":
                    value = str(random.randint(1, 10000))
                elif variable_type == "boolean":
                    value = str(random.choice([True, False])).lower()
                elif variable_type == "secret":
                    value = f"secret_{uuid.uuid4().hex}"
                elif variable_type == "json":
                    value = '{"key": "value", "enabled": true, "count": 42}'
                elif variable_type == "url":
                    value = f"https://example.com/{uuid.uuid4().hex[:8]}"
                elif variable_type == "file":
                    # For file type, we can't easily create a real file, just set a placeholder
                    value = ""  # The file content would be stored in file_content field

                description = f"Test environment variable {i + 1} of type {variable_type} for project {project.name}"

                # Create the environment variable
                env = Environment(
                    project=project,
                    key=key,
                    value=value,
                    variable_type=variable_type,
                    description=description,
                    is_enabled=random.choice([True, False]),
                    file_name=f"file_{i}.txt" if variable_type == "file" else None,
                    file_type="text/plain" if variable_type == "file" else None,
                )

                # If it's a secret type, ensure it's properly flagged
                if variable_type == "secret":
                    env._is_encrypted = True

                env.save()
                total_created += 1

                if (i + 1) % 10 == 0:
                    self.stdout.write(
                        f"  Created {i + 1} environment variables for {project.name}"
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {count} environment variables for project {project.name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Total environment variables created: {total_created}")
        )
