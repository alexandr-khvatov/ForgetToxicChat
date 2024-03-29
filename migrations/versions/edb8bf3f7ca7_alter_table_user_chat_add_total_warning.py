"""alter table user_chat add total_warning

Revision ID: edb8bf3f7ca7
Revises: 09d8f34ccc28
Create Date: 2023-04-28 12:14:24.632924

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'edb8bf3f7ca7'
down_revision = '09d8f34ccc28'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_chat', sa.Column('total_warnings', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_chat', 'total_warnings')
    # ### end Alembic commands ###
