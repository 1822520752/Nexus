"""扩展记忆表以支持三层记忆架构

Revision ID: 001
Revises: 
Create Date: 2025-03-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加新字段到 memories 表
    with op.batch_alter_table('memories', schema=None) as batch_op:
        # 会话追踪字段
        batch_op.add_column(sa.Column('session_id', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('conversation_id', sa.String(100), nullable=True))
        
        # 知识图谱支持字段
        batch_op.add_column(sa.Column('entities', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('entity_ids', sa.JSON(), nullable=True))
        
        # 记忆分类字段
        batch_op.add_column(sa.Column('category', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('keywords', sa.JSON(), nullable=True))
        
        # 记忆状态字段
        batch_op.add_column(sa.Column('status', sa.String(20), nullable=False, server_default='active'))
        batch_op.add_column(sa.Column('is_consolidated', sa.Boolean(), nullable=False, server_default='0'))
        
        # 向量嵌入字段
        batch_op.add_column(sa.Column('embedding_id', sa.String(100), nullable=True))
        
        # 修改时间字段类型（从 String 改为 DateTime）
        batch_op.alter_column('last_accessed_at',
                              existing_type=sa.String(50),
                              type_=sa.DateTime(timezone=True),
                              existing_nullable=True)
        batch_op.alter_column('expires_at',
                              existing_type=sa.String(50),
                              type_=sa.DateTime(timezone=True),
                              existing_nullable=True)
        
        # 修改 JSON 字段类型（从 Text 改为 JSON）
        batch_op.alter_column('tags',
                              existing_type=sa.Text(),
                              type_=sa.JSON(),
                              existing_nullable=True)
        batch_op.alter_column('metadata',
                              existing_type=sa.Text(),
                              type_=sa.JSON(),
                              existing_nullable=True)
        
        # 添加索引
        batch_op.create_index('ix_memories_session_id', ['session_id'], unique=False)
        batch_op.create_index('ix_memories_conversation_id', ['conversation_id'], unique=False)
        batch_op.create_index('ix_memories_category', ['category'], unique=False)
        batch_op.create_index('ix_memories_status', ['status'], unique=False)
        batch_op.create_index('ix_memories_embedding_id', ['embedding_id'], unique=False)


def downgrade() -> None:
    # 删除索引
    with op.batch_alter_table('memories', schema=None) as batch_op:
        batch_op.drop_index('ix_memories_embedding_id')
        batch_op.drop_index('ix_memories_status')
        batch_op.drop_index('ix_memories_category')
        batch_op.drop_index('ix_memories_conversation_id')
        batch_op.drop_index('ix_memories_session_id')
        
        # 恢复字段类型
        batch_op.alter_column('metadata',
                              existing_type=sa.JSON(),
                              type_=sa.Text(),
                              existing_nullable=True)
        batch_op.alter_column('tags',
                              existing_type=sa.JSON(),
                              type_=sa.Text(),
                              existing_nullable=True)
        batch_op.alter_column('expires_at',
                              existing_type=sa.DateTime(timezone=True),
                              type_=sa.String(50),
                              existing_nullable=True)
        batch_op.alter_column('last_accessed_at',
                              existing_type=sa.DateTime(timezone=True),
                              type_=sa.String(50),
                              existing_nullable=True)
        
        # 删除新增字段
        batch_op.drop_column('embedding_id')
        batch_op.drop_column('is_consolidated')
        batch_op.drop_column('status')
        batch_op.drop_column('keywords')
        batch_op.drop_column('category')
        batch_op.drop_column('entity_ids')
        batch_op.drop_column('entities')
        batch_op.drop_column('conversation_id')
        batch_op.drop_column('session_id')
