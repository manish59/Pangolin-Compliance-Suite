#!/usr/bin/env python
"""
Generate test data for the test protocol application.

This script creates multiple test suites, protocols, environments, and connection configurations.
Designed to be run in a Django shell or as a Django management command.

Usage:
    python manage.py shell < generate_test_data.py
    # or
    python manage.py runscript generate_test_data
"""

import random
import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User

# Import your models
from projects.models import Project
from test_protocols.models import TestSuite, TestProtocol, ConnectionConfig, ExecutionStep, VerificationMethod
from environments.models import Environment

# Configuration
NUM_PROJECTS = 5
NUM_SUITES_PER_PROJECT = 3
NUM_PROTOCOLS_PER_SUITE = 5
NUM_STEPS_PER_PROTOCOL = 3
NUM_ENVIRONMENTS_PER_PROJECT = 10
NUM_VERIFICATIONS_PER_STEP = 2

# Sample data
CONNECTION_TYPES = ['database', 'api', 'ssh', 'kubernetes', 'aws', 'azure']
PROTOCOL_STATUSES = ['active', 'deprecated', 'draft', 'archived']
VERIFICATION_TYPES = [
    'string_exact_match', 'string_contains', 'numeric_equal',
    'numeric_range', 'api_status_code', 'db_row_count'
]
VARIABLE_TYPES = ['text', 'number', 'boolean', 'secret', 'json', 'url']

# Sample hosts for different connection types
HOSTS = {
    'database': ['postgres-db', 'mysql-server', 'oracle-db', 'mssql-server'],
    'api': ['api.example.com', 'rest.service.io', 'graphql.endpoint.org'],
    'ssh': ['server1.example.com', 'bastion.example.com', 'worker1.example.com'],
    'kubernetes': ['k8s-master', 'aks-cluster', 'eks-cluster', 'gke-cluster'],
    'aws': ['s3.amazonaws.com', 'ec2.amazonaws.com', 'rds.amazonaws.com'],
    'azure': ['blob.core.windows.net', 'database.azure.com', 'azurewebsites.net']
}

# Sample project names
PROJECT_NAMES = [
    "Data Pipeline", "Customer API", "Authentication Service",
    "Inventory System", "Payment Gateway", "Order Management",
    "Analytics Platform", "CRM Integration", "Security Compliance",
    "DevOps Automation"
]


def get_random_host(connection_type):
    """Get a random host for the given connection type."""
    hosts = HOSTS.get(connection_type, ['localhost'])
    return random.choice(hosts)


def get_random_port(connection_type):
    """Get a sensible port for the given connection type."""
    port_ranges = {
        'database': [1433, 3306, 5432, 1521],
        'api': [80, 443, 8080, 8443],
        'ssh': [22, 2222],
        'kubernetes': [6443, 8443, 10250],
        'aws': [443],
        'azure': [443]
    }
    ports = port_ranges.get(connection_type, [80, 443, 8080])
    return random.choice(ports)


def generate_connection_config(protocol, config_type):
    """Generate a connection configuration for a protocol."""
    host = get_random_host(config_type)
    port = get_random_port(config_type)

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


