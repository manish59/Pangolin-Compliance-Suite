from celery import shared_task
import time
import logging
import json
from datetime import datetime

from django.utils import timezone
from test_protocols.models import (
    TestProtocol,
    TestSuite,
    ProtocolRun,
    ProtocolResult,
    ConnectionConfig,
    VerificationMethod
)

# Import Pangolin SDK modules
from pangolin_sdk.constants import (
    DatabaseType,
    ConnectionStatus,
    HTTPVerb,
    AuthMethod,
    SSHAuthMethod,
    KubernetesAuthMethod,
    AWSAuthMethod,
    AWSService,
    AWSRegion
)

# Import connection classes
from pangolin_sdk.connections.database import DatabaseConnection
from pangolin_sdk.connections.api import APIConnection
from pangolin_sdk.connections.ssh import SSHConnection
from pangolin_sdk.connections.kubernetes import KubernetesConnection
from pangolin_sdk.connections.aws import AWSConnection

# Import configuration classes
from pangolin_sdk.configs.database import DatabaseConnectionConfig
from pangolin_sdk.configs.api import APIConfig
from pangolin_sdk.configs.ssh import SSHConnectionConfig
from pangolin_sdk.configs.kubernetes import KubernetesConnectionConfig
from pangolin_sdk.configs.aws import AWSConnectionConfig

# Import exceptions
from pangolin_sdk.exceptions import (
    BaseConnectionError,
    BaseExecutionError,
    DatabaseConnectionError,
    APIConnectionError,
    SSHConnectionError
)

logger = logging.getLogger(__name__)


