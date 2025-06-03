import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
from services.import_service import ImportService

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

@app.route('/')
def home():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True)
