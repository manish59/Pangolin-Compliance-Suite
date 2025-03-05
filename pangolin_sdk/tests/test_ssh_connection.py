from pangolin_sdk.connections.ssh import SSHConnection, SSHConnectionConfig
from pangolin_sdk.constants import SSHAuthMethod
from pangolin_sdk.constants import ParamikoKey

encrypted_string = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jdHIAAAAGYmNyeXB0AAAAGAAAABBFDNLeBi
0DE+gKilvY41XtAAAAGAAAAAEAAAAzAAAAC3NzaC1lZDI1NTE5AAAAIKw3fe1oqESeOkMR
sSepvoavhuVIonjN9PZ//6hvUn3dAAAAsPjJVnhLoE9iIBHzhBqvWIIynjrFcE6v+HRQZn
ucpENLHBpa4DsXdxY3lIGwBUJMdSa/D0maKmLXW65ZRs8j9HeIsDVpRVCOWT4UKs+4cxGH
iFN8EHXmSbpP3oT3KHgK60qkH5227Xjy1dUcb93jnlMDHwFZV/5Sk2lT7vgk5+f+IBBzGc
tRZWJgKQHYAli/5cifYdRm1Xxtxm20IBToZW4qIVp0uR+MEFukndjGtxjC
-----END OPENSSH PRIVATE KEY-----"""

def test_ssh_connection():
    config = SSHConnectionConfig(
        name="test_ssh_connection",
        host="192.168.4.237",
        port=22,
        username="jarvis",
        # password="dydqu9-pastab-ravkIj",
        auth_method=SSHAuthMethod.PUBLIC_KEY,
        pkey_type=ParamikoKey.RSA,
        encrypted_key_str=encrypted_string,
        passphrase="M@nish123",
    )
    connection = SSHConnection(config)
    connection.execute("ls -l")
    result = connection.get_last_result()
    print(result)

if __name__ == "__main__":
    test_ssh_connection()
