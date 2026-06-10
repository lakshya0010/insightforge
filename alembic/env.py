from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.config import settings
import os

# Import Base so Alembic knows your table definitions
from app.core.database import Base

# Import all models — even if unused, this import registers
# the models with Base.metadata. Without this, Alembic won't
# see your tables and will generate empty migrations.
from app.models import user  # noqa: F401
from app.models import statement #noqa: F401

config = context.config
fileConfig(config.config_file_name)

# This is what Alembic compares against the real DB to figure
# out what's changed and what migration to generate.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=settings.DATABASE_URL_SYNC
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
