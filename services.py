import yt_dlp
import logging
from .transcription_service import TranscriptionFactory
from .utils import update_progress, validate_bv_id, get_max_video_duration
import os
from dotenv import load_dotenv
import retry
from tenacity import retry, stop_after_attempt, wait_fixed

load_dotenv()
# 全局变量定义
FASTER_WHISPER_MODEL_PATH = os.path.join(os.path.dirname(__file__), os.getenv('FASTER_WHISPER_MODEL_PATH'))

# 从环境变量获取 Bilibili cookies
BILIBILI_COOKIES = os.getenv('BILIBILI_COOKIES')


def download_bilibili_audio(bv_id):
    duration = None
    try:
        bv_id = validate_bv_id(bv_id)
    except ValueError as e:
        update_progress(bv_id, '下载失败', str(e))
        return None, None, None, duration

    update_progress(bv_id, '正在获取视频信息')
    url = f"https://www.bilibili.com/video/{bv_id}"
    ydl_opts = {
        'outtmpl': '%(id)s_%(title)s.%(ext)s',
        'format': 'bestaudio/best',
        'postprocessors': [],  # 移除后处理器
        'quiet': False,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'cookies': BILIBILI_COOKIES
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            update_progress(bv_id, '正在分析可用音频格式')
            meta = ydl.extract_info(url, download=False)
            
            # 检查视频时长
            duration = meta.get('duration')
            max_duration = get_max_video_duration()
            if duration and duration > max_duration:
                raise ValueError(f"视频时长 ({duration}秒) 超过允许的最大时长 ({max_duration}秒)")
                
            formats = meta.get('formats', [])
            
            if not formats:
                raise Exception("未找到可用的音频格式")

            update_progress(bv_id, '正在下载音频')
            info = ydl.extract_info(url, download=True)
            update_progress(bv_id, '音频下载完成')
            
            duration = info.get('duration')
            if duration is None:
                logging.warning("无法从下载信息中获取持续时间")
                duration = 0

            # 获取下载的文件路径
            if info['requested_downloads']:
                file_path = info['requested_downloads'][0]['filepath']
            else:
                file_path = ydl.prepare_filename(info)

            return info['id'], info['title'], file_path, duration
        except yt_dlp.utils.DownloadError as e:
            logging.error(f"下载失败: {str(e)}")
            logging.exception("详细错误信息:")
            update_progress(bv_id, '下载失败', str(e))
            raise ValueError(str(e))
        except Exception as e:
            logging.error(f"未知错误: {str(e)}")
            logging.exception("详细错误信息:")
            update_progress(bv_id, '下载失败', str(e))
            raise

    return None, None, None, duration

def transcribe_audio(audio_filename, transcriber_type="faster_whisper"):
    logging.info(f"开始转写音频文件: {audio_filename}")
    logging.info(f"使用转写器类型: {transcriber_type}")
    
    try:
        transcriber = TranscriptionFactory.get_transcriber(transcriber_type, model_path=FASTER_WHISPER_MODEL_PATH)
        update_progress(audio_filename, '正在转写音频')
        transcript = transcriber.transcribe(audio_filename)
        update_progress(audio_filename, '转写完成')
        return transcript
    except Exception as e:
        logging.error(f"转写过程中发生错误: {str(e)}")
        logging.exception("详细错误信息:")
        update_progress(audio_filename, '转写失败', str(e))
        return None

def cleanup_files(audio_filename):
    try:
        os.remove(audio_filename)
        logging.info(f"已删除文件：{audio_filename}")
    except FileNotFoundError:
        logging.warning(f"文件未找到，无法删除：{audio_filename}")
    except PermissionError:
        logging.warning(f"没有权限删除文件：{audio_filename}")
    except Exception as e:
        logging.error(f"删除文件 {audio_filename} 时发生错误：{str(e)}")