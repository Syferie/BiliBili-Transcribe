import os
from faster_whisper import WhisperModel
from openai import OpenAI
import httpx
import logging
from gradio_client import Client
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .cloud_faster_whisper import CloudFasterWhisperTranscriber
from .utils import create_direct_connection

class ProxiedSession(requests.Session):
    def __init__(self, proxies=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxies = proxies

class FasterWhisperTranscriber:
    def __init__(self, model_path, device="cpu", compute_type="int8"):
        try:
            logging.info(f"Initializing Faster Whisper model from path: {model_path}")
            logging.info(f"Device: {device}, Compute type: {compute_type}")
            if os.path.isdir(model_path):
                self.model = WhisperModel(model_path, device=device, compute_type=compute_type, local_files_only=True)
            else:
                raise ValueError(f"Invalid model path: {model_path}")
            logging.info("Faster Whisper model initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing Faster Whisper model: {str(e)}")
            logging.exception("Detailed error information:")
            raise

    def transcribe(self, audio_path):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            segments, _ = self.model.transcribe(
                audio_path, 
                language="zh", 
                initial_prompt="以下是普通话的句子。",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            transcription = []
            for segment in segments:
                transcription.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text
                })
            return transcription
        except Exception as e:
            logging.error(f"Error transcribing audio: {str(e)}")
            raise

class OpenAITranscriber:
    def __init__(self):
        self.base_url = os.getenv("OPENAI_API_BASE_URL")
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.base_url or not self.api_key:
            raise ValueError("未设置 OPENAI_API_BASE_URL 或 OPENAI_API_KEY 环境变量")

    def create_direct_connection(self):
        return httpx.HTTPTransport(proxy=None)

    def transcribe(self, audio_filename):
        with httpx.Client(transport=self.create_direct_connection()) as http_client:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                http_client=http_client,
                timeout=300.0
            )

            with open(audio_filename, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )

                return str(response)

class TranscriptionFactory:
    @staticmethod
    def get_transcriber(transcriber_type, model_path=None):
        if transcriber_type == "faster_whisper":
            if not model_path:
                raise ValueError("Model path must be provided for Faster Whisper transcriber")
            return FasterWhisperTranscriber(model_path=model_path)
        elif transcriber_type == "openai":
            return OpenAITranscriber()
        elif transcriber_type == "cloud_faster_whisper":
            return CloudFasterWhisperTranscriber()
        else:
            raise ValueError(f"Unsupported transcriber type: {transcriber_type}")