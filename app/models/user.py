from typing import Optional

from app.models import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)

    spotify_auth: Mapped[dict] = mapped_column(JSON, default={})
    ymusic_auth: Mapped[dict] = mapped_column(JSON, default={})


__all__ = ['User']
