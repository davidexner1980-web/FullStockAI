from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
import json
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@main_bp.route('/crypto')
def crypto():
    """Cryptocurrency predictions page"""
    return render_template('crypto.html')

@main_bp.route('/portfolio')
def portfolio():
    """Portfolio tracking page"""
    return render_template('portfolio.html')

@main_bp.route('/backtesting')
def backtesting():
    """Backtesting engine page"""
    return render_template('backtesting.html')

@main_bp.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    """User profile management"""
    profile_path = 'data/user_profiles.json'
    
    if request.method == 'POST':
        data = request.json
        profile_type = data.get('profile_type', 'moderate')
        
        # Load existing profiles
        profiles = {}
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profiles = json.load(f)
        
        # Update profile
        user_id = session.get('user_id', 'anonymous')
        profiles[user_id] = {
            'profile_type': profile_type,
            'signal_sensitivity': data.get('signal_sensitivity', 0.7),
            'position_sizing': data.get('position_sizing', 'moderate'),
            'oracle_tone': data.get('oracle_tone', 'balanced'),
            'notifications_enabled': data.get('notifications_enabled', True),
            'updated_at': json.dumps(datetime.utcnow(), default=str)
        }
        
        # Save profiles
        with open(profile_path, 'w') as f:
            json.dump(profiles, f, indent=2)
        
        return jsonify({'status': 'success'})
    
    else:
        # GET request - return current profile
        profiles = {}
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profiles = json.load(f)
        
        user_id = session.get('user_id', 'anonymous')
        profile = profiles.get(user_id, {
            'profile_type': 'moderate',
            'signal_sensitivity': 0.7,
            'position_sizing': 'moderate',
            'oracle_tone': 'balanced',
            'notifications_enabled': True
        })
        
        return jsonify(profile)
