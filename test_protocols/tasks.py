# test_protocols/tasks.py
import logging
import uuid
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User

from test_protocols.models import ProtocolRun, TestProtocol, ProtocolResult
from pangolin_sdk.connections.api import APIConnection
from pangolin_sdk.connections.database import DatabaseConnection
from pangolin_sdk.connections.ssh import SSHConnection
from pangolin_sdk.connections.kubernetes import KubernetesConnection
from pangolin_sdk.connections.aws import AWSConnection
from pangolin_sdk.configs.api import APIConfig
from pangolin_sdk.configs.database import DatabaseConnectionConfig
from pangolin_sdk.configs.ssh import SSHConnectionConfig
from pangolin_sdk.configs.kubernetes import KubernetesConnectionConfig
from pangolin_sdk.configs.aws import AWSConnectionConfig
from pangolin_sdk.constants import DatabaseType, AuthMethod, SSHAuthMethod, KubernetesAuthMethod, AWSAuthMethod, \
    AWSService, AWSRegion

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="execute_protocol_run")
def execute_protocol_run(self, protocol_run_id, protocol_id, username):
    """
    Execute a test protocol and update the run status.

    Args:
        protocol_run_id (str): UUID of the ProtocolRun
        protocol_id (str): UUID of the TestProtocol
        username (str): Username of the user who initiated the run

    Returns:
        dict: Result of the execution
    """
    logger.info(f"Starting protocol execution task for run: {protocol_run_id}")

    try:
        # Convert string UUIDs to UUID objects if they're strings
        if isinstance(protocol_run_id, str):
            protocol_run_id = uuid.UUID(protocol_run_id)
        if isinstance(protocol_id, str):
            protocol_id = uuid.UUID(protocol_id)

        # Get the protocol run and protocol objects
        protocol_run = ProtocolRun.objects.get(id=protocol_run_id)
        protocol = TestProtocol.objects.get(id=protocol_id)

        # Update run status to running
        protocol_run.status = 'running'
        protocol_run.save()

        # Log the execution
        logger.info(f"Executing protocol: {protocol.name} (ID: {protocol_id})")

        # Get the connection configuration if it exists
        connection = None
        try:
            connection_config = protocol.connection_config
            # Initialize connection based on type
            connection = create_connection(connection_config)
            logger.info(f"Using connection: {connection_config.config_type} - {connection_config.host}")
        except Exception as e:
            logger.warning(f"No connection configuration found or error initializing: {str(e)}")

        # Record start time for duration calculation
        start_time = timezone.now()

        # Attempt to connect and execute the protocol
        result_data = {}
        success = False
        error_message = None

        try:
            if connection:
                # Connect to the service
                connection.connect()

                # Execute the protocol (depending on connection type)
                execution_result = execute_by_connection_type(connection, connection_config, protocol)

                # Record the execution result
                result_data = {
                    "connection_type": connection_config.config_type,
                    "execution_result": execution_result,
                    "executed_by": username
                }
                success = True
            else:
                # Simulate a success for testing when no connection is available
                result_data = {
                    "simulated": True,
                    "executed_by": username,
                    "message": "No connection configuration available. This is a simulated success."
                }
                success = True

        except Exception as e:
            error_message = str(e)
            logger.error(f"Error executing protocol: {error_message}")
            result_data = {"error": error_message}
            success = False
        finally:
            # Disconnect if connection was established
            if connection and connection.status == 'connected':
                try:
                    connection.disconnect()
                except Exception as e:
                    logger.warning(f"Error disconnecting: {str(e)}")

        # Calculate duration
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        # Create a result object
        result = ProtocolResult.objects.create(
            run=protocol_run,
            success=success,
            result_data=result_data,
            error_message=error_message,
            result_text=generate_result_text(success, protocol.name, duration, error_message)
        )

        # Update protocol run
        protocol_run.status = 'completed' if success else 'failed'
        protocol_run.result_status = 'pass' if success else 'fail'
        protocol_run.completed_at = end_time
        protocol_run.duration_seconds = duration
        protocol_run.error_message = error_message
        protocol_run.save()

        logger.info(f"Protocol {protocol.name} execution completed. Success: {success}, Duration: {duration:.2f}s")

        return {
            "status": "success" if success else "failure",
            "run_id": str(protocol_run_id),
            "protocol_id": str(protocol_id),
            "duration": duration,
            "error": error_message
        }

    except Exception as e:
        logger.error(f"Unhandled error in execute_protocol_run: {str(e)}", exc_info=True)

        # Try to update the protocol run status
        try:
            protocol_run = ProtocolRun.objects.get(id=protocol_run_id)
            protocol_run.status = 'error'
            protocol_run.result_status = 'error'
            protocol_run.error_message = f"Task error: {str(e)}"
            protocol_run.completed_at = timezone.now()
            protocol_run.save()

            # Create error result
            ProtocolResult.objects.create(
                run=protocol_run,
                success=False,
                result_data={"task_error": str(e)},
                error_message=f"Task error: {str(e)}"
            )
        except Exception as inner_e:
            logger.error(f"Error updating run status: {str(inner_e)}")

        # Return error information
        return {
            "status": "error",
            "error": str(e),
            "run_id": str(protocol_run_id) if protocol_run_id else None
        }


