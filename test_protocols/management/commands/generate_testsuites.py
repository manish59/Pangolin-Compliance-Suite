from django.core.management.base import BaseCommand
import random
from projects.models import Project
from test_protocols.models import TestSuite


class Command(BaseCommand):
    help = "Generate test suites for existing projects"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Number of test suites to create per project",
        )
        parser.add_argument(
            "--project-id",
            type=str,
            help="Specific project ID to generate test suites for",
        )

    def handle(self, *args, **options):
        count = options["count"]
        project_id = options.get("project_id")

        # Suite types for naming
        SUITE_TYPES = [
            "Regression",
            "Smoke",
            "Integration",
            "Performance",
            "Security",
            "Functional",
            "End-to-End",
            "API",
            "Database",
            "UI",
            "Acceptance",
            "Compatibility",
            "Load",
            "Stress",
            "Recovery",
            "Usability",
            "Accessibility",
            "Exploratory",
            "Sanity",
            "Component",
        ]

        if project_id:
            try:
                projects = [Project.objects.get(pk=project_id)]
                self.stdout.write(
                    f"Generating test suites for specific project: {projects[0].name}"
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
                f"Generating {count} test suites for project: {project.name}"
            )

            # Get existing suites to avoid duplicate names
            existing_suite_names = set(
                TestSuite.objects.filter(project=project).values_list("name", flat=True)
            )

            for i in range(count):
                # Try to create a unique name
                attempts = 0
                while attempts < 10:  # Limit attempts to avoid infinite loop
                    suite_type = random.choice(SUITE_TYPES)
                    name = f"{suite_type} Test Suite {i + 1}"
                    if name not in existing_suite_names:
                        break
                    attempts += 1

                description = (
                    f"This is a {suite_type.lower()} test suite for {project.name}"
                )

                # Create the test suite
                suite = TestSuite(name=name, description=description, project=project)
                suite.save()

                existing_suite_names.add(name)
                total_created += 1

                if (i + 1) % 5 == 0:
                    self.stdout.write(
                        f"  Created {i + 1} test suites for {project.name}"
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {count} test suites for project {project.name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Total test suites created: {total_created}")
        )
