"""add model config to chat and message

Revision ID: 89ecbbadfb7d
Revises: 1c9c41905fb6
Create Date: 2024-10-01 17:11:24.963673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89ecbbadfb7d'
down_revision: Union[str, None] = '1c9c41905fb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chat', sa.Column('config', sa.PickleType(), nullable=True))
    op.add_column('message', sa.Column('config', sa.PickleType(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('message', 'config')
    op.drop_column('chat', 'config')
    # ### end Alembic commands ###
