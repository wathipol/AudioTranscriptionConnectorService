from abc import ABC, abstractmethod


class BaseTranscriber(ABC):
    """ Base class for all transcribers """
    @abstractmethod
    def transcribe(self, audio_url: str) -> dict:
        pass


