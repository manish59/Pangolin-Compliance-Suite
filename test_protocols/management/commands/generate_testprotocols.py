from django.core.management.base import BaseCommand
import random
import uuid
from test_protocols.models import TestSuite, TestProtocol, ConnectionConfig, ExecutionStep, VerificationMethod


class Command(BaseCommand):
    help = 'Generate test protocols for existing test suites'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='Number of protocols to create per test suite')
        parser.add_argument('--suite-id', type=str, help='Specific test suite ID to generate protocols for')
        parser.add_argument('--steps', type=int, default=3, help='Number of execution steps per protocol')
        parser.add_argument('--verifications', type=int, default=2, help='Number of verification methods per step')

    def handle(self, *args, **options):
        count = options['count']
        suite_id = options.get('suite_id')
        steps_count = options['steps']
        verifications_count = options['verifications']

        # Protocol types and related information
        PROTOCOL_STATUSES = ['active', 'deprecated', 'draft', 'archived']
        PROTOCOL_TYPES = [
            'API Test', 'DB Verification', 'Config Check', 'System Health',
            'Performance Test', 'Security Scan', 'Data Validation',
            'Integration Test', 'Infrastructure Test', 'CI/CD Verification'
        ]
        CONNECTION_TYPES = ['database', 'api', 'ssh', 'kubernetes', 'aws', 'azure']
        VERIFICATION_TYPES = [
            'string_exact_match', 'string_contains', 'numeric_equal',
            'numeric_range', 'api_status_code', 'db_row_count',
            'string_regex_match', 'dict_has_keys', 'list_length',
            'api_response_time', 'db_query_result'
        ]

        if suite_id:
            try:
                suites = [TestSuite.objects.get(pk=suite_id)]
                self.stdout.write(f"Generating protocols for specific test suite: {suites[0].name}")
            except TestSuite.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Test suite with ID {suite_id} not found"))
                return
        else:
            suites = TestSuite.objects.all()
            if not suites.exists():
                self.stdout.write(self.style.ERROR("No test suites found. Please create a test suite first."))
                return

        total_protocols = 0
        total_steps = 0
        total_verifications = 0
        total_connections = 0

        for suite in suites:
            self.stdout.write(f"Generating {count} protocols for test suite: {suite.name}")

            # Get existing protocol names to avoid duplicates
            existing_protocol_names = set(TestProtocol.objects.filter(suite=suite).values_list('name', flat=True))

            for i in range(count):
                # Create a unique name
                attempts = 0
                while attempts < 10:  # Limit attempts to avoid infinite loop
                    protocol_type = random.choice(PROTOCOL_TYPES)
                    name = f"Protocol {i + 1}: {protocol_type}"
                    if name not in existing_protocol_names:
                        break
                    attempts += 1

                # Bias towards active status
                status = random.choice(PROTOCOL_STATUSES)
                if random.random() < 0.7:  # 70% chance to be active
                    status = 'active'

                description = f"This is a test protocol for {suite.name} ({protocol_type})"

                # Create the protocol
                protocol = TestProtocol(
                    suite=suite,
                    name=name,
                    description=description,
                    status=status,
                    order_index=i * 10  # Space them out for easy reordering
                )
                protocol.save()
                existing_protocol_names.add(name)
                total_protocols += 1

                # Generate connection config
                connection_type = random.choice(CONNECTION_TYPES)
                self._create_connection_config(protocol, connection_type)
                total_connections += 1

                # Generate execution steps
                step_verifications = self._create_execution_steps(protocol, steps_count, verifications_count)
                total_steps += steps_count
                total_verifications += step_verifications

                if (i + 1) % 5 == 0:
                    self.stdout.write(f"  Created {i + 1} protocols for {suite.name}")

            self.stdout.write(self.style.SUCCESS(f"Successfully created {count} protocols for test suite {suite.name}"))

        self.stdout.write(self.style.SUCCESS(
            f"Total created: {total_protocols} protocols, {total_connections} connections, {total_steps} steps, {total_verifications} verifications"))

    def _create_connection_config(self, protocol, config_type):
        """Create a connection configuration for a protocol."""
        # Sample hosts for different connection types
        HOSTS = {
            'database': ['postgres-db', 'mysql-server', 'oracle-db', 'mssql-server'],
            'api': ['api.example.com', 'rest.service.io', 'graphql.endpoint.org'],
            'ssh': ['server1.example.com', 'bastion.example.com', 'worker1.example.com'],
            'kubernetes': ['k8s-master', 'aks-cluster', 'eks-cluster', 'gke-cluster'],
            'aws': ['s3.amazonaws.com', 'ec2.amazonaws.com', 'rds.amazonaws.com'],
            'azure': ['blob.core.windows.net', 'database.azure.com', 'azurewebsites.net']
        }

        # Port ranges for different connection types
        PORT_RANGES = {
            'database': [1433, 3306, 5432, 1521],
            'api': [80, 443, 8080, 8443],
            'ssh': [22, 2222],
            'kubernetes': [6443, 8443, 10250],
            'aws': [443],
            'azure': [443]
        }

        host = random.choice(HOSTS.get(config_type, ['localhost']))
        port = random.choice(PORT_RANGES.get(config_type, [80, 443, 8080]))

        # Create different config_data based on connection type
        if config_type == 'database':
            config_data = {
                'database_type': random.choice(['postgresql', 'mysql', 'oracle', 'mssql']),
                'database': f"test_db_{uuid.uuid4().hex[:8]}",
                'username': 'db_user',
                'password': '${DB_PASSWORD}',  # Reference to an environment variable
                'options': {
                    'ssl': random.choice([True, False]),
                    'timeout': random.randint(10, 60)
                }
            }
        elif config_type == 'api':
            config_data = {
                'auth_method': random.choice(['none', 'basic', 'bearer', 'api_key']),
                'api_key_name': 'X-API-Key',
                'api_key_location': 'header',
                'default_headers': {
                    'Accept': 'application/json',
                    'User-Agent': 'TestAutomation/1.0'
                }
            }
        elif config_type == 'ssh':
            config_data = {
                'auth_method': random.choice(['password', 'publickey']),
                'username': 'ssh_user',
                'private_key': '/path/to/key' if random.choice([True, False]) else None
            }
        elif config_type == 'kubernetes':
            config_data = {
                'auth_method': random.choice(['config', 'token']),
                'namespace': random.choice(['default', 'app', 'monitoring']),
                'verify_ssl': random.choice([True, False])
            }
        elif config_type == 'aws':
            config_data = {
                'auth_method': random.choice(['access_key', 'profile', 'instance_role']),
                'service': random.choice(['s3', 'ec2', 'rds', 'lambda']),
                'region': random.choice(['us-east-1', 'us-west-2', 'eu-west-1'])
            }
        else:  # azure
            config_data = {
                'auth_method': random.choice(['service_principal', 'managed_identity']),
                'tenant_id': f"{uuid.uuid4()}",
                'subscription_id': f"{uuid.uuid4()}",
                'resource_group': f"rg-{random.choice(['dev', 'test', 'prod'])}"
            }

        connection = ConnectionConfig(
            protocol=protocol,
            config_type=config_type,
            timeout_seconds=random.randint(10, 120),
            retry_attempts=random.randint(1, 5),
            config_data=config_data
        )
        connection.save()
        return connection

    def _create_execution_steps(self, protocol, steps_count, verifications_count):
        """Create execution steps and verification methods for a protocol."""
        total_verifications = 0

        # Step types
        STEP_TYPES = ['Prepare', 'Execute', 'Validate', 'Cleanup', 'Initialize', 'Analyze', 'Export']

        for i in range(steps_count):
            step_type = random.choice(STEP_TYPES)
            step_name = f"Step {i + 1}: {step_type}"

            # Create different kwargs based on the step type
            if step_type == 'Prepare':
                kwargs = {
                    "setup": True,
                    "initialize": random.choice([True, False]),
                    "config": {
                        "timeout": random.randint(10, 30),
                        "retries": random.randint(1, 3)
                    }
                }
            elif step_type == 'Execute':
                kwargs = {
                    "command": random.choice(["get_data", "process_items", "trigger_action"]),
                    "parameters": {
                        "limit": random.randint(10, 100),
                        "filter": random.choice(["active", "pending", "completed"])
                    }
                }
            elif step_type == 'Validate':
                kwargs = {
                    "validation_type": random.choice(["schema", "count", "content"]),
                    "expected": {
                        "status": random.choice(["success", "partial", "error"]),
                        "count": random.randint(0, 1000)
                    }
                }
            elif step_type == 'Cleanup':
                kwargs = {
                    "cleanup": True,
                    "remove_temp_files": random.choice([True, False]),
                    "reset_state": random.choice([True, False])
                }
            elif step_type == 'Initialize':
                kwargs = {
                    "create_resources": random.choice([True, False]),
                    "environment": random.choice(["dev", "test", "prod"]),
                    "debug": random.choice([True, False])
                }
            elif step_type == 'Analyze':
                kwargs = {
                    "analyze": True,
                    "metrics": ["response_time", "error_rate", "throughput"],
                    "thresholds": {
                        "response_time_ms": random.randint(100, 5000),
                        "error_rate_percent": random.uniform(0, 5),
                        "min_throughput": random.randint(10, 1000)
                    }
                }
            else:  # Export
                kwargs = {
                    "export": True,
                    "format": random.choice(["json", "csv", "xml", "yaml"]),
                    "destination": f"s3://bucket/results/{uuid.uuid4().hex}.json",
                    "include_metadata": random.choice([True, False])
                }

            step = ExecutionStep(
                test_protocol=protocol,
                name=step_name,
                kwargs=kwargs
            )
            step.save()

            # Add verification methods to this step
            step_verifications = self._create_verification_methods(step, verifications_count)
            total_verifications += step_verifications

        return total_verifications

    def _create_verification_methods(self, step, count):
        """Create verification methods for an execution step."""
        # Verification types
        VERIFICATION_TYPES = [
            'string_exact_match', 'string_contains', 'numeric_equal',
            'numeric_range', 'api_status_code', 'db_row_count',
            'string_regex_match', 'dict_has_keys', 'list_length',
            'api_response_time', 'db_query_result'
        ]

        total_created = 0

        for i in range(count):
            verification_type = random.choice(VERIFICATION_TYPES)
            verification_name = f"Verify {verification_type.replace('_', ' ')} {i + 1}"

            # Create different expected results based on verification type
            if 'string' in verification_type:
                expected_result = {"result": "Expected string value"}
            elif 'numeric' in verification_type:
                expected_result = {"result": random.randint(1, 100)}
            elif 'api_status_code' in verification_type:
                expected_result = {"result": random.choice([200, 201, 204])}
            elif 'db_row_count' in verification_type:
                expected_result = {"result": random.randint(1, 1000)}
            elif 'dict_has_keys' in verification_type:
                expected_result = {"result": ["id", "name", "status"]}
            elif 'list_length' in verification_type:
                expected_result = {"result": random.randint(1, 50)}
            else:
                expected_result = {"result": "default_value"}

            # Determine if this type supports comparison
            supports_comparison = any(t in verification_type for t in ['string', 'numeric', 'api_status', 'db_row'])

            # Choose a comparison method if applicable
            comparison_method = ''
            if supports_comparison:
                if 'string' in verification_type:
                    comparison_method = random.choice(['eq', 'contains', 'starts_with', 'ends_with'])
                elif 'numeric' in verification_type:
                    comparison_method = random.choice(['eq', 'gt', 'lt', 'gte', 'lte'])
                else:
                    comparison_method = 'eq'  # Default to equals for other types

            # Create the verification method
            verification = VerificationMethod(
                execution_step=step,
                name=verification_name,
                description=f"Verification method to {verification_type.replace('_', ' ')} for step: {step.name}",
                method_type=verification_type,
                supports_comparison=supports_comparison,
                comparison_method=comparison_method,
                expected_result=expected_result,
                requires_expected_value=random.choice([True, False]),
                supports_dynamic_expected=random.choice([True, False]),
                config_schema={
                    "type": "object",
                    "properties": {
                        "timeout": {"type": "number"},
                        "retry": {"type": "boolean"}
                    }
                }
            )
            verification.save()
            total_created += 1

        return total_created