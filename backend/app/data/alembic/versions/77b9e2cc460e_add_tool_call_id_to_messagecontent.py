"""add tool call id to messagecontent

Revision ID: 77b9e2cc460e
Revises: 2e992f3f46ab
Create Date: 2024-10-17 13:01:41.983876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77b9e2cc460e'
down_revision: Union[str, None] = '2e992f3f46ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('message_content', sa.Column('tool_call_id', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('message_content', 'tool_call_id')
    # ### end Alembic commands ###
