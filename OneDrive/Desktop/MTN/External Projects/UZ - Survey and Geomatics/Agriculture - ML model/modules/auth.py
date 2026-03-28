"""
modules/auth.py
─────────────────────────────────────────────────────────────────────────
Authentication and access control for the Flask dashboard and API.

Provides:
  • login_required   — decorator for web page routes (session-based)
  • api_key_required — decorator for API routes (header-based)
  • check_credentials — validates username/password
"""

import os
import functools
from flask import request, jsonify, redirect, url_for, session

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# ─── Credentials from environment ────────────────────────────────────────────

DASHBOARD_USERNAME = os.environ.get("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "OptiflowAqua2025")
API_KEY = os.environ.get("API_KEY", "oaq-optiflow-2025-secret-key")


# ─── Credential validation ───────────────────────────────────────────────────

def check_credentials(username: str, password: str) -> bool:
    """Validate username and password against environment configuration."""
    return (
        username.strip().lower() == DASHBOARD_USERNAME.strip().lower()
        and password.strip() == DASHBOARD_PASSWORD.strip()
    )


# ─── Web route protection (session-based) ────────────────────────────────────

def login_required(f):
    """
    Decorator that redirects unauthenticated users to /login.
    Checks for 'authenticated' flag in the Flask session.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


# ─── API route protection (key-based) ────────────────────────────────────────

def api_key_required(f):
    """
    Decorator that requires a valid API key in the request.
    
    The key can be provided as:
      • X-API-Key header
      • api_key query parameter
      • Or if the user has an active web session (authenticated via login)
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow if user has a valid web session
        if session.get("authenticated"):
            return f(*args, **kwargs)

        # Check for API key
        key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if key and key == API_KEY:
            return f(*args, **kwargs)

        return jsonify({
            "status": "error",
            "message": "Unauthorized. Provide a valid API key via X-API-Key header or api_key parameter."
        }), 401

    return decorated_function
