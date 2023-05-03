"""alter table user_chat add messege_counter

Revision ID: cae3f95f47a2
Revises: 1438b1a78590
Create Date: 2023-05-03 16:07:08.179650

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cae3f95f47a2'
down_revision = '1438b1a78590'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chat', sa.Column('message_counter', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('chat', 'message_counter')
    # ### end Alembic commands ###