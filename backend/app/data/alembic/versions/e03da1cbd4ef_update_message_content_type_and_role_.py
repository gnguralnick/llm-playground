"""update message content type and role enums

Revision ID: e03da1cbd4ef
Revises: 77b9e2cc460e
Create Date: 2024-10-17 14:28:39.904489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e03da1cbd4ef'
down_revision: Union[str, None] = '77b9e2cc460e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('''ALTER TYPE messagecontenttype ADD VALUE 'TOOL_CALL' ''')
    op.execute('''ALTER TYPE messagecontenttype ADD VALUE 'TOOL_RESULT' ''')
    op.execute('''ALTER TYPE role ADD VALUE 'TOOL' ''')


def downgrade() -> None:
    # convert all existing TOOL_CALL and TOOL_RESULT messages to TEXT
    op.execute('''
        UPDATE message_content
        SET type = 'TEXT'
        WHERE type = 'TOOL_CALL' OR type = 'TOOL_RESULT'
    ''')
    op.execute('''ALTER TYPE messagecontenttype DROP VALUE 'TOOL_CALL' ''')
    op.execute('''ALTER TYPE messagecontenttype DROP VALUE 'TOOL_RESULT' ''')
    
    # convert all existing TOOL roles to USER
    op.execute('''
        UPDATE message
        SET role = 'USER'
        WHERE role = 'TOOL'
    ''')
    op.execute('''ALTER TYPE role DROP VALUE 'TOOL' ''')
