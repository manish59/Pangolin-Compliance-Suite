import unittest
import base64
import time
import hmac
import hashlib
from pangolin_sdk.configs.api import APIConfig, HeaderDefinition, AuthError
from pangolin_sdk.constants import AuthMethod, HeaderRequirement

class TestAPIConfig(unittest.TestCase):
    def test_header_definition_full_initialization(self):
        header_def = HeaderDefinition(
            name="X-Custom-Header",
            requirement=HeaderRequirement.REQUIRED,
            default_value="default",
            allowed_values=["default", "custom"],
            pattern="^[a-zA-Z0-9_-]*$",
            description="A custom header."
        )
        self.assertEqual(header_def.name, "X-Custom-Header")
        self.assertEqual(header_def.requirement, HeaderRequirement.REQUIRED)
        self.assertEqual(header_def.default_value, "default")
        self.assertEqual(header_def.allowed_values, ["default", "custom"])
        self.assertEqual(header_def.pattern, "^[a-zA-Z0-9_-]*$")
        self.assertEqual(header_def.description, "A custom header.")

    def test_header_definition_minimal_initialization(self):
        header_def = HeaderDefinition(
            name="X-Another-Header",
            requirement=HeaderRequirement.OPTIONAL
        )
        self.assertEqual(header_def.name, "X-Another-Header")
        self.assertEqual(header_def.requirement, HeaderRequirement.OPTIONAL)
        self.assertIsNone(header_def.default_value)
        self.assertIsNone(header_def.allowed_values)
        self.assertIsNone(header_def.pattern)
        self.assertIsNone(header_def.description)

    def test_api_config_default_initialization(self):
        config = APIConfig(name="default_config", host="http://localhost")
        self.assertEqual(config.host, "http://localhost")
        # self.assertEqual(config.port, 80) # Default from ConnectionConfig - Port attribute not explicitly defined
        self.assertEqual(config.timeout, 30) # Default from ConnectionConfig
        self.assertEqual(config.auth_method, AuthMethod.NONE)
        self.assertIsNone(config.auth_token)
        self.assertIsNone(config.api_key)
        self.assertIsNone(config.api_key_name)
        self.assertEqual(config.api_key_location, "header")
        self.assertIsNone(config.hmac_key)
        self.assertIsNone(config.hmac_secret)
        self.assertEqual(config.hmac_algorithm, "sha256")
        self.assertIsNone(config.oauth_client_id)
        self.assertIsNone(config.oauth_client_secret)
        self.assertIsNone(config.oauth_scope)
        self.assertIsNone(config.jwt_secret)
        self.assertEqual(config.jwt_algorithm, "HS256")
        self.assertEqual(config.default_headers, {"Content-Type": "application/json", "Accept": "application/json"})
        # Check that default header definitions are initialized
        self.assertTrue(len(config.header_definitions) > 0)
        self.assertIsInstance(config.header_definitions[0], HeaderDefinition)

    def test_api_config_custom_initialization(self):
        custom_headers = {"X-Test": "true"}
        header_defs = [HeaderDefinition(name="X-Specific", requirement=HeaderRequirement.REQUIRED)]
        config = APIConfig(
            name="custom_config",
            host="https://api.example.com/", # Test trailing slash
            # port=443, # Port should be part of host string if non-standard
            timeout=60,
            auth_method=AuthMethod.BEARER,
            auth_token="test_token",
            default_headers=custom_headers,
            header_definitions=header_defs,
            username="user", # For ConnectionConfig part
            password="pass"  # For ConnectionConfig part
        )
        self.assertEqual(config.host, "https://api.example.com") # Trailing slash should be stripped
        # self.assertEqual(config.port, 443) # Port attribute not explicitly defined
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.auth_method, AuthMethod.BEARER)
        self.assertEqual(config.auth_token, "test_token")
        self.assertEqual(config.default_headers, custom_headers)
        self.assertEqual(config.header_definitions, header_defs)
        self.assertEqual(config.username, "user")
        self.assertEqual(config.password, "pass")

    def test_api_config_host_normalization(self):
        config1 = APIConfig(name="host_norm1", host="http://example.com/")
        self.assertEqual(config1.host, "http://example.com")
        config2 = APIConfig(name="host_norm2", host="http://example.com")
        self.assertEqual(config2.host, "http://example.com")

    def test_api_config_default_header_definitions_initialization(self):
        config = APIConfig(name="default_headers_config", host="http://localhost")
        self.assertTrue(len(config.header_definitions) == 3) # Based on current implementation
        names = [hd.name for hd in config.header_definitions]
        self.assertIn("Content-Type", names)
        self.assertIn("Accept", names)
        self.assertIn("User-Agent", names)

    def test_api_config_custom_header_definitions(self):
        my_header_def = [HeaderDefinition(name="X-My-Header", requirement=HeaderRequirement.OPTIONAL)]
        config = APIConfig(name="custom_headers_config", host="http://localhost", header_definitions=my_header_def)
        self.assertEqual(config.header_definitions, my_header_def)

    def test_validate_basic_auth_valid(self):
        try:
            APIConfig(name="basic_auth_valid", host="h", username="user", password="password", auth_method=AuthMethod.BASIC)
        except AuthError:
            self.fail("AuthError raised unexpectedly for valid basic auth")

    def test_validate_basic_auth_invalid(self):
        with self.assertRaisesRegex(AuthError, "Username and password required for basic authentication"):
            APIConfig(name="basic_auth_invalid1", host="h", username="user", auth_method=AuthMethod.BASIC)
        with self.assertRaisesRegex(AuthError, "Username and password required for basic authentication"):
            APIConfig(name="basic_auth_invalid2", host="h", password="password", auth_method=AuthMethod.BASIC)

    def test_validate_bearer_auth_valid(self):
        try:
            APIConfig(name="bearer_auth_valid", host="h", auth_token="token", auth_method=AuthMethod.BEARER)
        except AuthError:
            self.fail("AuthError raised unexpectedly for valid bearer auth")

    def test_validate_bearer_auth_invalid(self):
        with self.assertRaisesRegex(AuthError, "Token required for bearer authentication"):
            APIConfig(name="bearer_auth_invalid", host="h", auth_method=AuthMethod.BEARER)

    def test_validate_jwt_auth_valid(self):
        # A simple, unsigned JWT for testing structure. Replace with a more robust one if needed.
        # Header: {"alg": "HS256", "typ": "JWT"} -> eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
        # Payload: {"sub": "1234567890", "name": "John Doe", "iat": 1516239022} -> eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ
        # Signature: (empty for unsigned)
        valid_jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
        try:
            APIConfig(name="jwt_auth_valid", host="h", auth_token=valid_jwt_token, auth_method=AuthMethod.JWT)
        except AuthError:
            self.fail("AuthError raised unexpectedly for valid JWT auth")

    def test_validate_jwt_auth_invalid_token_missing(self):
        with self.assertRaisesRegex(AuthError, "JWT token required for JWT authentication"):
            APIConfig(name="jwt_auth_invalid_missing", host="h", auth_method=AuthMethod.JWT)

    def test_validate_jwt_auth_invalid_token_format(self):
        with self.assertRaisesRegex(AuthError, "Invalid JWT token format"):
            APIConfig(name="jwt_auth_invalid_format", host="h", auth_token="not.a.jwt", auth_method=AuthMethod.JWT)

    def test_validate_api_key_auth_valid(self):
        try:
            APIConfig(name="api_key_auth_valid", host="h", api_key="key", api_key_name="X-API-KEY", auth_method=AuthMethod.API_KEY)
        except AuthError:
            self.fail("AuthError raised unexpectedly for valid API key auth")

    def test_validate_api_key_auth_invalid(self):
        with self.assertRaisesRegex(AuthError, "API key and key name required for API key authentication"):
            APIConfig(name="api_key_auth_invalid1", host="h", api_key="key", auth_method=AuthMethod.API_KEY)
        with self.assertRaisesRegex(AuthError, "API key and key name required for API key authentication"):
            APIConfig(name="api_key_auth_invalid2", host="h", api_key_name="X-API-KEY", auth_method=AuthMethod.API_KEY)

    def test_validate_oauth2_auth_valid(self):
        try:
            APIConfig(name="oauth2_auth_valid", host="h", oauth_client_id="id", oauth_client_secret="secret", auth_method=AuthMethod.OAUTH2)
        except AuthError:
            self.fail("AuthError raised unexpectedly for valid OAuth2 auth")

    def test_validate_oauth2_auth_invalid(self):
        with self.assertRaisesRegex(AuthError, "Client ID and secret required for OAuth2"):
            APIConfig(name="oauth2_auth_invalid1", host="h", oauth_client_id="id", auth_method=AuthMethod.OAUTH2)
        with self.assertRaisesRegex(AuthError, "Client ID and secret required for OAuth2"):
            APIConfig(name="oauth2_auth_invalid2", host="h", oauth_client_secret="secret", auth_method=AuthMethod.OAUTH2)

    def test_validate_hmac_auth_valid(self):
        try:
            APIConfig(name="hmac_auth_valid", host="h", hmac_key="key", hmac_secret="secret", auth_method=AuthMethod.HMAC)
        except AuthError:
            self.fail("AuthError raised unexpectedly for valid HMAC auth")

    def test_validate_hmac_auth_invalid(self):
        with self.assertRaisesRegex(AuthError, "Key and secret required for HMAC authentication"):
            APIConfig(name="hmac_auth_invalid1", host="h", hmac_key="key", auth_method=AuthMethod.HMAC)
        with self.assertRaisesRegex(AuthError, "Key and secret required for HMAC authentication"):
            APIConfig(name="hmac_auth_invalid2", host="h", hmac_secret="secret", auth_method=AuthMethod.HMAC)

    def test_no_auth_valid(self):
        try:
            APIConfig(name="no_auth_valid", host="h", auth_method=AuthMethod.NONE)
        except AuthError:
            self.fail("AuthError raised unexpectedly for AuthMethod.NONE")

    def test_get_auth_headers_none(self):
        config = APIConfig(name="get_headers_none", host="h", auth_method=AuthMethod.NONE)
        self.assertEqual(config.get_auth_headers(), {})

    def test_get_auth_headers_basic(self):
        config = APIConfig(name="get_headers_basic", host="h", username="testuser", password="testpassword", auth_method=AuthMethod.BASIC)
        expected_token = base64.b64encode(b"testuser:testpassword").decode()
        self.assertEqual(config.get_auth_headers(), {"Authorization": f"Basic {expected_token}"})

    def test_get_auth_headers_bearer(self):
        config = APIConfig(name="get_headers_bearer", host="h", auth_token="mybearertoken", auth_method=AuthMethod.BEARER)
        self.assertEqual(config.get_auth_headers(), {"Authorization": "Bearer mybearertoken"})

    def test_get_auth_headers_jwt(self):
        # Using the same simple JWT as in validation test
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
        config = APIConfig(name="get_headers_jwt", host="h", auth_token=jwt_token, auth_method=AuthMethod.JWT)
        self.assertEqual(config.get_auth_headers(), {"Authorization": f"Bearer {jwt_token}"})

    def test_get_auth_headers_api_key_header_location(self):
        config = APIConfig(name="get_headers_api_key_header", host="h", api_key="myapikey", api_key_name="X-API-Token", api_key_location="header", auth_method=AuthMethod.API_KEY)
        self.assertEqual(config.get_auth_headers(), {"X-API-Token": "myapikey"})

    def test_get_auth_headers_api_key_query_location(self):
        # api_key_location="query" should result in no auth headers from this method
        config = APIConfig(name="get_headers_api_key_query", host="h", api_key="myapikey", api_key_name="apiKey", api_key_location="query", auth_method=AuthMethod.API_KEY)
        self.assertEqual(config.get_auth_headers(), {})

    def test_get_auth_headers_oauth2_with_token(self):
        config = APIConfig(name="get_headers_oauth_with_token", host="h", oauth_client_id="id", oauth_client_secret="secret", auth_token="myoauthtoken", auth_method=AuthMethod.OAUTH2)
        self.assertEqual(config.get_auth_headers(), {"Authorization": "Bearer myoauthtoken"})

    def test_get_auth_headers_oauth2_no_token(self):
        config = APIConfig(name="get_headers_oauth_no_token", host="h", oauth_client_id="id", oauth_client_secret="secret", auth_method=AuthMethod.OAUTH2)
        with self.assertRaisesRegex(AuthError, "OAuth2 token not available. Authentication flow required."):
            config.get_auth_headers()

    def test_get_auth_headers_hmac(self):
        hmac_key = "hmac_key"
        hmac_secret = "hmac_secret"
        config = APIConfig(name="get_headers_hmac", host="http://localhost", hmac_key=hmac_key, hmac_secret=hmac_secret, auth_method=AuthMethod.HMAC)
        request_data = {"method": "POST", "path": "/test/endpoint"}

        # Mock time.time() for predictable timestamp
        original_time = time.time
        time.time = lambda: 1678886400 # Example: 2023-03-15 12:00:00 UTC

        headers = config.get_auth_headers(request_data=request_data)

        time.time = original_time # Restore time

        self.assertIn("X-Timestamp", headers)
        self.assertEqual(headers["X-Timestamp"], "1678886400")
        self.assertIn("X-API-Key", headers)
        self.assertEqual(headers["X-API-Key"], hmac_key)
        self.assertIn("X-Signature", headers)

        # Verify signature
        string_to_sign = f"1678886400:{hmac_key}:{request_data['method']}:{request_data['path']}"
        expected_signature = hmac.new(
            hmac_secret.encode(),
            string_to_sign.encode(),
            getattr(hashlib, config.hmac_algorithm),
        ).hexdigest()
        self.assertEqual(headers["X-Signature"], expected_signature)

    def test_get_auth_headers_hmac_sha512(self):
        hmac_key = "hmac_key_sha512"
        hmac_secret = "hmac_secret_sha512"
        config = APIConfig(name="get_headers_hmac_sha512", host="http://localhost", hmac_key=hmac_key, hmac_secret=hmac_secret, hmac_algorithm="sha512", auth_method=AuthMethod.HMAC)
        request_data = {"method": "GET", "path": "/another/path"}

        original_time = time.time
        time.time = lambda: 1678886401

        headers = config.get_auth_headers(request_data=request_data)

        time.time = original_time

        self.assertIn("X-Timestamp", headers)
        self.assertEqual(headers["X-Timestamp"], "1678886401")
        self.assertIn("X-API-Key", headers)
        self.assertEqual(headers["X-API-Key"], hmac_key)
        self.assertIn("X-Signature", headers)

        string_to_sign = f"1678886401:{hmac_key}:{request_data['method']}:{request_data['path']}"
        expected_signature = hmac.new(
            hmac_secret.encode(),
            string_to_sign.encode(),
            getattr(hashlib, "sha512"),
        ).hexdigest()
        self.assertEqual(headers["X-Signature"], expected_signature)


    def test_get_auth_headers_hmac_no_request_data(self):
        config = APIConfig(name="get_headers_hmac_no_data", host="h", hmac_key="key", hmac_secret="secret", auth_method=AuthMethod.HMAC)
        with self.assertRaisesRegex(AuthError, "Request data required for HMAC authentication"):
            config.get_auth_headers()

    def test_init_default_header_definitions_explicit_call(self):
        config = APIConfig(name="init_default_headers_explicit", host="http://localhost", header_definitions=[]) # Start with empty list
        # __post_init__ already calls _init_default_header_definitions if list is empty
        # So, by this point, it should already be populated.
        self.assertTrue(len(config.header_definitions) > 0)
        self.assertEqual(config.header_definitions[0].name, "Content-Type")
        self.assertEqual(config.header_definitions[1].name, "Accept")
        self.assertEqual(config.header_definitions[2].name, "User-Agent")

        # To specifically test the method if it were public and called again,
        # (though it's protected and called by __post_init__)
        # we can simulate it by resetting and calling, or just verify __post_init__'s behavior.
        # The current test `test_api_config_default_header_definitions_initialization` and this one
        # sufficiently cover the scenario of it being initialized when the list is empty.

        # If we want to ensure it DOESN'T re-initialize if definitions are already there:
        my_def = HeaderDefinition(name="X-My-Own", requirement=HeaderRequirement.OPTIONAL)
        config_with_defs = APIConfig(name="init_default_headers_custom", host="http://localhost", header_definitions=[my_def])
        self.assertEqual(len(config_with_defs.header_definitions), 1)
        self.assertEqual(config_with_defs.header_definitions[0], my_def)
        # Call the internal method (for testing purposes, normally not done)
        # config_with_defs._init_default_header_definitions()
        # self.assertEqual(len(config_with_defs.header_definitions), 1, "Should not overwrite existing definitions")
        # self.assertEqual(config_with_defs.header_definitions[0], my_def)
        # Commenting out direct call to protected method as it's not typical in unit tests
        # unless specifically testing that method in isolation and it's hard to trigger otherwise.
        # The existing __post_init__ behavior is what matters for users.

    def test_get_full_url(self):
        config = APIConfig(name="get_full_url_test", host="http://api.example.com")

        # Test with empty endpoint
        self.assertEqual(config.get_full_url(), "http://api.example.com")
        self.assertEqual(config.get_full_url(""), "http://api.example.com")

        # Test with non-empty endpoint
        self.assertEqual(config.get_full_url("test/path"), "http://api.example.com/test/path")

        # Test with endpoint having a leading slash
        self.assertEqual(config.get_full_url("/another/path"), "http://api.example.com/another/path")

        # Test with host having a trailing slash (should be handled by __post_init__)
        config_trailing_slash = APIConfig(name="get_full_url_trailing_slash", host="http://api.example.com/")
        self.assertEqual(config_trailing_slash.get_full_url("test"), "http://api.example.com/test")
        self.assertEqual(config_trailing_slash.get_full_url("/test"), "http://api.example.com/test")
        self.assertEqual(config_trailing_slash.get_full_url(), "http://api.example.com")

    def test_get_full_url_with_port(self):
        config = APIConfig(name="get_full_url_with_port1", host="http://localhost:8080")
        # The get_full_url method in the current implementation does not explicitly add the port
        # if it's not already part of the host string. It relies on the host string being complete.
        # This test will reflect the current behavior. If port should be part of URL construction,
        # the APIConfig.host or get_full_url method would need modification.
        # For now, we test based on current code which assumes host includes port if not standard.

        self.assertEqual(config.get_full_url("path"), "http://localhost:8080/path") # Adjusted to expect port from host

        config_with_port_in_host = APIConfig(name="get_full_url_with_port2", host="http://localhost:8080")
        self.assertEqual(config_with_port_in_host.get_full_url(), "http://localhost:8080")
        self.assertEqual(config_with_port_in_host.get_full_url("test"), "http://localhost:8080/test")

if __name__ == '__main__':
    unittest.main()
