"""add yandex music fileds

Revision ID: e4a1561c2b63
Revises: 
Create Date: 2025-04-05 21:22:09.221527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4a1561c2b63'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tracks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('telegram_id', sa.BigInteger(), nullable=True),
    sa.Column('telegram_access_hash', sa.BigInteger(), nullable=True),
    sa.Column('telegram_file_reference', sa.LargeBinary(), nullable=True),
    sa.Column('spotify_id', sa.String(), nullable=True),
    sa.Column('ymusic_id', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('artist', sa.String(), nullable=False),
    sa.Column('cover_url', sa.String(), nullable=False),
    sa.Column('used_times', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('spotify_access_token', sa.String(), nullable=True),
    sa.Column('spotify_refresh_token', sa.String(), nullable=True),
    sa.Column('spotify_refresh_at', sa.Integer(), nullable=True),
    sa.Column('ymusic_token', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    op.drop_table('tracks')
    # ### end Alembic commands ###