def generate_verification_method(step, name, method_type):
    """Generate a verification method for an execution step."""
    # Create different expected results based on verification type
    if 'string' in method_type:
        expected_result = {"result": "Expected string value"}
    elif 'numeric' in method_type:
        expected_result = {"result": random.randint(1, 100)}
    elif 'api_status_code' in method_type:
        expected_result = {"result": random.choice([200, 201, 204])}
    elif 'db_row_count' in method_type:
        expected_result = {"result": random.randint(1, 1000)}
    else:
        expected_result = {"result": "default_value"}

    # Determine if this type supports comparison
    supports_comparison = any(t in method_type for t in ['string', 'numeric', 'api_status', 'db_row'])

    # Choose a comparison method if applicable
    comparison_method = ''
    if supports_comparison:
        if 'string' in method_type:
            comparison_method = random.choice(['eq', 'contains', 'starts_with', 'ends_with'])
        elif 'numeric' in method_type:
            comparison_method = random.choice(['eq', 'gt', 'lt', 'gte', 'lte'])
        else:
            comparison_method = 'eq'  # Default to equals for other types

    # Create the verification method
    verification = VerificationMethod(
        execution_step=step,
        name=name,
        description=f"Verification for {name}",
        method_type=method_type,
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
    return verification


def generate_execution_step(protocol, index):
    """Generate an execution step for a protocol."""
    step_name = f"Step {index + 1}: {random.choice(['Prepare', 'Execute', 'Validate', 'Cleanup'])}"

    # Create different kwargs based on the step name
    if 'Prepare' in step_name:
        kwargs = {
            "setup": True,
            "initialize": random.choice([True, False]),
            "config": {
                "timeout": random.randint(10, 30),
                "retries": random.randint(1, 3)
            }
        }
    elif 'Execute' in step_name:
        kwargs = {
            "command": random.choice(["get_data", "process_items", "trigger_action"]),
            "parameters": {
                "limit": random.randint(10, 100),
                "filter": random.choice(["active", "pending", "completed"])
            }
        }
    elif 'Validate' in step_name:
        kwargs = {
            "validation_type": random.choice(["schema", "count", "content"]),
            "expected": {
                "status": random.choice(["success", "partial", "error"]),
                "count": random.randint(0, 1000)
            }
        }
    else:  # Cleanup
        kwargs = {
            "cleanup": True,
            "remove_temp_files": random.choice([True, False]),
            "reset_state": random.choice([True, False])
        }

    step = ExecutionStep(
        test_protocol=protocol,
        name=step_name,
        kwargs=kwargs
    )
    step.save()

    # Generate verification methods for this step
    for i in range(NUM_VERIFICATIONS_PER_STEP):
        verification_type = random.choice(VERIFICATION_TYPES)
        verification_name = f"Verify {verification_type.replace('_', ' ')} {i + 1}"
        generate_verification_method(step, verification_name, verification_type)

    return step


def generate_environment_variable(project, key_index):
    """Generate an environment variable for a project."""
    variable_type = random.choice(VARIABLE_TYPES)
    key = f"TEST_VAR_{key_index}"

    # Generate different values based on type
    if variable_type == 'text':
        value = f"text_value_{uuid.uuid4().hex[:8]}"
    elif variable_type == 'number':
        value = str(random.randint(1, 10000))
    elif variable_type == 'boolean':
        value = str(random.choice([True, False])).lower()
    elif variable_type == 'secret':
        value = f"secret_{uuid.uuid4().hex}"
    elif variable_type == 'json':
        value = '{"key": "value", "enabled": true, "count": 42}'
    elif variable_type == 'url':
        value = f"https://example.com/{uuid.uuid4().hex[:8]}"

    env_var = Environment(
        project=project,
        key=key,
        value=value,
        variable_type=variable_type,
        description=f"Test variable {key_index} of type {variable_type}",
        is_enabled=random.choice([True, False])
    )
    env_var.save()
    return env_var


def generate_test_protocol(suite, index):
    """Generate a test protocol for a suite."""
    status = random.choice(PROTOCOL_STATUSES)
    if status == 'active':
        # Weight the distribution to have more active protocols
        if random.random() < 0.7:
            status = 'active'

    protocol = TestProtocol(
        suite=suite,
        name=f"Protocol {index + 1}: {random.choice(['API Test', 'DB Verification', 'Config Check', 'System Health', 'Performance Test'])}",
        description=f"This is a test protocol {index + 1} for suite {suite.name}",
        status=status,
        order_index=index * 10  # Space them out for easy reordering
    )
    protocol.save()

    # Generate a connection config
    connection_type = random.choice(CONNECTION_TYPES)
    generate_connection_config(protocol, connection_type)

    # Generate execution steps
    for step_index in range(NUM_STEPS_PER_PROTOCOL):
        generate_execution_step(protocol, step_index)

    return protocol


def generate_test_suite(project, index):
    """Generate a test suite for a project."""
    suite = TestSuite(
        name=f"Suite {index + 1}: {random.choice(['Regression', 'Smoke', 'Integration', 'Performance', 'Security'])}",
        description=f"This is a test suite {index + 1} for project {project.name}",
        project=project
    )
    suite.save()

    # Generate test protocols for this suite
    for protocol_index in range(NUM_PROTOCOLS_PER_SUITE):
        generate_test_protocol(suite, protocol_index)

    return suite


@transaction.atomic
def generate_all_test_data():
    """Generate all test data."""
    print("Starting test data generation...")
    start_time = datetime.now()

    # Use existing projects or create new ones if none exist
    existing_projects = Project.objects.all()
    projects = []

    if existing_projects.exists():
        print(f"Using {min(NUM_PROJECTS, existing_projects.count())} existing projects")
        projects = list(existing_projects[:NUM_PROJECTS])

    # Create more projects if needed
    if len(projects) < NUM_PROJECTS:
        num_to_create = NUM_PROJECTS - len(projects)
        print(f"Creating {num_to_create} new projects")
        for i in range(num_to_create):
            project = Project(
                name=f"{random.choice(PROJECT_NAMES)} {i + 1}",
                description=f"Test project {i + 1}",
                status="active"
            )
            project.save()
            projects.append(project)

    # Generate test suites for each project
    for project in projects:
        print(f"Generating data for project: {project.name}")

        # Generate environment variables
        print(f"  Creating {NUM_ENVIRONMENTS_PER_PROJECT} environment variables")
        for env_index in range(NUM_ENVIRONMENTS_PER_PROJECT):
            generate_environment_variable(project, env_index)

        # Generate test suites
        print(f"  Creating {NUM_SUITES_PER_PROJECT} test suites")
        for suite_index in range(NUM_SUITES_PER_PROJECT):
            suite = generate_test_suite(project, suite_index)
            print(f"    Created suite: {suite.name} with {NUM_PROTOCOLS_PER_SUITE} protocols")

    end_time = datetime.now()
    print(f"Finished test data generation in {(end_time - start_time).total_seconds():.2f} seconds")

    # Print summary
    projects_count = Project.objects.count()
    suites_count = TestSuite.objects.count()
    protocols_count = TestProtocol.objects.count()
    steps_count = ExecutionStep.objects.count()
    verifications_count = VerificationMethod.objects.count()
    environments_count = Environment.objects.count()

    print("\nGenerated Data Summary:")
    print(f"Projects: {projects_count}")
    print(f"Test Suites: {suites_count}")
    print(f"Test Protocols: {protocols_count}")
    print(f"Execution Steps: {steps_count}")
    print(f"Verification Methods: {verifications_count}")
    print(f"Environment Variables: {environments_count}")


if __name__ == "__main__":
    # This allows the script to be run directly with manage.py
    generate_all_test_data()