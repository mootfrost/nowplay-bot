from abc import ABC, abstractmethod

from app.models import Track


class MusicProviderStrategy(ABC):
    def __init__(self, user_id):
        self.user_id = user_id

    @abstractmethod
    async def get_tracks(self, token) -> list[Track]:
        pass

    @abstractmethod
    async def handle_token(self) -> str:
        pass

    @abstractmethod
    async def fetch_track(self, track: Track) -> Track:
        pass

    @abstractmethod
    def song_link(self, track: Track):
        pass

    @abstractmethod
    def track_id(self, track: Track):
        pass
