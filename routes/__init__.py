from flask import render_template, jsonify
from database import check_database_health


def register_routes(app):
    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/api/health")
    def health_check():
        """
        API endpoint to check application and database health.

        Returns:
            JSON response with health status of the application and database.
        """
        result = check_database_health()
        status_code = 200 if result["status"] == "connected" else 503

        return (
            jsonify(
                {
                    "application": "running",
                    "database": result,
                }
            ),
            status_code,
        )
