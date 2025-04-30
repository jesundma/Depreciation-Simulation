import sys
import os
from dotenv import load_dotenv

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

FLASK_URL = os.getenv("FLASK_URL", "http://127.0.0.1:5000")

# run.py
from gui.main_window import main_window
from flask import Flask, jsonify, request
from services.project_service import ProjectService
from db.database_service import DatabaseService

app = Flask(__name__)

@app.route('/api/projects', methods=['POST'])
def create_project():
    data = request.json
    try:
        project = Project(
            project_id=data['project_id'],
            branch=data['branch'],
            operations=data['operations'],
            description=data['description']
        )
        ProjectService.save_to_database(project)
        return jsonify({"message": "Project saved successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    try:
        project = ProjectService.load_from_database(project_id)
        if project:
            return jsonify(project.__dict__), 200
        else:
            return jsonify({"error": "Project not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/database/setup', methods=['POST'])
def setup_database():
    try:
        DatabaseService().setup_database()
        return jsonify({"message": "Database setup completed successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/search', methods=['GET'])
def search_projects():
    project_id = request.args.get('project_id')
    branch = request.args.get('branch')
    operations = request.args.get('operations')
    description = request.args.get('description')

    try:
        query = "SELECT * FROM projects WHERE TRUE"
        params = []

        if project_id:
            query += " AND project_id = %s"
            params.append(project_id)
        if branch:
            query += " AND branch ILIKE %s"
            params.append(f"%{branch}%")
        if operations:
            query += " AND operations ILIKE %s"
            params.append(f"%{operations}%")
        if description:
            query += " AND description ILIKE %s"
            params.append(f"%{description}%")

        db_service = DatabaseService()
        results = db_service.execute_query(query, params, fetch=True)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "flask":
        # Run Flask server in development mode
        app.run(debug=True, host="127.0.0.1", port=5000)
    else:
        # Run the desktop application
        main_window()
