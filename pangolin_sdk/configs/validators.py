"""Universal config validation module for Pangolin SDK.

This module provides a common validation framework for different connection
configurations, consolidating validation logic into a single utility class.
"""

from typing import Any, Dict, List, Optional, Set, Type, Union, Callable
import logging
from dataclasses import is_dataclass, fields

# Setup logging
logger = logging.getLogger(__name__)


class ConfigurationValidator:
    """Universal configuration validator for connection configs.

    This class provides methods to validate various types of connection
    configurations using a consistent approach, eliminating the need for
    multiple validator implementations.
    """

    @staticmethod
    def validate(
        config: Any, validation_rules: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[str]:
        """Validate a configuration object against defined rules.

        Args:
            config: The configuration object to validate
            validation_rules: Optional custom validation rules to apply

        Returns:
            List of validation error messages (empty if validation passed)
        """
        if not is_dataclass(config):
            return ["Validation target must be a dataclass instance"]

        errors = []

        # Apply default validation rules based on config type if no custom rules provided
        if validation_rules is None:
            validation_rules = ConfigurationValidator._get_default_rules(config)

        # Validate each field according to its rules
        for field_name, rules in validation_rules.items():
            field_value = getattr(config, field_name, None)
            field_errors = ConfigurationValidator._validate_field(
                field_name, field_value, rules
            )
            errors.extend(field_errors)

        # Add any complex cross-field validations
        context_errors = ConfigurationValidator._validate_context(
            config, validation_rules
        )
        errors.extend(context_errors)

        return errors

    @staticmethod
    def _get_default_rules(config: Any) -> Dict[str, Dict[str, Any]]:
        """Get default validation rules based on the config type.

        Args:
            config: The configuration object

        Returns:
            Dictionary of validation rules
        """
        # Detect config type from class name
        config_type = config.__class__.__name__

        # AWS connection config
        if "AWS" in config_type:
            return {
                "auth_method": {
                    "required": True,
                    "choices": [
                        "ACCESS_KEY",
                        "PROFILE",
                        "INSTANCE_ROLE",
                        "WEB_IDENTITY",
                        "SSO",
                    ],
                },
                "region": {
                    "required": True,
                },
                "service": {
                    "required": True,
                },
                "access_key_id": {
                    "required_if": {"field": "auth_method", "value": "ACCESS_KEY"}
                },
                "secret_access_key": {
                    "required_if": {"field": "auth_method", "value": "ACCESS_KEY"}
                },
                "profile_name": {
                    "required_if": {"field": "auth_method", "value": "PROFILE"}
                },
                "role_arn": {
                    "required_if": {"field": "auth_method", "value": "WEB_IDENTITY"}
                },
                "web_identity_token_file": {
                    "required_if": {"field": "auth_method", "value": "WEB_IDENTITY"}
                },
                "sso_account_id": {
                    "required_if": {"field": "auth_method", "value": "SSO"}
                },
                "sso_role_name": {
                    "required_if": {"field": "auth_method", "value": "SSO"}
                },
                "sso_region": {"required_if": {"field": "auth_method", "value": "SSO"}},
                "sso_start_url": {
                    "required_if": {"field": "auth_method", "value": "SSO"}
                },
            }

        # Database connection config
        elif "Database" in config_type:
            return {
                "database_type": {
                    "required": True,
                },
                "host": {
                    "required_unless": {"field": "connection_string", "not_empty": True}
                },
                "port": {
                    "required_unless": {"field": "connection_string", "not_empty": True}
                },
                "database": {
                    "required_unless": [
                        {"field": "connection_string", "not_empty": True},
                        {"field": "service_name", "not_empty": True},
                        {"field": "sid", "not_empty": True},
                    ]
                },
                "username": {
                    "required_unless": {"field": "connection_string", "not_empty": True}
                },
                "password": {
                    "required_unless": {"field": "connection_string", "not_empty": True}
                },
                # Special validation for Oracle connections
                "service_name": {
                    "required_if_custom": {
                        "condition": lambda cfg: cfg.database_type == "ORACLE"
                        and not cfg.connection_string
                        and not cfg.sid
                        and not cfg.tns_name
                    }
                },
            }

        # Kubernetes connection config
        elif "Kubernetes" in config_type:
            return {
                "auth_method": {
                    "required": True,
                    "choices": ["CONFIG", "TOKEN", "CERTIFICATE", "BASIC"],
                },
                "kubeconfig_path": {
                    "required_if_custom": {
                        "condition": lambda cfg: cfg.auth_method == "CONFIG"
                        and not cfg.in_cluster
                    }
                },
                "in_cluster": {
                    "required_if_custom": {
                        "condition": lambda cfg: cfg.auth_method == "CONFIG"
                        and not cfg.kubeconfig_path
                    }
                },
                "api_token": {
                    "required_if": {"field": "auth_method", "value": "TOKEN"}
                },
                "client_cert_path": {
                    "required_if": {"field": "auth_method", "value": "CERTIFICATE"}
                },
                "client_key_path": {
                    "required_if": {"field": "auth_method", "value": "CERTIFICATE"}
                },
                "username": {"required_if": {"field": "auth_method", "value": "BASIC"}},
                "password": {"required_if": {"field": "auth_method", "value": "BASIC"}},
            }

        # SSH connection config
        elif "SSH" in config_type:
            return {
                "auth_method": {
                    "required": True,
                    "choices": ["PASSWORD", "PUBLIC_KEY", "AGENT"],
                },
                "username": {"required": True},
                "password": {
                    "required_if": {"field": "auth_method", "value": "PASSWORD"}
                },
                "key_filename": {
                    "required_if_custom": {
                        "condition": lambda cfg: cfg.auth_method == "PUBLIC_KEY"
                        and not cfg.encrypted_key_str
                    }
                },
                "encrypted_key_str": {
                    "required_if_custom": {
                        "condition": lambda cfg: cfg.auth_method == "PUBLIC_KEY"
                        and not cfg.key_filename
                    }
                },
                "passphrase": {
                    "required_if_custom": {
                        "condition": lambda cfg: cfg.auth_method == "PUBLIC_KEY"
                        and cfg.encrypted_key_str
                        and not cfg.key_filename
                    }
                },
            }

        # API connection config
        elif "API" in config_type:
            return {
                "auth_method": {
                    "required": True,
                    "choices": [
                        "NONE",
                        "BASIC",
                        "BEARER",
                        "JWT",
                        "API_KEY",
                        "OAUTH2",
                        "HMAC",
                    ],
                },
                "username": {"required_if": {"field": "auth_method", "value": "BASIC"}},
                "password": {"required_if": {"field": "auth_method", "value": "BASIC"}},
                "auth_token": {
                    "required_if": [
                        {"field": "auth_method", "value": "BEARER"},
                        {"field": "auth_method", "value": "JWT"},
                    ]
                },
                "api_key": {
                    "required_if": {"field": "auth_method", "value": "API_KEY"}
                },
                "api_key_name": {
                    "required_if": {"field": "auth_method", "value": "API_KEY"}
                },
                "oauth_client_id": {
                    "required_if": {"field": "auth_method", "value": "OAUTH2"}
                },
                "oauth_client_secret": {
                    "required_if": {"field": "auth_method", "value": "OAUTH2"}
                },
                "hmac_key": {"required_if": {"field": "auth_method", "value": "HMAC"}},
                "hmac_secret": {
                    "required_if": {"field": "auth_method", "value": "HMAC"}
                },
            }

        # Azure connection config
        elif "Azure" in config_type:
            return {
                "auth_method": {
                    "required": True,
                    "choices": ["SERVICE_PRINCIPAL", "MANAGED_IDENTITY", "CLI"],
                },
                "client_id": {
                    "required_if": {
                        "field": "auth_method",
                        "value": "SERVICE_PRINCIPAL",
                    }
                },
                "client_secret": {
                    "required_if": {
                        "field": "auth_method",
                        "value": "SERVICE_PRINCIPAL",
                    }
                },
                "tenant_id": {
                    "required_if": {
                        "field": "auth_method",
                        "value": "SERVICE_PRINCIPAL",
                    }
                },
            }

        # Default base connection config
        else:
            return {"name": {"required": True}, "host": {"required": True}}

    @staticmethod
    def _validate_field(
        field_name: str, field_value: Any, rules: Dict[str, Any]
    ) -> List[str]:
        """Validate a single field against its rules.

        Args:
            field_name: Name of the field to validate
            field_value: Value of the field to validate
            rules: Validation rules for the field

        Returns:
            List of validation error messages (empty if validation passed)
        """
        errors = []

        # Required field check
        if rules.get("required", False) and not field_value:
            errors.append(f"'{field_name}' is required")

        # Check against allowed choices
        if "choices" in rules and field_value is not None:
            choices = rules["choices"]
            if field_value not in choices and str(field_value) not in choices:
                errors.append(
                    f"'{field_name}' must be one of: {', '.join(str(c) for c in choices)}"
                )

        # Type validation
        if "type" in rules and field_value is not None:
            expected_type = rules["type"]
            if not isinstance(field_value, expected_type):
                errors.append(
                    f"'{field_name}' must be of type {expected_type.__name__}"
                )

        # Range validation for numeric fields
        if "min_value" in rules and field_value is not None:
            min_value = rules["min_value"]
            if field_value < min_value:
                errors.append(f"'{field_name}' must be at least {min_value}")

        if "max_value" in rules and field_value is not None:
            max_value = rules["max_value"]
            if field_value > max_value:
                errors.append(f"'{field_name}' must be at most {max_value}")

        # Pattern validation for string fields
        if (
            "pattern" in rules
            and field_value is not None
            and isinstance(field_value, str)
        ):
            import re

            pattern = rules["pattern"]
            if not re.match(pattern, field_value):
                errors.append(f"'{field_name}' does not match required pattern")

        return errors

    @staticmethod
    def _validate_context(config: Any, rules: Dict[str, Dict[str, Any]]) -> List[str]:
        """Perform context-dependent validations that involve multiple fields.

        Args:
            config: The configuration object to validate
            rules: Validation rules to apply

        Returns:
            List of validation error messages (empty if validation passed)
        """
        errors = []

        # Process each field for conditional validations
        for field_name, field_rules in rules.items():
            field_value = getattr(config, field_name, None)

            # Required if another field has specific value
            if "required_if" in field_rules:
                required_if = field_rules["required_if"]

                # Handle both single condition and list of conditions
                conditions = (
                    required_if if isinstance(required_if, list) else [required_if]
                )

                for condition in conditions:
                    other_field = condition["field"]
                    expected_value = condition["value"]
                    other_value = getattr(config, other_field, None)

                    # Check if the condition applies
                    if (
                        other_value == expected_value
                        or str(other_value) == expected_value
                    ):
                        if not field_value:
                            errors.append(
                                f"'{field_name}' is required when '{other_field}' is '{expected_value}'"
                            )

            # Required unless another field has a non-empty value
            if "required_unless" in field_rules:
                required_unless = field_rules["required_unless"]

                # Handle both single condition and list of conditions
                conditions = (
                    required_unless
                    if isinstance(required_unless, list)
                    else [required_unless]
                )

                # Default to field being required
                is_required = True

                for condition in conditions:
                    other_field = condition["field"]
                    other_value = getattr(config, other_field, None)

                    # Check if any condition is met to make this field not required
                    if condition.get("not_empty", False) and other_value:
                        is_required = False
                        break
                    elif "value" in condition and other_value == condition["value"]:
                        is_required = False
                        break

                if is_required and not field_value:
                    fields_list = ", ".join(f"'{c['field']}'" for c in conditions)
                    errors.append(
                        f"'{field_name}' is required unless {fields_list} meets conditions"
                    )

            # Custom condition function
            if "required_if_custom" in field_rules:
                condition_func = field_rules["required_if_custom"]["condition"]
                if condition_func(config) and not field_value:
                    errors.append(
                        f"'{field_name}' is required based on other configuration settings"
                    )

        return errors


# Usage example
def validate_config(config: Any) -> List[str]:
    """Validate a configuration object using the universal validator.

    Args:
        config: The configuration object to validate

    Returns:
        List of validation error messages (empty if validation passed)

    Raises:
        ValueError: If validation fails and raise_exception is True
    """
    errors = ConfigurationValidator.validate(config)

    if errors:
        error_message = f"Configuration validation failed: {'; '.join(errors)}"
        logger.error(error_message)
        raise ValueError(error_message)

    return errors
