"""Add version and version_id to recipes table

Revision ID: c74a444c1459
Revises: ebe558af2392
Create Date: 2024-11-20 11:16:10.702153

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c74a444c1459'
down_revision = 'ebe558af2392'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('original_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'recipes', ['original_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('original_id')
        batch_op.drop_column('version')

    # ### end Alembic commands ###
