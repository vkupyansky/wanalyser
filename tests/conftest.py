import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.update(
    BOT_TOKEN="123456789:" + secrets.token_urlsafe(32),
    BOT_NAME="isolated_test_bot",
    PG_DSN="postgresql://localhost/isolated_test",
    REDIS_URL="redis://127.0.0.1:6379/15",
    BASE_WEBHOOK_URL="https://example.invalid",
    WEBHOOK_SECRET=secrets.token_urlsafe(32),
)
