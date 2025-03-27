"""YAML Validation Rules Loader for the Pangolin SDK.

This module handles loading validation rules from YAML configuration files
and mapping them to the appropriate configuration classes.
"""

import os
import logging
from typing import Any, Dict, Type
import yaml

from pangolin_sdk.configs.base import BaseConfig

logger = logging.getLogger(__name__)

# Dictionary for mapping custom validation functions
CUSTOM_VALIDATOR_FUNCTIONS = {
    # Oracle database validation
    'oracle_connection_requires_identifier': lambda cfg: (
            cfg.database_type == 'ORACLE' and
            not cfg.connection_string and
            not cfg.sid and
            not cfg.tns_name
    ),

    # Kubernetes validation functions
    'config_auth_without_in_cluster': lambda cfg: (
            cfg.auth_method == 'CONFIG' and not cfg.in_cluster
    ),
    'config_auth_without_kubeconfig': lambda cfg: (
            cfg.auth_method == 'CONFIG' and not cfg.kubeconfig_path
    ),

    # SSH validation functions
    'public_key_auth_without_encrypted_key': lambda cfg: (
            cfg.auth_method == 'PUBLIC_KEY' and not cfg.encrypted_key_str
    ),
    'public_key_auth_without_key_filename': lambda cfg: (
            cfg.auth_method == 'PUBLIC_KEY' and not cfg.key_filename
    ),
    'encrypted_key_without_filename': lambda cfg: (
            cfg.auth_method == 'PUBLIC_KEY' and
            cfg.encrypted_key_str and
            not cfg.key_filename
    ),
}


class ValidationRulesLoader:
    """Loader for YAML-based validation rules.

    This class handles loading and processing validation rules from YAML files
    and mapping them to the appropriate configuration classes.
    """

    _instance = None
    _rules_cache = None

    def __new__(cls):
        """Implement singleton pattern for the loader."""
        if cls._instance is None:
            cls._instance = super(ValidationRulesLoader, cls).__new__(cls)
            cls._instance._rules_cache = None
        return cls._instance

    def __init__(self):
        """Initialize the validation rules loader."""
        if self._rules_cache is None:
            self._rules_cache = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load validation rules from YAML files.

        Returns:
            Dictionary containing all loaded validation rules
        """
        rules = {}

        # Default rules file path
        default_rules_path = os.path.join(
            os.path.dirname(__file__),
            'validation_rules.yaml'
        )

        # Custom rules path from environment variable
        custom_rules_path = os.environ.get('PANGOLIN_VALIDATION_RULES')

        # Load default rules
        if os.path.exists(default_rules_path):
            try:
                with open(default_rules_path, 'r') as f:
                    rules = yaml.safe_load(f)
                logger.debug(f"Loaded default validation rules from {default_rules_path}")
            except Exception as e:
                logger.error(f"Error loading validation rules: {e}")

        # Override with custom rules if available
        if custom_rules_path and os.path.exists(custom_rules_path):
            try:
                with open(custom_rules_path, 'r') as f:
                    custom_rules = yaml.safe_load(f)
                    # Update rules with custom values
                    rules = self._deep_update(rules, custom_rules)
                logger.debug(f"Loaded custom validation rules from {custom_rules_path}")
            except Exception as e:
                logger.error(f"Error loading custom validation rules: {e}")

        return rules

    def _deep_update(self, d1: Dict, d2: Dict) -> Dict:
        """Perform a deep update of one dictionary with another.

        Args:
            d1: Base dictionary to update
            d2: Dictionary with values to overlay on d1

        Returns:
            Updated dictionary
        """
        result = d1.copy()

        for k, v in d2.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._deep_update(result[k], v)
            else:
                result[k] = v

        return result

    def get_rules_for_config(self, config_class: Type[BaseConfig]) -> Dict[str, Dict[str, Any]]:
        """Get validation rules for a specific configuration class.

        Args:
            config_class: The configuration class to get rules for

        Returns:
            Dictionary containing validation rules for the specified class
        """
        # Determine which rule set to use based on class name
        class_name = config_class.__name__.lower()

        # Map class name to rule set
        rule_key = None

        if 'aws' in class_name:
            rule_key = 'aws_connection'
        elif 'database' in class_name:
            rule_key = 'database_connection'
        elif 'kubernetes' in class_name:
            rule_key = 'kubernetes_connection'
        elif 'ssh' in class_name:
            rule_key = 'ssh_connection'
        elif 'api' in class_name:
            rule_key = 'api_connection'
        elif 'azure' in class_name:
            rule_key = 'azure_connection'
        else:
            rule_key = 'base_connection'

        # Get rules or empty dict if not found
        rules = self._rules_cache.get(rule_key, {})

        # Process custom validators
        self._process_custom_validators(rules)

        return rules

    def _process_custom_validators(self, rules: Dict[str, Dict[str, Any]]) -> None:
        """Process custom validator references in the rules.

        This method replaces custom validator names with actual functions.

        Args:
            rules: Rules dictionary to process
        """
        for field_name, field_rules in rules.items():
            if 'required_if_custom' in field_rules:
                validator_name = field_rules['required_if_custom']

                if isinstance(validator_name, str):
                    # Replace validator name with actual function
                    validator_func = CUSTOM_VALIDATOR_FUNCTIONS.get(validator_name)

                    if validator_func:
                        field_rules['required_if_custom'] = {
                            'condition': validator_func
                        }
                    else:
                        logger.warning(f"Custom validator '{validator_name}' not found")
                        # Remove invalid validator to prevent errors
                        del field_rules['required_if_custom']


# Function to get validation rules for a config class
def get_validation_rules(config_class: Type[BaseConfig]) -> Dict[str, Dict[str, Any]]:
    """Get validation rules for a configuration class.

    Args:
        config_class: The configuration class to get rules for

    Returns:
        Dictionary containing validation rules
    """
    loader = ValidationRulesLoader()
    return loader.get_rules_for_config(config_class)


# Function to validate a config object with appropriate rules
def validate_config(config: BaseConfig) -> None:
    """Validate a configuration object using rules from YAML files.

    Args:
        config: The configuration object to validate

    Raises:
        ValueError: If validation fails
    """
    from pangolin_sdk.configs.validators import ConfigurationValidator

    # Get rules for this config class
    rules = get_validation_rules(config.__class__)

    # Validate using the rules
    errors = ConfigurationValidator.validate(config, rules)

    if errors:
        error_message = f"Configuration validation failed: {'; '.join(errors)}"
        logger.error(error_message)
        raise ValueError(error_message)