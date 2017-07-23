"""Basic user and author

Revision ID: 0520c81bb824
Revises: 
Create Date: 2017-07-23 14:21:01.402263

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0520c81bb824'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('author',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('token_secret', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('follows',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('follows', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['follows'], ['author.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'follows')
    )

def downgrade():
    op.drop_table('follows')
    op.drop_table('user')
    op.drop_table('author')

