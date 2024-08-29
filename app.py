from flask import Flask, jsonify
from flask_cors import CORS
from .routes import register_routes
from .utils import setup_logging, start_cleanup_timer, stop_cleanup_timer, get_rate_limit_seconds
import atexit
import signal
import sys
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    CORS(app)

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{get_rate_limit_seconds()} per second"]
    )
    limiter.init_app(app)

    setup_logging(app)
    register_routes(app)

    start_cleanup_timer()
    atexit.register(stop_cleanup_timer)

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            'error': '速率限制：请求过于频繁，请稍后再试',
            'code': 'RATE_LIMIT_EXCEEDED',
            'retryAfter': get_rate_limit_seconds()
        }), 429

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

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
atexit.register(cleanup_on_exit)

app = create_app()

if __name__ == "__main__":
    logger.info("Starting Flask application...")
    app.run(debug=False)