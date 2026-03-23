import logging
from flask import Blueprint, jsonify, request
from backend.services import AuthService

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
auth_service = AuthService()

@auth_bp.route('/cookie', methods=['POST'])
def update_cookie():
    """
    Update Douyin cookie manually.
    Expects JSON body: {"cookie": "cookie_string_here"}
    """
    try:
        data = request.get_json()
        if not data or 'cookie' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing cookie in request body'
            }), 400
        
        cookie_str = data['cookie']
        result = auth_service.update_cookie(cookie_str)
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating cookie: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@auth_bp.route('/cookie', methods=['GET'])
def get_cookie():
    """
    Get current cookie status (masked for security).
    """
    try:
        result = auth_service.get_current_cookie()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Error getting cookie: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
