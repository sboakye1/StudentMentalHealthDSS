import os
from flask import Flask

from config import create_app


def main() -> None:
    app = create_app()
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "False").lower() in {"1", "true", "yes"},
    )


if __name__ == "__main__":
    main()
