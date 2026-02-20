"""test alembic

Revision ID: dd89913c9bd3
Revises: 1f6ebc20aa15
Create Date: 2026-02-20 15:33:42.487955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd89913c9bd3'
down_revision: Union[str, Sequence[str], None] = '1f6ebc20aa15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
