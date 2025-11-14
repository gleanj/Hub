#!/usr/bin/env python3
"""
Configuration loader for HubSpot CTF tools
Loads credentials from .env file for security
"""

import os
from pathlib import Path
from typing import Optional

def load_env_file():
    """Load .env file from project root"""
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'

    if not env_file.exists():
        return {}

    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars

# Load environment variables
_env_vars = load_env_file()

# Export configuration
HUBSPOT_ACCESS_TOKEN = _env_vars.get('HUBSPOT_ACCESS_TOKEN', '')
HUBSPOT_API_KEY = _env_vars.get('HUBSPOT_API_KEY', '')
TARGET_PORTAL_ID = _env_vars.get('TARGET_PORTAL_ID', '46962361')
TARGET_CONTACT_ID = _env_vars.get('TARGET_CONTACT_ID', '1')
MY_PORTAL_ID = _env_vars.get('MY_PORTAL_ID', '')
HUBSPOT_COOKIES = _env_vars.get('HUBSPOT_COOKIES', '')

def get_api_key() -> Optional[str]:
    """Get API key, preferring access token over API key"""
    return HUBSPOT_ACCESS_TOKEN or HUBSPOT_API_KEY

def get_auth_header() -> dict:
    """Get authorization header for API requests"""
    api_key = get_api_key()
    if not api_key:
        return {}
    return {'Authorization': f'Bearer {api_key}'}

def has_credentials() -> bool:
    """Check if we have valid credentials configured"""
    return bool(HUBSPOT_ACCESS_TOKEN or HUBSPOT_API_KEY)

def print_config_status():
    """Print configuration status (without exposing keys)"""
    print("Configuration Status:")
    print(f"  Access Token: {'[OK] Set' if HUBSPOT_ACCESS_TOKEN else '[X] Not set'}")
    print(f"  API Key: {'[OK] Set' if HUBSPOT_API_KEY else '[X] Not set'}")
    print(f"  Target Portal: {TARGET_PORTAL_ID}")
    print(f"  Target Contact: {TARGET_CONTACT_ID}")
    print(f"  My Portal ID: {MY_PORTAL_ID if MY_PORTAL_ID else '[X] Not set'}")
    print(f"  Session Cookies: {'[OK] Set' if HUBSPOT_COOKIES else '[X] Not set'}")

if __name__ == '__main__':
    print_config_status()
