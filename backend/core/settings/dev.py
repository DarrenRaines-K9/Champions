from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Relaxed throttles in dev — 100x prod rate so local work isn't blocked.
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "2000/minute",
    "user": "10000/minute",
    "auth": "500/minute",
    "signup": "1000/minute",
}

# Shorter token lifetimes make it easy to test the refresh flow locally.
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    **SIMPLE_JWT,  # noqa: F405
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=1),
}
