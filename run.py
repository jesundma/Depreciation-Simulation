import sys
import os

# Ensure the project root is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# run.py
from gui.main_window import main_window
from flask import Flask, jsonify, request
from services.project_service import ProjectService
from db.project_repositary import DatabaseService

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

if __name__ == "__main__":
    app = main_window()
    app.run(debug=True)
