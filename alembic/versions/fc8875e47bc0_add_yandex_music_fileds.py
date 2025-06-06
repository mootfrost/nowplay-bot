"""add yandex music fileds

Revision ID: fc8875e47bc0
Revises: e4a1561c2b63
Create Date: 2025-04-08 23:34:01.812378

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc8875e47bc0'
down_revision: Union[str, None] = 'e4a1561c2b63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tracks', sa.Column('telegram_reference', sa.JSON(), nullable=True))
    op.add_column('tracks', sa.Column('yt_id', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tracks', 'yt_id')
    op.drop_column('tracks', 'telegram_reference')
    # ### end Alembic commands ###
