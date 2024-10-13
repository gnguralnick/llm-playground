"""convert config to json type

Revision ID: 63e93b6411a7
Revises: 44c8787a686e
Create Date: 2024-10-10 20:49:20.041718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '63e93b6411a7'
down_revision: Union[str, None] = '44c8787a686e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('chat', 'config')
    op.add_column('chat', sa.Column('config', sa.JSON(), nullable=True))
    op.drop_column('message', 'config')
    op.add_column('message', sa.Column('config', sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('message', 'config')
    op.add_column('message', sa.Column('config', sa.PickleType(), nullable=True))
    op.drop_column('chat', 'config')
    op.add_column('chat', sa.Column('config', sa.PickleType(), nullable=True))
    # ### end Alembic commands ###