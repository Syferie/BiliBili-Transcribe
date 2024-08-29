import logging
from threading import Lock, Timer
import os
import time

# 全局变量
TRANSCRIPTION_PROGRESS = {}
PROGRESS_LOCK = Lock()
cleanup_timer = None

def setup_logging(app):
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    logging.basicConfig(level=getattr(logging, log_level))
    logger = logging.getLogger(__name__)
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)

def update_progress(filename, status, details=None):
    with PROGRESS_LOCK:
        TRANSCRIPTION_PROGRESS[filename] = {
            'status': status,
            'details': details,
            'timestamp': time.time()
        }

def get_progress_info(filename):
    with PROGRESS_LOCK:
        return TRANSCRIPTION_PROGRESS.get(filename, {})

def cleanup_progress():
    current_time = time.time()
    with PROGRESS_LOCK:
        for filename in list(TRANSCRIPTION_PROGRESS.keys()):
            if current_time - TRANSCRIPTION_PROGRESS[filename].get('timestamp', 0) > 3600:  # 1 hour
                del TRANSCRIPTION_PROGRESS[filename]
    
    global cleanup_timer
    cleanup_timer = Timer(3600, cleanup_progress)
    cleanup_timer.start()
    logging.info("Cleanup complete. Next cleanup scheduled.")

def start_cleanup_timer():
    global cleanup_timer
    cleanup_timer = Timer(3600, cleanup_progress)
    cleanup_timer.start()
    logging.info("Initial cleanup timer started.")

def stop_cleanup_timer():
    global cleanup_timer
    if cleanup_timer:
        cleanup_timer.cancel()
        logging.info("Cleanup timer stopped.")

def validate_bv_id(bv_id):
    import re
    if not re.match(r'^BV[a-zA-Z0-9]{10}$', bv_id):
        raise ValueError("无效的BV号")
    return bv_id

def format_time(seconds):
    """Convert seconds to SRT time format."""
    import datetime
    return str(datetime.timedelta(seconds=seconds)).replace('.', ',')[:-3]

def generate_srt(transcript):
    """Generate SRT formatted subtitles from transcript."""
    srt_content = ""
    for index, segment in enumerate(transcript, start=1):
        start_time = format_time(segment['start'])
        end_time = format_time(segment['end'])
        text = segment['text'].strip()
        
        srt_content += f"{index}\n{start_time} --> {end_time}\n{text}\n\n"
    
    return srt_content.strip()

def save_srt(content, filename):
    """Save SRT content to a file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

def create_direct_connection():
    import httpx
    return httpx.HTTPTransport(proxy=None)

def get_enabled_transcribers():
    return {
        'faster_whisper': os.getenv('ENABLE_LOCAL_FASTER_WHISPER', 'true').lower() == 'true',
        'openai': os.getenv('ENABLE_OPENAI_WHISPER', 'true').lower() == 'true',
        'cloud_faster_whisper': os.getenv('ENABLE_CLOUD_FASTER_WHISPER', 'true').lower() == 'true'
    }

def get_max_video_duration():
    return int(os.getenv('MAX_VIDEO_DURATION', 3600))  # 默认为1小时