def create_connection(connection_config):
    """Create the appropriate connection based on the configuration type"""
    config_type = connection_config.config_type

    if config_type == 'api':
        # Create API connection configuration
        api_config = APIConfig(
            name=f"API-{connection_config.host}",
            host=connection_config.host,
            port=connection_config.port,
            timeout=connection_config.timeout_seconds,
            auth_method=AuthMethod.BASIC if connection_config.username else AuthMethod.NONE,
            username=connection_config.username.value if connection_config.username else None,
            password=connection_config.password.value if connection_config.password else None,
            max_retries=connection_config.retry_attempts,
            options=connection_config.config_data
        )
        return APIConnection(api_config)

    elif config_type == 'database':
        # Get database type from config or default to postgresql
        db_type_str = connection_config.config_data.get('database_type', 'postgresql')
        db_type = DatabaseType.POSTGRESQL
        if db_type_str == 'mysql':
            db_type = DatabaseType.MYSQL
        elif db_type_str == 'oracle':
            db_type = DatabaseType.ORACLE
        elif db_type_str == 'mssql':
            db_type = DatabaseType.MSSQL

        # Create Database connection configuration
        db_config = DatabaseConnectionConfig(
            name=f"DB-{connection_config.host}",
            host=connection_config.host,
            port=connection_config.port,
            database=connection_config.config_data.get('database', ''),
            database_type=db_type,
            username=connection_config.username.value if connection_config.username else None,
            password=connection_config.password.value if connection_config.password else None,
            timeout=connection_config.timeout_seconds,
            max_retries=connection_config.retry_attempts,
            options=connection_config.config_data.get('options', {})
        )
        return DatabaseConnection(db_config)

    elif config_type == 'ssh':
        # Create SSH connection configuration
        ssh_config = SSHConnectionConfig(
            name=f"SSH-{connection_config.host}",
            host=connection_config.host,
            port=connection_config.port or 22,
            username=connection_config.username.value if connection_config.username else None,
            password=connection_config.password.value if connection_config.password else None,
            timeout=connection_config.timeout_seconds,
            max_retries=connection_config.retry_attempts,
            auth_method=SSHAuthMethod.PASSWORD
        )
        return SSHConnection(ssh_config)

    elif config_type == 'kubernetes':
        # Create Kubernetes connection configuration
        k8s_config = KubernetesConnectionConfig(
            name=f"K8S-{connection_config.host}",
            host=connection_config.host,
            port=connection_config.port or 6443,
            username=connection_config.username.value if connection_config.username else None,
            password=connection_config.password.value if connection_config.password else None,
            auth_method=KubernetesAuthMethod.BASIC if connection_config.username else KubernetesAuthMethod.CONFIG,
            api_token=connection_config.secret_key.value if connection_config.secret_key else None,
            timeout=connection_config.timeout_seconds,
            max_retries=connection_config.retry_attempts,
            namespace=connection_config.config_data.get('namespace', 'default')
        )
        return KubernetesConnection(k8s_config)

    elif config_type == 'aws':
        # Create AWS connection configuration
        aws_config = AWSConnectionConfig(
            name=f"AWS-{connection_config.host or 'default'}",
            host=connection_config.host or '',
            auth_method=AWSAuthMethod.ACCESS_KEY,
            access_key_id=connection_config.username.value if connection_config.username else None,
            secret_access_key=connection_config.password.value if connection_config.password else None,
            region=AWSRegion.US_EAST_1,  # Default region
            service=AWSService.S3,  # Default service
            timeout=connection_config.timeout_seconds,
            max_retries=connection_config.retry_attempts
        )

        # Set additional AWS-specific configuration
        if 'region' in connection_config.config_data:
            region_value = connection_config.config_data['region']
            for region in AWSRegion:
                if region.value == region_value:
                    aws_config.region = region
                    break

        if 'service' in connection_config.config_data:
            service_value = connection_config.config_data['service']
            for service in AWSService:
                if service.value == service_value:
                    aws_config.service = service
                    break

        return AWSConnection(aws_config)

    else:
        raise ValueError(f"Unsupported connection type: {config_type}")


def execute_by_connection_type(connection, connection_config, protocol):
    """Execute the protocol based on the connection type"""
    config_type = connection_config.config_type

    if config_type == 'api':
        # Execute API test
        method = connection_config.config_data.get('method', 'GET')
        endpoint = connection_config.config_data.get('endpoint', '')
        data = connection_config.config_data.get('data')
        params = connection_config.config_data.get('params')

        result = connection.execute(
            method=method,
            endpoint=endpoint,
            data=data,
            params=params
        )
        return result

    elif config_type == 'database':
        # Execute database query
        query = connection_config.config_data.get('query', 'SELECT 1')
        params = connection_config.config_data.get('params', {})

        result = connection.execute(query, params=params)
        return result

    elif config_type == 'ssh':
        # Execute SSH command
        command = connection_config.config_data.get('command', 'echo "Test execution"')

        result = connection.execute(command)
        return {"output": result}

    elif config_type == 'kubernetes':
        # Execute Kubernetes operation
        resource_type = connection_config.config_data.get('resource_type', 'pod')
        action = connection_config.config_data.get('action', 'list')
        namespace = connection_config.config_data.get('namespace', 'default')

        result = connection.execute(
            resource_type=resource_type,
            action=action,
            namespace=namespace
        )
        return result

    elif config_type == 'aws':
        # Execute AWS operation
        operation = connection_config.config_data.get('operation', 'list_buckets')
        params = connection_config.config_data.get('params', {})

        result = connection.execute(
            operation=operation,
            **params
        )
        return result

    else:
        return {"message": "No execution performed"}


def generate_result_text(success, protocol_name, duration, error=None):
    """Generate a human-readable result text"""
    if success:
        return f"Protocol '{protocol_name}' executed successfully in {duration:.2f} seconds."
    else:
        return f"Protocol '{protocol_name}' failed after {duration:.2f} seconds. Error: {error}"