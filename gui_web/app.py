import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, flash
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
    if not file or file.filename == '':
        flash('No file selected!')
        return redirect(url_for('home'))
    try:
        # Save the uploaded file to a temporary location
        temp_path = os.path.join('/tmp', file.filename)
        file.save(temp_path)
        # Use the shared backend logic for importing projects
        ImportService.create_projects_from_dataframe(filepath=temp_path)
        flash('Projects imported successfully!')
    except Exception as e:
        flash(f'Error importing projects: {e}')
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
