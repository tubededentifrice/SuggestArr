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
    
    # Create Flask app with proper static folder configuration
    # NOTE: We're setting static_url_path to empty string to ensure static files 
    # are served directly from the root/subpath without adding an extra /static segment
    application = Flask(__name__, static_folder=static_folder, static_url_path='')
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
    # Create a handler that will serve index.html for our SPA routes
    def serve_index():
        """Serve the index.html file"""
        logger.debug(f"Serving index.html for root path {subpath}/")
        return send_from_directory(app.static_folder, 'index.html')
    
    # Register all routes that should serve the SPA
    # Define all routes that should be handled by the SPA
    app.add_url_rule(f'{subpath}/', 'serve_index', serve_index)
    app.add_url_rule(f'{subpath}/requests', 'serve_requests', serve_index)
    
    # Also add a catch-all route for anything else that should be handled by the SPA
    # Add routes for CSS, JS and other static files
    @app.route(f'{subpath}/css/<path:filename>')
    def serve_css(filename):
        logger.debug(f"Serving CSS: {filename}")
        return send_from_directory(os.path.join(app.static_folder, 'css'), filename)
    
    @app.route(f'{subpath}/js/<path:filename>')
    def serve_js(filename):
        logger.debug(f"Serving JS: {filename}")
        return send_from_directory(os.path.join(app.static_folder, 'js'), filename)
    
    @app.route(f'{subpath}/img/<path:filename>')
    def serve_img(filename):
        logger.debug(f"Serving image: {filename}")
        return send_from_directory(os.path.join(app.static_folder, 'img'), filename)
    
    @app.route(f'{subpath}/images/<path:filename>')
    def serve_images(filename):
        logger.debug(f"Serving image from images/: {filename}")
        return send_from_directory(os.path.join(app.static_folder, 'images'), filename)
    
    @app.route(f'{subpath}/favicon.ico')
    def serve_favicon():
        logger.debug("Serving favicon.ico")
        return send_from_directory(app.static_folder, 'favicon.ico')
        
    # Catch-all route for any other URL under the SUBPATH
    @app.route(f'{subpath}/<path:path>')
    def serve_frontend(path):
        """Serve static files or redirect to index.html for SPA routes"""
        logger.debug(f"Catch-all requested path: {path}")
        
        # Check if this is a static asset - we should look for these specific assets
        for asset_dir in ['css', 'js', 'img', 'images']:
            if path.startswith(f"{asset_dir}/"):
                asset_path = path[len(f"{asset_dir}/"):]
                full_asset_path = os.path.join(app.static_folder, asset_dir, asset_path)
                if os.path.exists(full_asset_path) and os.path.isfile(full_asset_path):
                    logger.debug(f"Serving {asset_dir} asset: {asset_path}")
                    return send_from_directory(os.path.join(app.static_folder, asset_dir), asset_path)
        
        # If not a static asset or it doesn't exist, serve the SPA (index.html)
        logger.debug(f"No static asset found, serving index.html for path: {path}")
        return send_from_directory(app.static_folder, 'index.html')
    
    # Redirect from root to SUBPATH if SUBPATH is configured
    if subpath:
        @app.route('/')
        def redirect_to_subpath():
            """Redirect from root to SUBPATH"""
            logger.debug(f"Redirecting from / to {subpath}/")
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