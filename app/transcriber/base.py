from abc import ABC, abstractmethod


class BaseTranscriber(ABC):
    """ Base class for all transcribers """
    @abstractmethod
    def transcribe(self, audio_url: str) -> dict:
        pass
        
    @abstractmethod
    def transcribe_from_base64(self, audio_base64: str) -> dict:
        """Транскрибирует аудио из base64 строки"""
        pass


