import sys
import threading
from pathlib import Path
import time

import uvicorn
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / "src"))
load_dotenv()

from src.authen_authori.interface import main


def start_api_server() -> None:
    uvicorn.run(
        "src.app:app",
        host="127.0.0.1",
        port=8011,
        log_level="error",
        access_log=False,
    )


if __name__ == "__main__":
    # 1. Start server in background thread
    server_thread = threading.Thread(target=start_api_server, daemon=True)
    server_thread.start()

    time.sleep(1)  # Wait for the server to start

    # 2. Launch Main CLI Interface
    main()