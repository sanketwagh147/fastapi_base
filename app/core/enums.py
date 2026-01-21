"""Enumeration definitions for the"""

from enum import Enum


class Environment(str, Enum):
    """Application environment types."""

    LOCAL = "local"
    DEV = "dev"
    UAT = "uat"
    UATBIZ = "uatbiz"
    PREPROD = "preprod"
    SANITY = "sanity"
    PROD = "prod"