def create_connection(connection_config):
    """
    Create a connection object based on the ConnectionConfig model.

    Args:
        connection_config: The ConnectionConfig model instance containing configuration details

    Returns:
        A connection object for the appropriate service type

    Raises:
        ValueError: If connection type is not supported
    """
    # Get environment variables from the ConnectionConfig
    env_vars = {}
    if connection_config.username:
        env_vars['username'] = connection_config.username.get_actual_value()
    if connection_config.password:
        env_vars['password'] = connection_config.password.get_actual_value()
    if connection_config.secret_key:
        env_vars['secret_key'] = connection_config.secret_key.get_actual_value()

    # Get custom config data for each connection type
    config_data = connection_config.config_data or {}

    if connection_config.config_type == 'database':
        # Create database connection
        db_type = config_data.get('database_type', 'postgresql')

        # Map string to DatabaseType enum
        db_type_map = {
            'postgresql': DatabaseType.POSTGRESQL,
            'mysql': DatabaseType.MYSQL,
            'oracle': DatabaseType.ORACLE,
            'mssql': DatabaseType.MSSQL,
            'sqlite': DatabaseType.SQLITE
        }

        db_config = DatabaseConnectionConfig(
            name=f"db_connection_{connection_config.id}",
            host=connection_config.host,
            port=connection_config.port,
            database=config_data.get('database'),
            username=env_vars.get('username'),
            password=env_vars.get('password'),
            database_type=db_type_map.get(db_type, DatabaseType.POSTGRESQL),
            timeout=connection_config.timeout_seconds,
            max_retries=connection_config.retry_attempts,
            options=config_data.get('options', {})
        )

        return DatabaseConnection(db_config)

    elif connection_config.config_type == 'api':
        # Create API connection
        auth_method_str = config_data.get('auth_method', 'none')

        # Map string to AuthMethod enum
        auth_method_map = {
            'none': AuthMethod.NONE,
            'basic': AuthMethod.BASIC,
            'bearer': AuthMethod.BEARER,
            'jwt': AuthMethod.JWT,
            'api_key': AuthMethod.API_KEY,
            'oauth2': AuthMethod.OAUTH2,
            'digest': AuthMethod.DIGEST,
            'hmac': AuthMethod.HMAC
        }

        api_config = APIConfig(
            name=f"api_connection_{connection_config.id}",
            host=connection_config.host,
            port=connection_config.port,
            username=env_vars.get('username'),
            password=env_vars.get('password'),
            auth_method=auth_method_map.get(auth_method_str, AuthMethod.NONE),
            auth_token=env_vars.get('secret_key'),
            timeout=connection_config.timeout_seconds,
            max_retries=connection_config.retry_attempts,
            # Additional API-specific configurations
            api_key=config_data.get('api_key'),
            api_key_name=config_data.get('api_key_name'),
            api_key_location=config_data.get('api_key_location', 'header'),
            default_headers=config_data.get('default_headers', {})
        )

        return APIConnection(api_config)

    elif connection_config.config_type == 'ssh':
        # Create SSH connection
        auth_method_str = config_data.get('auth_method', 'password')

        # Map string to SSHAuthMethod enum
        auth_method_map = {
            'password': SSHAuthMethod.PASSWORD,
            'publickey': SSHAuthMethod.PUBLIC_KEY,
            'agent': SSHAuthMethod.AGENT
        }

        ssh_config = SSHConnectionConfig(
            name=f"ssh_connection_{connection_config.id}",
            host=connection_config.host,
            port=connection_config.port,
            username=env_vars.get('username'),
            password=env_vars.get('password'),
            auth_method=auth_method_map.get(auth_method_str, SSHAuthMethod.PASSWORD),
            private_key=config_data.get('private_key'),
            passphrase=env_vars.get('secret_key'),
            timeout=connection_config.timeout_seconds,
            max_retries=connection_config.retry_attempts
        )

        return SSHConnection(ssh_config)

    elif connection_config.config_type == 'kubernetes':
        # Create Kubernetes connection
        auth_method_str = config_data.get('auth_method', 'config')

        # Map string to KubernetesAuthMethod enum
        auth_method_map = {
            'config': KubernetesAuthMethod.CONFIG,
            'token': KubernetesAuthMethod.TOKEN,
            'certificate': KubernetesAuthMethod.CERTIFICATE,
            'basic': KubernetesAuthMethod.BASIC
        }

        k8s_config = KubernetesConnectionConfig(
            name=f"k8s_connection_{connection_config.id}",
            host=connection_config.host,
            port=connection_config.port,
            username=env_vars.get('username'),
            password=env_vars.get('password'),
            auth_method=auth_method_map.get(auth_method_str, KubernetesAuthMethod.CONFIG),
            api_token=env_vars.get('secret_key'),
            kubeconfig_path=config_data.get('kubeconfig_path'),
            namespace=config_data.get('namespace', 'default'),
            verify_ssl=config_data.get('verify_ssl', True),
            timeout=connection_config.timeout_seconds,
            max_retries=connection_config.retry_attempts
        )

        return KubernetesConnection(k8s_config)

    elif connection_config.config_type == 'aws':
        # Create AWS connection
        auth_method_str = config_data.get('auth_method', 'access_key')
        service_str = config_data.get('service', 's3')
        region_str = config_data.get('region', 'us-east-1')

        # Map strings to enums
        auth_method_map = {
            'access_key': AWSAuthMethod.ACCESS_KEY,
            'profile': AWSAuthMethod.PROFILE,
            'instance_role': AWSAuthMethod.INSTANCE_ROLE,
            'web_identity': AWSAuthMethod.WEB_IDENTITY,
            'sso': AWSAuthMethod.SSO
        }

        service_map = {
            's3': AWSService.S3,
            'ec2': AWSService.EC2,
            'rds': AWSService.RDS,
            'lambda': AWSService.LAMBDA,
            'dynamodb': AWSService.DYNAMODB
        }

        region_map = {
            'us-east-1': AWSRegion.US_EAST_1,
            'us-east-2': AWSRegion.US_EAST_2,
            'us-west-1': AWSRegion.US_WEST_1,
            'us-west-2': AWSRegion.US_WEST_2,
            'eu-west-1': AWSRegion.EU_WEST_1
        }

        aws_config = AWSConnectionConfig(
            name=f"aws_connection_{connection_config.id}",
            host=connection_config.host,
            auth_method=auth_method_map.get(auth_method_str, AWSAuthMethod.ACCESS_KEY),
            service=service_map.get(service_str, AWSService.S3),
            region=region_map.get(region_str, AWSRegion.US_EAST_1),
            access_key_id=env_vars.get('username'),
            secret_access_key=env_vars.get('password'),
            session_token=env_vars.get('secret_key'),
            timeout=connection_config.timeout_seconds,
            max_retries=connection_config.retry_attempts
        )

        return AWSConnection(aws_config)

    else:
        raise ValueError(f"Unsupported connection type: {connection_config.config_type}")


