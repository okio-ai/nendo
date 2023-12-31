"""initial migration

Revision ID: 4d18e8964428
Revises: 
Create Date: 2023-11-22 16:10:47.482481

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql.sqltypes import Text
import sqlalchemy as sa
import nendo
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4d18e8964428'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('blobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('visibility', postgresql.ENUM('public', 'private', 'deleted', name='visibility'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resource', nendo.library.model.JSONEncodedDict(astext_type=Text()), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('collections',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('collection_type', sa.String(), nullable=True),
    sa.Column('visibility', postgresql.ENUM('public', 'private', 'deleted', name='visibility'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('meta', nendo.library.model.JSONEncodedDict(astext_type=Text()), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tracks',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('track_type', sa.String(), nullable=True),
    sa.Column('visibility', postgresql.ENUM('public', 'private', 'deleted', name='visibility'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('images', nendo.library.model.JSONEncodedDict(astext_type=Text()), nullable=True),
    sa.Column('resource', nendo.library.model.JSONEncodedDict(astext_type=Text()), nullable=True),
    sa.Column('meta', nendo.library.model.JSONEncodedDict(astext_type=Text()), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('collection_collection_relationships',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=True),
    sa.Column('target_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('relationship_type', sa.String(), nullable=True),
    sa.Column('meta', nendo.library.model.JSONEncodedDict(astext_type=Text()), nullable=True),
    sa.ForeignKeyConstraint(['source_id'], ['collections.id'], ),
    sa.ForeignKeyConstraint(['target_id'], ['collections.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('plugin_data',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('track_id', sa.UUID(), nullable=True),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('plugin_name', sa.String(), nullable=False),
    sa.Column('plugin_version', sa.String(), nullable=False),
    sa.Column('key', sa.String(), nullable=False),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['track_id'], ['tracks.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('track_collection_relationships',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=True),
    sa.Column('target_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('relationship_type', sa.String(), nullable=True),
    sa.Column('meta', nendo.library.model.JSONEncodedDict(astext_type=Text()), nullable=True),
    sa.Column('relationship_position', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['source_id'], ['tracks.id'], ),
    sa.ForeignKeyConstraint(['target_id'], ['collections.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('track_track_relationships',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=True),
    sa.Column('target_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('relationship_type', sa.String(), nullable=True),
    sa.Column('meta', nendo.library.model.JSONEncodedDict(astext_type=Text()), nullable=True),
    sa.ForeignKeyConstraint(['source_id'], ['tracks.id'], ),
    sa.ForeignKeyConstraint(['target_id'], ['tracks.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('track_track_relationships')
    op.drop_table('track_collection_relationships')
    op.drop_table('plugin_data')
    op.drop_table('collection_collection_relationships')
    op.drop_table('tracks')
    op.drop_table('collections')
    op.drop_table('blobs')
    # ### end Alembic commands ###
