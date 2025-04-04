from typing import Optional

from app.models import Base
from sqlalchemy.orm import Mapped, mapped_column


class Track(Base):
    __tablename__ = 'tracks'
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[Optional[int]]
    telegram_md5_checksum: Mapped[Optional[str]]
    spotify_id: Mapped[str]
    name: Mapped[str]
    artist: Mapped[str]
    cover_url: Mapped[str]
    used_times: Mapped[str]




__all__ = ['Track']