@shared_task(queue='protocol_queue')
def run_test_protocol(protocol_id, user_id=None):
    """
    Runs a single test protocol.
    This task is processed by the protocol worker.

    Args:
        protocol_id: UUID of the TestProtocol to run
        user_id: Optional user ID who initiated the run

    Returns:
        Dictionary containing run results
    """
    try:
        # Get the protocol
        protocol = TestProtocol.objects.get(id=protocol_id)

        # Create a run record
        run = ProtocolRun.objects.create(
            protocol=protocol,
            status='running',
            executed_by=f"User {user_id}" if user_id else "System"
        )

        logger.info(f"Starting test protocol run: {protocol.name} (ID: {protocol_id})")
        start_time = time.time()

        # Initialize variables to store execution results
        test_results = {}
        connection = None
        success = False
        error_message = None
        result_data = {}
        result_text = ""

        try:
            # Check if protocol has a connection configuration
            try:
                connection_config = protocol.connection_config

                # Create connection object from the configuration
                connection = create_connection(connection_config)

                # Establish connection
                connection.connect()

                if connection.get_status() != ConnectionStatus.CONNECTED:
                    raise ConnectionError(f"Failed to connect to {connection_config.config_type} service")

                # Execute the test - this will depend on the connection type
                if connection_config.config_type == 'database':
                    # Example database test
                    query = "SELECT 1 as test_value"
                    if 'query' in connection_config.config_data:
                        query = connection_config.config_data['query']

                    test_results = connection.execute(query)
                    result_text = f"Database query executed successfully. Results: {len(test_results)} rows"
                    result_data = {"rows": test_results}

                elif connection_config.config_type == 'api':
                    # Example API test
                    endpoint = ""
                    method = "GET"
                    params = {}
                    data = {}
                    headers = {}

                    if 'endpoint' in connection_config.config_data:
                        endpoint = connection_config.config_data['endpoint']
                    if 'method' in connection_config.config_data:
                        method = connection_config.config_data['method']
                    if 'params' in connection_config.config_data:
                        params = connection_config.config_data['params']
                    if 'data' in connection_config.config_data:
                        data = connection_config.config_data['data']
                    if 'headers' in connection_config.config_data:
                        headers = connection_config.config_data['headers']

                    test_results = connection.execute(method=method, endpoint=endpoint, params=params, data=data,
                                                      headers=headers)
                    result_text = f"API test executed successfully. Status code: {test_results.get('status_code')}"
                    result_data = test_results

                elif connection_config.config_type == 'ssh':
                    # Example SSH test
                    command = "echo 'Hello, Pangolin!'"
                    if 'command' in connection_config.config_data:
                        command = connection_config.config_data['command']

                    test_results = connection.execute(command)
                    result_text = f"SSH command executed successfully. Output: {test_results}"
                    result_data = {"output": test_results}

                elif connection_config.config_type == 'kubernetes':
                    # Example Kubernetes test
                    resource_type = "pod"  # Default to pod
                    action = "list"  # Default to list
                    namespace = "default"

                    if 'resource_type' in connection_config.config_data:
                        resource_type = connection_config.config_data['resource_type']
                    if 'action' in connection_config.config_data:
                        action = connection_config.config_data['action']
                    if 'namespace' in connection_config.config_data:
                        namespace = connection_config.config_data['namespace']

                    test_results = connection.execute(resource_type=resource_type, action=action, namespace=namespace)
                    result_text = f"Kubernetes operation executed successfully"
                    result_data = test_results

                elif connection_config.config_type == 'aws':
                    # Example AWS test
                    operation = "list_buckets"  # Default operation for S3
                    service_params = {}

                    if 'operation' in connection_config.config_data:
                        operation = connection_config.config_data['operation']
                    if 'params' in connection_config.config_data:
                        service_params = connection_config.config_data['params']

                    test_results = connection.execute(operation=operation, **service_params)
                    result_text = f"AWS operation executed successfully"
                    result_data = test_results

                # Apply verification methods if configured
                verification_methods = protocol.verification_methods.filter(test_protocol=protocol)
                if verification_methods.exists():
                    verification_results = []
                    for verification in verification_methods:
                        # Apply verification method - simplified for example
                        verification_result = {
                            "name": verification.name,
                            "method": verification.method_type,
                            "success": True,  # Default success
                            "message": "Verification passed"
                        }

                        # TODO: Implement actual verification logic based on method_type

                        verification_results.append(verification_result)

                    result_data["verifications"] = verification_results
                    all_verifications_passed = all(vr["success"] for vr in verification_results)
                    success = all_verifications_passed
                else:
                    # Without verifications, just mark as success if we got this far
                    success = True

            except ConnectionError as e:
                # Handle connection errors
                error_message = f"Connection error: {str(e)}"
                success = False
                result_text = f"Failed to connect to {connection_config.config_type} service: {str(e)}"
                logger.error(error_message)

            except Exception as e:
                # Handle all other errors during execution
                error_message = f"Execution error: {str(e)}"
                success = False
                result_text = f"Error during test execution: {str(e)}"
                logger.error(error_message)

        finally:
            # Close connection if it was opened
            if connection and connection.get_status() == ConnectionStatus.CONNECTED:
                try:
                    connection.disconnect()
                except Exception as e:
                    logger.warning(f"Error disconnecting: {str(e)}")

        # Calculate duration
        end_time = time.time()
        duration = end_time - start_time

        # Create a result record
        result = ProtocolResult.objects.create(
            run=run,
            success=success,
            result_data=result_data,
            result_text=result_text,
            error_message=error_message
        )

        # Update the run record
        run.status = 'completed'
        run.result_status = 'pass' if success else 'fail'
        run.completed_at = timezone.now()
        run.duration_seconds = duration
        run.error_message = error_message
        run.save()

        logger.info(f"Completed test protocol run: {protocol.name} in {duration:.2f}s - Success: {success}")

        return {
            'protocol_id': str(protocol_id),
            'run_id': str(run.id),
            'success': success,
            'duration': duration,
            'error_message': error_message
        }

    except Exception as e:
        logger.error(f"Error running test protocol {protocol_id}: {str(e)}")

        # If we already created a run record, update it with the error
        try:
            if 'run' in locals():
                run.status = 'error'
                run.result_status = 'error'
                run.error_message = str(e)
                run.completed_at = timezone.now()
                if 'start_time' in locals():
                    run.duration_seconds = time.time() - start_time
                run.save()

                # Create error result if needed
                if not hasattr(run, 'result'):
                    ProtocolResult.objects.create(
                        run=run,
                        success=False,
                        error_message=str(e),
                        result_text=f"Error: {str(e)}"
                    )
        except Exception as inner_e:
            logger.error(f"Error updating run record: {str(inner_e)}")

        # Re-raise the exception
        raise


