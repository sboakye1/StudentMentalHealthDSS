import os
from flask import Flask

from config import Config, create_app


def main() -> None:
    app = create_app()
    
    # Verify template and static folders are set correctly
    print(f"[INFO] App root path: {app.root_path}")
    print(f"[INFO] Template folder: {app.template_folder}")
    print(f"[INFO] Static folder: {app.static_folder}")
    print(f"[INFO] Template folder exists: {os.path.exists(app.template_folder) if app.template_folder else 'N/A'}")
    print(f"[INFO] Static folder exists: {os.path.exists(app.static_folder) if app.static_folder else 'N/A'}")
    
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "False").lower() in {"1", "true", "yes"},
        use_reloader=False,  # Disable reloader to avoid subprocess issues
    )


if __name__ == "__main__":
    main()
