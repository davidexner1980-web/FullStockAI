from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_socketio import emit
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main dashboard with comprehensive stock prediction interface"""
    return render_template('index.html')

@main_bp.route('/crypto')
def crypto():
    """Cryptocurrency prediction dashboard"""
    return render_template('crypto.html')

@main_bp.route('/portfolio')
def portfolio():
    """Portfolio management and analysis"""
    return render_template('portfolio.html')

@main_bp.route('/backtesting')
def backtesting():
    """Strategy backtesting interface"""
    return render_template('backtesting.html')

@main_bp.route('/oracle')
def oracle():
    """Oracle mode mystical insights interface"""
    return render_template('oracle.html')

@main_bp.route('/strategic')
def strategic():
    """Strategic intelligence dashboard"""
    return render_template('strategic.html')