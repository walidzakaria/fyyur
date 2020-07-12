"""empty message

Revision ID: 687ac91e53a5
Revises: ddb0de4e4950
Create Date: 2020-07-12 04:35:35.254431

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '687ac91e53a5'
down_revision = 'ddb0de4e4950'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('available_from', sa.Integer(), nullable=True))
    op.add_column('Artist', sa.Column('available_till', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Artist', 'available_till')
    op.drop_column('Artist', 'available_from')
    # ### end Alembic commands ###
