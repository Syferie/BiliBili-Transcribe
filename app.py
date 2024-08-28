from flask import Flask
from flask_cors import CORS
from .routes import register_routes
from .utils import setup_logging, start_cleanup_timer, stop_cleanup_timer
import atexit
import signal
import sys
import logging

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    CORS(app)

    setup_logging(app)
    register_routes(app)

    start_cleanup_timer()
    atexit.register(stop_cleanup_timer)

    return app

def signal_handler(sig, frame):
    logger.info('Interrupt received. Starting cleanup...')
    stop_cleanup_timer()
    logger.info('Cleanup complete. Exiting...')
    sys.exit(0)

def cleanup_on_exit():
    logger.info("Performing final cleanup before exit...")
    stop_cleanup_timer()
    # 在这里添加任何其他需要的清理代码
    logger.info("Final cleanup complete.")

app = create_app()

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
atexit.register(cleanup_on_exit)

if __name__ == "__main__":
    logger.info("Starting Flask application...")
    app.run(debug=False)