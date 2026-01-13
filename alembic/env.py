# alembic/env.py
from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from app.core.config import settings
from alembic import context
from app.db.database import Base

from app.models.models import (
    User,
    Tweet,
    Like,
    Retweet,
    Reply,
    Follow,
    Hashtag,
    TweetHashtag,
    Mention,
    Notification,
    Bookmark,
    FacialExpression,
)

target_metadata = Base.metadata

# Config Alembic
config = context.config

# Loggers
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

DATABASE_URL = str(settings.database_url)
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section), #type: ignore
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()