from alembic import context
from sqlalchemy import engine_from_config, pool

from sport_results.database import Base, enable_foreign_keys

config = context.config
target_metadata = Base.metadata


def run_migrations_online() -> None:
    engine = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with engine.connect() as connection:
        if connection.dialect.name == "sqlite":
            enable_foreign_keys(connection.connection, None)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
