import os
import time
import json
import logging
from typing import List, Dict, Union, Any
from dotenv import load_dotenv
from gradio_client import Client, handle_file

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudFasterWhisperTranscriber:
    def __init__(self):
        self.use_proxy = os.getenv('USE_PROXY', 'False').lower() == 'true'
        self.proxy_url = os.getenv('PROXY_URL', 'http://127.0.0.1:7890')
        
        if self.use_proxy:
            self.original_http_proxy = os.environ.get('HTTP_PROXY')
            self.original_https_proxy = os.environ.get('HTTPS_PROXY')
            os.environ['HTTP_PROXY'] = self.proxy_url
            os.environ['HTTPS_PROXY'] = self.proxy_url

        for attempt in range(3):
            try:
                self.client = Client("magicsif/fasterwhisper")
                break
            except Exception as e:
                if attempt == 2:
                    self._restore_proxy_settings()
                    raise Exception(f"无法连接到 Hugging Face 空间: {str(e)}")
                time.sleep(5)

    def transcribe(self, audio_filename: str, language: str = "zh", initial_prompt: str = "以下是普通话的句子。", vad_filter: bool = True, min_silence_duration_ms: int = 500) -> List[Dict[str, Union[float, str]]]:
        if not os.path.exists(audio_filename):
            raise FileNotFoundError(f"音频文件未找到: {audio_filename}")

        try:
            logger.info(f"开始转写文件: {audio_filename}")
            
            result = self.client.predict(
                handle_file(audio_filename),
                language,
                initial_prompt,
                vad_filter,
                min_silence_duration_ms,
                api_name="/predict"
            )
            
            logger.info("转写完成，开始处理结果")
            return self._process_transcription(result)
        except Exception as e:
            logger.error(f"Cloud Faster Whisper 转写失败: {str(e)}")
            logger.error(f"音频文件路径: {audio_filename}")
            logger.error(f"文件是否存在: {os.path.exists(audio_filename)}")
            logger.error(f"文件大小: {os.path.getsize(audio_filename) if os.path.exists(audio_filename) else 'N/A'}")
            raise
        finally:
            self._restore_proxy_settings()

    def _process_transcription(self, result: Any) -> List[Dict[str, Union[float, str]]]:
        try:
            if isinstance(result, str):
                # 如果结果是字符串，尝试解析为 JSON
                result = json.loads(result)

            if not isinstance(result, (dict, list)):
                raise ValueError(f"未预期的结果类型: {type(result)}")

            # 如果结果是字典，假设它包含一个 'transcription' 键
            if isinstance(result, dict):
                transcription = result.get('transcription', [])
            else:
                # 如果结果已经是列表，直接使用
                transcription = result
            
            processed_result = []
            for segment in transcription:
                if isinstance(segment, dict) and all(key in segment for key in ['start', 'end', 'text']):
                    processed_result.append({
                        'start': float(segment['start']),
                        'end': float(segment['end']),
                        'text': segment['text'].strip()
                    })
                else:
                    logger.warning(f"跳过无效的片段: {segment}")

            logger.info(f"处理完成，共 {len(processed_result)} 个有效片段")
            return processed_result
        except Exception as e:
            logger.error(f"处理转写结果时发生错误: {str(e)}")
            logger.error(f"原始结果: {str(result)[:1000]}...")  # 记录前1000个字符
            raise

    def _restore_proxy_settings(self):
        if self.use_proxy:
            if self.original_http_proxy:
                os.environ['HTTP_PROXY'] = self.original_http_proxy
            else:
                os.environ.pop('HTTP_PROXY', None)
            
            if self.original_https_proxy:
                os.environ['HTTPS_PROXY'] = self.original_https_proxy
            else:
                os.environ.pop('HTTPS_PROXY', None)

    def __del__(self):
        self._restore_proxy_settings()