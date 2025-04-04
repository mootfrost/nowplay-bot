from app.models import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    spotify_access_token: Mapped[str] = mapped_column(String())
    spotify_refresh_token: Mapped[str]
    spotify_refresh_at: Mapped[int]


__all__ = ['User']