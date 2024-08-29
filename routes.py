import os
import tempfile
import logging
from threading import Timer
from flask import request, jsonify, send_file, after_this_request, current_app
from .services import download_bilibili_audio, transcribe_audio, cleanup_files
from .utils import update_progress, get_progress_info, validate_bv_id, get_enabled_transcribers, get_max_video_duration
from .subtitle_utils import generate_srt

# 设置日志
logging.basicConfig(level=logging.INFO)
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

def register_routes(app):
    @app.route('/api/transcribe', methods=['POST'])
    def transcribe():
        data = request.json
        try:
            bv_number = validate_bv_id(data['bvId'])
            transcriber_type = data.get('transcriber_type', 'faster_whisper')
        except ValueError as e:
            return jsonify({'error': str(e), 'code': 'INVALID_BV_ID'}), 400
        
        update_progress(bv_number, '开始处理')
        duration = None
        try:
            bvid, title, audio_filename, duration = download_bilibili_audio(bv_number)
            
            if duration is None:
                raise ValueError('无法获取视频时长')

            max_duration = get_max_video_duration()
            if duration > max_duration:
                raise ValueError(f"视频时长 ({duration}秒) 超过允许的最大时长 ({max_duration}秒)")

            if not audio_filename or not os.path.exists(audio_filename):
                raise ValueError('音频下载失败或文件不存在')

            update_progress(bv_number, '开始音频转写')
            transcript = transcribe_audio(audio_filename, transcriber_type)
            if transcript is None:
                raise Exception("转写失败")
            
            cleanup_files(audio_filename)
            update_progress(bv_number, '处理完成')
            
            formatted_transcript = transcript
            
            return jsonify({
                'transcript': formatted_transcript,
                'title': title,
                'bvId': bv_number,
                'duration': duration
            })

        except ValueError as e:
            error_message = str(e)
            if "视频时长" in error_message:
                return jsonify({
                    'error': '视频时长超出限制',
                    'details': error_message,
                    'code': 'DURATION_EXCEEDED',
                    'maxDuration': get_max_video_duration(),
                    'videoDuration': duration if duration is not None else 0
                }), 400
            else:
                return jsonify({
                    'error': '下载失败',
                    'details': error_message,
                    'code': 'DOWNLOAD_FAILED'
                }), 400

        except Exception as e:
            if 'audio_filename' in locals() and audio_filename:
                cleanup_files(audio_filename)
            error_message = f"转写失败: {str(e)}"
            update_progress(bv_number, '转写失败', error_message)
            return jsonify({
                'error': '转录过程中发生错误',
                'details': error_message,
                'code': 'TRANSCRIPTION_FAILED'
            }), 500

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
        logger.info("Received request to export SRT")
        data = request.json
        transcript = data.get('transcript')
        video_title = data.get('videoTitle')
        
        if not transcript or not video_title:
            logger.error("Missing required data for SRT export")
            return jsonify({'error': '缺少必要的数据'}), 400
        
        try:
            srt_content = generate_srt(transcript)
            
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.srt', encoding='utf-8-sig') as temp_file:
                temp_filename = temp_file.name
                temp_file.write(srt_content)
            
            @after_this_request
            def remove_file(response):
                delayed_file_delete(temp_filename)
                return response

            return send_file(
                temp_filename, 
                as_attachment=True, 
                download_name=f"{video_title}.srt",
                mimetype='text/plain'
            )
        except Exception as e:
            logger.exception(f"Error occurred while generating SRT file: {str(e)}")
            return jsonify({'error': f'生成 SRT 文件时发生错误: {str(e)}'}), 500

    @app.route('/api/enabled_transcribers', methods=['GET'])
    def get_enabled_transcribers_route():
        enabled_transcribers = get_enabled_transcribers()
        return jsonify(enabled_transcribers)
        
def init_app(app):
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)