"""Changes

Revision ID: f89dbbfd0b50
Revises: 3032d03b16ef
Create Date: 2024-11-18 15:26:10.593564

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f89dbbfd0b50'
down_revision = '3032d03b16ef'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ingredients', schema=None) as batch_op:
        batch_op.drop_index('ix_ingredients_name')
        batch_op.create_index(batch_op.f('ix_ingredients_name'), ['name'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ingredients', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ingredients_name'))
        batch_op.create_index('ix_ingredients_name', ['name'], unique=True)

    # ### end Alembic commands ###
