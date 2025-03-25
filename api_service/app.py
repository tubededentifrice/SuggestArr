"""
Main Flask application for managing environment variables and running processes.
"""
from concurrent.futures import ThreadPoolExecutor
import os
from flask import Flask, send_from_directory, url_for, redirect
from flask_cors import CORS
from asgiref.wsgi import WsgiToAsgi
import logging
import atexit

from api_service.utils.utils import AppUtils
from api_service.config.logger_manager import LoggerManager
from api_service.config.config import load_env_vars

from api_service.blueprints.jellyfin.routes import jellyfin_bp
from api_service.blueprints.seer.routes import seer_bp
from api_service.blueprints.plex.routes import plex_bp
from api_service.blueprints.automation.routes import automation_bp
from api_service.blueprints.logs.routes import logs_bp
from api_service.blueprints.config.routes import config_bp

executor = ThreadPoolExecutor(max_workers=3)
logger = LoggerManager.get_logger("APP") 
logger.info(f"Current log level: {logging.getLevelName(logger.getEffectiveLevel())}")

# App Factory Pattern for modularity and testability
def create_app():
    """
    Create and configure the Flask application.
    """
    # Load environment variables first to get SUBPATH
    env_vars = load_env_vars()
    subpath = env_vars.get('SUBPATH') or ''
    
    # Strip leading/trailing slashes for consistency
    if subpath:
        subpath = '/' + subpath.strip('/')
        logger.info(f"Application configured with SUBPATH: {subpath}")

    if AppUtils.is_last_worker():
        AppUtils.print_welcome_message() # Print only for last worker

    # Configure Flask app with the correct static folder
    static_folder = '../client/dist'
    
    # Configure the app with the static folder
    # It's important that the static_url_path is set to subpath (without /static)
    # This ensures that all static files are served correctly from the SUBPATH
    application = Flask(__name__, static_folder=static_folder, static_url_path=subpath)
    CORS(application)

    # Register blueprints with proper subpath prefixes
    application.register_blueprint(jellyfin_bp, url_prefix=f'{subpath}/api/jellyfin')
    application.register_blueprint(seer_bp, url_prefix=f'{subpath}/api/seer')
    application.register_blueprint(plex_bp, url_prefix=f'{subpath}/api/plex')
    application.register_blueprint(automation_bp, url_prefix=f'{subpath}/api/automation')
    application.register_blueprint(logs_bp, url_prefix=f'{subpath}/api')
    application.register_blueprint(config_bp, url_prefix=f'{subpath}/api/config')

    # Store subpath in the app config for templates and other uses
    application.config['SUBPATH'] = subpath

    # Register routes
    register_routes(application, subpath)

    # Load environment variables at startup
    AppUtils.load_environment()

    return application

def register_routes(app, subpath): # pylint: disable=redefined-outer-name
    """
    Register the application routes.
    """
    # Main route with SUBPATH support
    @app.route(f'{subpath}/', defaults={'path': ''})
    @app.route(f'{subpath}/<path:path>')
    def serve_frontend(path):
        """
        Serve the built frontend's index.html or any other static file.
        """
        # We don't need to reset static_folder here as it's already set correctly
        if path == "" or not os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            # Serve the requested file (static assets like JS, CSS, images, etc.)
            return send_from_directory(app.static_folder, path)
    
    # Redirect from root to SUBPATH if SUBPATH is configured
    if subpath:
        @app.route('/')
        def redirect_to_subpath():
            """Redirect from root to SUBPATH"""
            return redirect(subpath + '/')

app = create_app()
asgi_app = WsgiToAsgi(app)
env_vars = load_env_vars()
if env_vars.get('CRON_TIMES'):
    from api_service.config.cron_jobs import start_cron_job
    start_cron_job(env_vars)

def close_log_handlers():
    for handler in logging.root.handlers[:]:
        handler.close()
        logging.root.removeHandler(handler)
atexit.register(close_log_handlers)

if __name__ == '__main__':
    port = int(os.environ.get('SUGGESTARR_PORT', 5000))
    app.run(host='0.0.0.0', port=port)