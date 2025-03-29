# test_protocols/services.py
import logging
from django.utils import timezone
from django.contrib.auth.models import User

from test_protocols.models import ProtocolRun, TestProtocol, TestSuite
from test_protocols.tasks import run_test_protocol, run_test_suite

logger = logging.getLogger(__name__)


def run_protocol(protocol_id, user=None, executed_by=None):
    """
    Create a protocol run and send a message to RabbitMQ for Celery to process.

    Args:
        protocol_id: The UUID of the protocol to run
        user: The user who is initiating the run (optional)
        executed_by: String describing who/what executed the protocol (optional)

    Returns:
        ProtocolRun: The created protocol run object
    """
    logger.info(f"Initiating protocol run for protocol ID: {protocol_id}")

    # Get the protocol
    try:
        protocol = TestProtocol.objects.get(id=protocol_id)
    except TestProtocol.DoesNotExist:
        logger.error(f"Protocol with ID {protocol_id} not found")
        raise ValueError(f"Protocol with ID {protocol_id} not found")

    # Determine executed_by value
    if executed_by is None and user is not None:
        executed_by = user.username
    elif executed_by is None:
        executed_by = "system"

    # Create the protocol run
    protocol_run = ProtocolRun.objects.create(
        protocol=protocol, status="pending", executed_by=executed_by
    )

    logger.info(f"Created ProtocolRun with ID: {protocol_run.id}")

    # Determine the username for the task
    username = user.username if user else "system"

    # Send task to Celery via RabbitMQ with protocol UUID
    run_test_protocol.delay(protocol_run.id, username)

    logger.info(
        f"Sent message to RabbitMQ for protocol run: {protocol_run.id}, protocol: {protocol.id}"
    )

    return protocol_run


def run_suite(suite_id, user=None):
    """
    Run all active protocols in a test suite.

    Args:
        suite_id: The UUID of the test suite
        user: The user who is initiating the runs

    Returns:
        list: The created protocol run objects
    """
    logger.info(f"Running test suite with ID: {suite_id}")

    # Get the test suite
    try:
        test_suite = TestSuite.objects.get(id=suite_id)
    except TestSuite.DoesNotExist:
        logger.error(f"Test suite with ID {suite_id} not found")
        raise ValueError(f"Test suite with ID {suite_id} not found")

    # Determine the username and user_id for the task
    username = user.username if user else "system"

    # Send the entire suite to the suite queue
    run_test_suite.delay(test_suite.id, username)
    logger.info(f"Sent test suite {test_suite.id} to suite queue")

    # For backward compatibility, return empty list
    # (actual runs will be created by the task)
    return []


def run_protocols_in_suite(suite_id, user=None):
    """
    Individually run all active protocols in a test suite.
    This is the original implementation that schedules each protocol separately.

    Args:
        suite_id: The UUID of the test suite
        user: The user who is initiating the runs

    Returns:
        list: The created protocol run objects
    """
    logger.info(f"Running protocols in test suite with ID: {suite_id}")

    # Get the test suite
    try:
        test_suite = TestSuite.objects.get(id=suite_id)
    except TestSuite.DoesNotExist:
        logger.error(f"Test suite with ID {suite_id} not found")
        raise ValueError(f"Test suite with ID {suite_id} not found")

    # Get all active protocols in this suite
    protocols = test_suite.protocols.filter(status="active").order_by("order_index")

    if not protocols.exists():
        logger.warning(f"No active protocols found in test suite: {test_suite.name}")
        return []

    # Run each protocol
    protocol_runs = []
    for protocol in protocols:
        try:
            protocol_run = run_protocol(protocol.id, user)
            protocol_runs.append(protocol_run)
            logger.info(
                f"Scheduled protocol {protocol.name} (ID: {protocol.id}) in suite {test_suite.name} (ID: {test_suite.id})"
            )
        except Exception as e:
            logger.error(
                f"Failed to schedule protocol {protocol.name} (ID: {protocol.id}): {str(e)}"
            )

    return protocol_runs
