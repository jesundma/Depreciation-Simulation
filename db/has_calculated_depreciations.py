from flask import Blueprint, jsonify

has_calculated_depreciations_bp = Blueprint('has_calculated_depreciations', __name__)

@has_calculated_depreciations_bp.route('/api/projects/<project_id>/has-calculated-depreciations', methods=['GET'])
def has_calculated_depreciations(project_id):
    # Placeholder logic: Always return false for now
    return jsonify({"has_calculated_depreciations": False})
