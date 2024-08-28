from flask import request, jsonify, send_file, after_this_request
from .services import download_bilibili_audio, transcribe_audio, cleanup_files
from .utils import update_progress, get_progress_info, validate_bv_id
from .subtitle_utils import generate_srt
import tempfile
import os
import logging
import time
import os
import tempfile
import time
from flask import jsonify, send_file, after_this_request, current_app
from werkzeug.datastructures import Headers
from .subtitle_utils import generate_srt
import threading
import os
import tempfile
import time
from flask import jsonify, send_file, current_app, request
from .subtitle_utils import generate_srt
import logging
import atexit
from threading import Timer
from flask import request, jsonify, send_file, after_this_request, current_app
from .subtitle_utils import generate_srt
import tempfile
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

# 确保在模块级别定义 logger
logger = logging.getLogger(__name__)

# 存储需要删除的临时文件
temp_files_to_delete = set()

def delayed_file_delete(filename, delay=5):
    def delete_file():
        try:
            if os.path.exists(filename):
                os.unlink(filename)
                logger.info(f"Successfully removed temporary file: {filename}")
            temp_files_to_delete.discard(filename)
        except Exception as e:
            logger.error(f"Failed to remove temporary file: {filename}. Error: {str(e)}")

    Timer(delay, delete_file).start()

def cleanup_temp_files():
    for filename in list(temp_files_to_delete):
        try:
            if os.path.exists(filename):
                os.unlink(filename)
                logger.info(f"Cleanup: removed temporary file: {filename}")
        except Exception as e:
            logger.error(f"Cleanup: failed to remove temporary file: {filename}. Error: {str(e)}")
    temp_files_to_delete.clear()

atexit.register(cleanup_temp_files)

def register_routes(app):
    @app.route('/api/transcribe', methods=['POST'])
    def transcribe():
        data = request.json
        try:
            bv_number = validate_bv_id(data['bvId'])
            transcriber_type = data.get('transcriber_type', 'faster_whisper')
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        update_progress(bv_number, '开始处理')
        bvid, title, audio_filename, duration = download_bilibili_audio(bv_number)
        if not audio_filename or not os.path.exists(audio_filename):
            return jsonify({'error': '音频下载失败或文件不存在'}), 400

        update_progress(bv_number, '开始音频转写')
        try:
            transcript = transcribe_audio(audio_filename, transcriber_type)
            if transcript is None:
                raise Exception("转写失败")
            
            cleanup_files(audio_filename)
            update_progress(bv_number, '处理完成')
            
            # 如果是云端 Faster Whisper，保持原样返回
            if transcriber_type == 'cloud_faster_whisper':
                formatted_transcript = transcript
            else:
                # 对于本地 Faster Whisper，保持原有的格式
                formatted_transcript = transcript
            
            return jsonify({
                'transcript': formatted_transcript,
                'title': title,
                'bvId': bv_number,
                'duration': duration
            })
        except Exception as e:
            cleanup_files(audio_filename)
            error_message = f"转写失败: {str(e)}"
            update_progress(bv_number, '转写失败', error_message)
            return jsonify({'error': error_message}), 500

    @app.route('/api/progress', methods=['GET'])
    def get_transcription_progress():
        try:
            bv_id = validate_bv_id(request.args.get('bvId'))
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        progress_info = get_progress_info(bv_id)
        if progress_info:
            return jsonify(progress_info)
        else:
            return jsonify({'error': '没有可用的进度信息'}), 404

    @app.route('/api/export_srt', methods=['POST'])
    def export_srt():
        # 使用模块级别的 logger，而不是尝试重新定义它
        logger.info("Received request to export SRT")
        data = request.json
        logger.debug(f"Received data: {data}")
        
        transcript = data.get('transcript')
        video_title = data.get('videoTitle')
        
        if not transcript or not video_title:
            logger.error("Missing required data for SRT export")
            return jsonify({'error': '缺少必要的数据'}), 400
        
        temp_filename = None
        try:
            logger.info("Generating SRT content")
            srt_content = generate_srt(transcript)
            logger.debug(f"Generated SRT content: {srt_content[:100]}...")  # Log first 100 characters
            
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.srt', encoding='utf-8-sig') as temp_file:
                temp_filename = temp_file.name
                logger.info(f"Saving SRT to temporary file: {temp_filename}")
                temp_file.write(srt_content)
            
            @after_this_request
            def remove_file(response):
                try:
                    if temp_filename and os.path.exists(temp_filename):
                        logger.info(f"Cleaning up temporary file: {temp_filename}")
                        os.remove(temp_filename)
                except Exception as e:
                    logger.error(f"Error removing temporary file: {str(e)}")
                return response

            logger.info(f"Sending file: {temp_filename}")
            return send_file(
                temp_filename, 
                as_attachment=True, 
                download_name=f"{video_title}.srt",
                mimetype='text/plain'
            )
        except Exception as e:
            logger.exception(f"Error occurred while generating SRT file: {str(e)}")
            if temp_filename and os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except Exception as cleanup_error:
                    logger.error(f"Error removing temporary file after exception: {str(cleanup_error)}")
            return jsonify({'error': f'生成 SRT 文件时发生错误: {str(e)}'}), 500

def init_app(app):
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)