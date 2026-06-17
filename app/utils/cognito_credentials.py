"""Cognito credential helpers for the Prompt Engineering Workshop."""

import boto3
import os


def get_cognito_credentials(identity_pool_id: str, region: str = "us-east-1") -> dict:
    """Get temporary AWS credentials from a Cognito Identity Pool.

    Returns a dict with AccessKeyId, SecretKey, SessionToken, and Expiration.
    """
    client = boto3.client("cognito-identity", region_name=region)
    identity_response = client.get_id(IdentityPoolId=identity_pool_id)
    identity_id = identity_response["IdentityId"]

    credentials_response = client.get_credentials_for_identity(IdentityId=identity_id)
    return credentials_response.get("Credentials", {})
