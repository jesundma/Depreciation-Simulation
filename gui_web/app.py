import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import os
from services.import_service import ImportService
from gui_web.auth import register_login_routes, login_required

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# Register login/logout routes
register_login_routes(app)

@app.route('/')
# Add login_required to home page
@login_required
def home():
    return render_template('index.html')

@app.route('/import')
def import_page():
    return render_template('import.html')

@app.route('/projects')
def projects_page():
    return render_template('projects.html')

@app.route('/import-projects', methods=['POST'])
def import_projects():
    file = request.files.get('file')
    messages = []
    def status_callback(msg):
        messages.append(msg)
    if not file or file.filename == '':
        return jsonify({'success': False, 'messages': ['No file selected!']}), 400
    try:
        # Save the uploaded file to a temporary location
        temp_path = os.path.join('/tmp', file.filename)
        file.save(temp_path)
        # Use the shared backend logic for importing projects
        ImportService.create_projects_from_dataframe(filepath=temp_path, status_callback=status_callback)
        success = True
    except Exception as e:
        messages.append(f'Error importing projects: {e}')
        success = False
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return jsonify({'success': success, 'messages': messages})

@app.route('/import-investments', methods=['POST'])
def import_investments():
    file = request.files.get('file')
    messages = []
    def status_callback(msg):
        messages.append(msg)
    if not file or file.filename == '':
        return jsonify({'success': False, 'messages': ['No file selected!']}), 400
    try:
        temp_path = os.path.join('/tmp', file.filename)
        file.save(temp_path)
        ImportService.create_investments_from_dataframe(filepath=temp_path, status_callback=status_callback)
        success = True
    except Exception as e:
        messages.append(f'Error importing investments: {e}')
        success = False
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return jsonify({'success': success, 'messages': messages})

@app.route('/import-depreciation-starts', methods=['POST'])
def import_depreciation_starts():
    file = request.files.get('file')
    messages = []
    def status_callback(msg):
        messages.append(msg)
    if not file or file.filename == '':
        return jsonify({'success': False, 'messages': ['No file selected!']}), 400
    try:
        temp_path = os.path.join('/tmp', file.filename)
        file.save(temp_path)
        ImportService.create_depreciation_starts_from_dataframe(filepath=temp_path, status_callback=status_callback)
        success = True
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        messages.append(f'Error importing depreciation starts: {e}')
        messages.append(f'Traceback: {tb}')
        # If the error is about a malformed tuple, try to show more context
        if hasattr(e, 'args') and e.args and 'tuple' in str(e.args[0]):
            messages.append('Possible malformed tuple detected. Check the debug output in the backend logs for tuple samples.')
        success = False
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return jsonify({'success': success, 'messages': messages})

@app.route('/search-projects')
def search_projects():
    project_id = request.args.get('project_id')
    branch = request.args.get('branch')
    operations = request.args.get('operations')
    description = request.args.get('description')
    from services.project_management_service import ProjectManagementService
    results = ProjectManagementService.search_projects(
        project_id=project_id or None,
        branch=branch or None,
        operations=operations or None,
        description=description or None
    )
    # Convert results to dicts for JSON serialization
    projects = []
    for proj in results:
        # If proj is a Project instance, convert to dict
        if hasattr(proj, '__dict__'):
            projects.append(proj.__dict__)
        elif isinstance(proj, dict):
            projects.append(proj)
        elif isinstance(proj, (list, tuple)):
            # Fallback: try to map to keys
            keys = ['project_id', 'branch', 'operations', 'description', 'depreciation_method']
            projects.append(dict(zip(keys, proj)))
    return jsonify(projects)

if __name__ == '__main__':
    app.run(debug=True)
