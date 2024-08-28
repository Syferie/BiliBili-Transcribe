import os
from dotenv import load_dotenv
from gradio_client import Client
import time
import json
from typing import List, Dict, Union

load_dotenv()

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

    def transcribe(self, audio_filename) -> List[Dict[str, Union[float, str]]]:
        if not os.path.exists(audio_filename):
            raise FileNotFoundError(f"音频文件未找到: {audio_filename}")

        try:
            result = self.client.predict(
                audio_filename,
                api_name="/predict"
            )
            return self._process_transcription(result)
        except Exception as e:
            print(f"Cloud Faster Whisper 转写失败: {str(e)}")
            raise
        finally:
            self._restore_proxy_settings()

    def _process_transcription(self, result: Union[str, List]) -> List[Dict[str, Union[float, str]]]:
        if isinstance(result, str):
            try:
                transcription = json.loads(result)
            except json.JSONDecodeError:
                raise ValueError("无法解析转写结果")
        elif isinstance(result, list):
            transcription = result
        else:
            raise ValueError(f"未预期的结果类型: {type(result)}")

        processed_result = []
        for segment in transcription:
            processed_result.append({
                'start': float(segment['start']),
                'end': float(segment['end']),
                'text': segment['text'].strip()
            })
        return processed_result

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