@shared_task(queue='suite_queue')
def run_test_suite(suite_id, user_id=None):
    """
    Runs all protocols in a test suite.
    This task is processed by the suite worker.

    Args:
        suite_id: UUID of the TestSuite to run
        user_id: Optional user ID who initiated the run

    Returns:
        Dictionary containing run results summary
    """
    try:
        # Get the suite
        suite = TestSuite.objects.get(id=suite_id)

        logger.info(f"Starting test suite: {suite.name} (ID: {suite_id})")
        start_time = time.time()

        # Get ordered protocols in the suite
        protocols = suite.get_ordered_protocols()

        # Track results
        results = {
            'total': len(protocols),
            'succeeded': 0,
            'failed': 0,
            'errors': 0,
            'protocol_results': []
        }

        # Run each protocol in sequence - directly call the function instead of using apply_async
        for protocol in protocols:
            try:
                # Call the function directly (still goes through Celery's task system)
                protocol_result = run_test_protocol(str(protocol.id), user_id)

                # Track success/failure
                if protocol_result['success']:
                    results['succeeded'] += 1
                else:
                    results['failed'] += 1

                results['protocol_results'].append(protocol_result)

            except Exception as e:
                logger.error(f"Error running protocol {protocol.id} in suite {suite_id}: {str(e)}")
                results['errors'] += 1
                results['protocol_results'].append({
                    'protocol_id': str(protocol.id),
                    'success': False,
                    'error': str(e)
                })

        # Calculate duration
        duration = time.time() - start_time
        results['duration'] = duration

        logger.info(f"Completed test suite: {suite.name} in {duration:.2f}s - "
                    f"Success: {results['succeeded']}/{results['total']}")

        return results

    except Exception as e:
        logger.error(f"Error running test suite {suite_id}: {str(e)}")
        raise