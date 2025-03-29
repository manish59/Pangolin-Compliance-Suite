"""Base configuration module for Pangolin SDK.

This module provides the foundational configuration classes used for
establishing and managing connections across different services.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional
from dataclasses import fields


@dataclass(kw_only=True)
class BaseConfig:
    """Base configuration for all connection types.

    This class provides the fundamental configuration parameters needed
    for establishing and maintaining connections.

    Attributes:
        name: Unique identifier for the connection
        host: Target host address or URL
        timeout: Connection timeout in seconds
        max_retries: Maximum number of connection retry attempts
        retry_interval: Time to wait between retries in seconds
        retry_backoff: Multiplier for increasing retry interval
    """

    name: str
    host: str
    timeout: int = 30
    max_retries: int = 3
    retry_interval: int = 5
    retry_backoff: float = 1.5

    @classmethod
    def from_dict(cls, config_dict):
        """
        Create a configuration instance from a dictionary.

        Args:
            config_dict (dict): Dictionary with configuration values

        Returns:
            An instance of the configuration class
        """
        # Get valid field names for this class
        valid_keys = {f.name for f in fields(cls)}
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_keys}

        # Create and return the instance
        return cls(**filtered_dict)

    def get_info(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary.

        Returns:
            Dictionary containing all configuration parameters
        """
        return asdict(self)


@dataclass(kw_only=True)
class ConnectionConfig(BaseConfig):
    """Extended configuration for connections requiring authentication.

    This class extends BaseConfig with additional parameters for
    authentication and SSL configuration.

    Attributes:
        username: Authentication username
        password: Authentication password
        retry_jitter: Whether to add random jitter to retry intervals
        ssl_enabled: Whether SSL/TLS is enabled for the connection
        ssl_verify: Whether to verify SSL certificates
        options: Additional connection-specific options
    """

    username: Optional[str] = None
    password: Optional[str] = None
    retry_jitter: bool = True
    ssl_enabled: bool = True
    ssl_verify: bool = True
    options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Perform post-initialization validation.

        This method is called after the dataclass is initialized and can
        be overridden by subclasses to add custom validation logic.
        """
