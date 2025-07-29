import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    # Use the provided DATABASE_URL or fall back to individual components
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@database-flor-instance-1.csqth4u0zi2z.us-west-2.rds.amazonaws.com:5432/postgres")
    
    # Individual components for backward compatibility
    HOST = os.getenv("DB_HOST", "database-flor-instance-1.csqth4u0zi2z.us-west-2.rds.amazonaws.com")
    PORT = os.getenv("DB_PORT", "5432")
    NAME = os.getenv("DB_NAME", "postgres")
    USER = os.getenv("DB_USER", "postgres")
    PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    
    @classmethod
    def get_connection_string(cls):
        return cls.DATABASE_URL
    
    @classmethod
    def get_sync_connection_string(cls):
        """Get connection string for synchronous psycopg2"""
        # Convert asyncpg URL to psycopg2 format
        if cls.DATABASE_URL.startswith("postgresql+asyncpg://"):
            return cls.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        return cls.DATABASE_URL

class AzureConfig:
    """Azure AD/Entra ID configuration"""
    TENANT_ID = os.getenv("AZURE_TENANT_ID", "b8869792-ee44-4a05-a4fb-b6323a34ca35")
    CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "b7fb9a3b-efe3-418d-8fa8-243487a42530")
    CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "your-client-secret")
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    ISSUER = f"{AUTHORITY}/v2.0"
    JWKS_URL = f"{AUTHORITY}/discovery/v2.0/keys"

class EntraSSOConfig:
    """Entra SSO configuration for alternate middleware"""
    TENANT_ID = os.getenv("VITE_ENTRA_SSO_TENANT_ID", "b8869792-ee44-4a05-a4fb-b6323a34ca35")
    CLIENT_ID = os.getenv("VITE_ENTRA_SSO_CLIENT_ID", "5e71dda2-3628-4942-b3cc-06370c2c0459")
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    ISSUER = f"https://sts.windows.net/{TENANT_ID}/"
    JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys" 