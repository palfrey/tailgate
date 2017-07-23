"""Add books

Revision ID: 40e76ca5423b
Revises: 0520c81bb824
Create Date: 2017-07-23 15:54:23.119666

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '40e76ca5423b'
down_revision = '0520c81bb824'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('book',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('published', sa.DateTime(), nullable=False),
        sa.Column('author', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['author'], ['author.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('author', sa.Column('last_updated', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('author', 'last_updated')
    op.drop_table('book')
