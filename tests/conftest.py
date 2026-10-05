"""Keep unit tests off the developer .env and off a live Qdrant server."""

import os

os.environ["APP_ENV"] = "test"
os.environ["QDRANT_LOCATION"] = ":memory:"
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["AUTH_REQUIRED"] = "false"
