import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from dotenv import load_dotenv
import os
from services.import_service import ImportService
from gui_web.auth import register_login_routes, login_required, admin_required
from models import db
from models.project_model import Project
import logging

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# Set SQLALCHEMY_DATABASE_URI from environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

#the session cookie is a browser session cookie and will be deleted when the browser is closed
app.config['SESSION_PERMANENT'] = False

# Initialize SQLAlchemy with app
db.init_app(app)

# Register login/logout routes
register_login_routes(app)

# Configure logging
logging.basicConfig(
    filename='depreciation_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.route('/')
# Add login_required to home page
@login_required
def home():
    role = session.get('role', 'user')
    return render_template('index.html', role=role)

@app.route('/import')
@admin_required
def import_page():
    return render_template('import.html')

@app.route('/projects')
def projects_page():
    project_fields = list(Project.__dataclass_fields__.keys())
    return render_template('projects.html', project_fields=project_fields)

@app.route('/admin')
@admin_required
def admin_page():
    return render_template('admin.html')

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
    try:
        results = ProjectManagementService.search_projects(
            project_id=project_id or None,
            branch=branch or None,
            operations=operations or None,
            description=description or None
        )
        # Convert results to dicts for JSON serialization
        project_fields = list(Project.__dataclass_fields__.keys())
        projects = []
        for proj in results:
            # If proj is a Project instance, convert to dict
            if hasattr(proj, '__dict__'):
                proj_dict = proj.__dict__
            elif isinstance(proj, dict):
                proj_dict = proj
            elif isinstance(proj, (list, tuple)):
                # Fallback: try to map to keys
                keys = project_fields
                proj_dict = dict(zip(keys[:len(proj)], proj))
            else:
                continue  # Skip this item if we can't convert it
                
            # Ensure all expected fields exist
            for field in project_fields:
                if field not in proj_dict:
                    proj_dict[field] = None
                    
            projects.append(proj_dict)
        return jsonify(projects)
    except Exception as e:
        app.logger.error(f"Error in search_projects: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/admin/create-user', methods=['POST'])
@admin_required
def admin_create_user():
    from services.user_service import UserService
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    if not username or not password or not role:
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400
    user, error = UserService.create_user(username, password, role)
    if user:
        return jsonify({'success': True, 'message': 'User created successfully.'})
    else:
        return jsonify({'success': False, 'message': error or 'Failed to create user.'}), 400

@app.route('/admin/search-users')
@admin_required
def admin_search_users():
    query = request.args.get('query', '')
    from services.user_service import UserService
    users = UserService.search_users(query)
    # Return id, username, and role name for each user
    return jsonify([
        {'id': u.id, 'username': u.username, 'role': u.role.name if u.role else None}
        for u in users
    ])

@app.route('/admin/delete-users', methods=['POST'])
@admin_required
def admin_delete_users():
    data = request.get_json()
    user_ids = data.get('user_ids', [])
    from services.user_service import UserService
    success, message = UserService.delete_users(user_ids)
    return jsonify({'success': success, 'message': message})

@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

@app.route('/project-investments/<project_id>')
@login_required
def get_project_investments(project_id):
    """
    Returns investment and depreciation data for a given project as JSON.
    """
    from services.project_management_service import ProjectManagementService
    data = ProjectManagementService.get_project_investments(project_id)
    return jsonify(data)

@app.route('/project-depreciations/<project_id>')
@login_required
def get_project_depreciations(project_id):
    from services.project_management_service import ProjectManagementService
    data = ProjectManagementService.get_calculated_project_depreciations(project_id)
    return jsonify(data)

@app.route('/api/projects/<project_id>/calculate-depreciations', methods=['POST'])
@login_required
def calculate_depreciations(project_id):
    try:
        # Call the existing calculation service
        from services.calculation_service import CalculationService
        method_type = CalculationService.handle_depreciation_calculation(project_id)
        # Return the method_type for debugging
        return jsonify({
            'success': True, 
            'method_type': method_type,
            'message': f"Debug info: Depreciation method type is '{method_type}'"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/projects/<project_id>/recalculate-depreciations', methods=['POST'])
@login_required
def recalculate_depreciations(project_id):
    try:        
        from db.repository_factory import RepositoryFactory
        depreciation_repo = RepositoryFactory.create_depreciation_repository()
        depreciation_repo.delete_calculated_depreciations(project_id)
        
        # Then calculate new ones
        from services.calculation_service import CalculationService
        method_type = CalculationService.handle_depreciation_calculation(project_id)
        
        # Return the method_type for debugging
        return jsonify({
            'success': True,
            'method_type': method_type,
            'message': f"Debug info: Depreciation method type is '{method_type}'"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/projects/<project_id>/has-calculated-depreciations')
@login_required
def has_calculated_depreciations(project_id):
    try:
        from services.project_management_service import ProjectManagementService
        # Use ProjectManagementService to check depreciations
        has_depreciations = ProjectManagementService.get_project_depreciations(project_id)
        return jsonify({'has_calculated_depreciations': has_depreciations['has_depreciations']})
    except Exception as e:
        return jsonify({'has_calculated_depreciations': False, 'error': str(e)})

@app.route('/api/projects/<project_id>/save-investments', methods=['POST'])
@login_required
def save_investments_and_depreciation(project_id):
    """
    Endpoint to save investments and depreciation years/months for a project.
    Expects JSON body with keys like investment_<year>, depr_start_<year>, depr_month_<year>.
    """
    try:
        data = request.get_json() or {}

        # Parse investments and depreciation starts from data
        investments = {}
        depreciation_starts = {}
        for key, value in data.items():
            if key.startswith('investment_'):
                year = key.split('_', 1)[1]
                investments[year] = value
            elif key.startswith('depr_start_'):
                year = key.split('_', 2)[2] if key.count('_') == 2 else key.split('_', 1)[1]
                if year not in depreciation_starts:
                    depreciation_starts[year] = [None, None]
                depreciation_starts[year][0] = value
            elif key.startswith('depr_month_'):
                year = key.split('_', 2)[2] if key.count('_') == 2 else key.split('_', 1)[1]
                if year not in depreciation_starts:
                    depreciation_starts[year] = [None, None]
                depreciation_starts[year][1] = value
        # Convert depreciation_starts values to tuples
        depreciation_starts = {k: tuple(v) for k, v in depreciation_starts.items()}

        # Save using the service
        from services.project_management_service import ProjectManagementService
        result = ProjectManagementService.save_investments_and_depreciation(project_id, investments, depreciation_starts)

        # Log the result from the service function
        logging.debug(f"Result from save_investments_and_depreciation for project {project_id}: {result}")

        return jsonify({'success': True, 'message': 'Investments and depreciation data saved.'})
    except Exception as e:
        logging.error(f"Error saving investments and depreciation for project {project_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/profile')
@login_required
def profile_page():
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(debug=True)
