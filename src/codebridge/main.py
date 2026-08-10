"""CodeBridge main entry point."""

from __future__ import annotations

import uvicorn

from codebridge.api.app import create_app
from codebridge.config import get_settings
from codebridge.logging import configure_logging


def run() -> None:
    """Start the CodeBridge server."""
    settings = get_settings()
    configure_logging(settings.codebridge_log_level)

    app = create_app()

    uvicorn.run(
        app,
        host=settings.codebridge_host,
        port=settings.codebridge_port,
        log_config=None,  # We handle logging ourselves
        access_log=False,
    )


if __name__ == "__main__":
    run()
