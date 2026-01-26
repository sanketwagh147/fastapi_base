"""
Example custom secrets loader for AWS Secrets Manager.

To implement your own provider:
    1. Subclass SecretsLoader
    2. Set mode=SecretsMode.CUSTOM
    3. Override load_secret(name) -> str | None
"""

import json

from app.core.secrets import SecretsLoader, SecretsMode

__all__ = ["AWSSecretsLoader"]


class AWSSecretsLoader(SecretsLoader):
    """
    AWS Secrets Manager loader.

    Requires: pip install boto3

    Usage:
        loader = AWSSecretsLoader(secret_name="myapp/prod")
        configure_secrets(loader=loader)
    """

    def __init__(
        self,
        secret_name: str,
        region: str = "us-east-1",
        **kwargs,
    ):
        super().__init__(mode=SecretsMode.CUSTOM, **kwargs)
        self.secret_name = secret_name
        self.region = region
        self._client = None
        self._cache: dict | None = None

    @property
    def client(self):
        if self._client is None:
            try:
                import boto3
            except ImportError as exc:
                msg = "boto3 required: pip install boto3"
                raise ImportError(msg) from exc
            self._client = boto3.client("secretsmanager", region_name=self.region)
        return self._client

    def load_secret(self, name: str) -> str | None:
        """Load secret from AWS. Secrets stored as JSON: {"KEY": "value"}"""
        if self._cache is None:
            try:
                response = self.client.get_secret_value(SecretId=self.secret_name)
                self._cache = json.loads(response["SecretString"])
            except Exception:
                self._cache = {}
        return self._cache.get(name)


# =============================================================================
# Template for other providers (Vault, Azure, GCP):
# =============================================================================
#
# class MySecretsLoader(SecretsLoader):
#     def __init__(self, **kwargs):
#         super().__init__(mode=SecretsMode.CUSTOM, **kwargs)
#         # Initialize your client
#
#     def load_secret(self, name: str) -> str | None:
#         # Fetch and return secret value
#         return your_client.get(name)
