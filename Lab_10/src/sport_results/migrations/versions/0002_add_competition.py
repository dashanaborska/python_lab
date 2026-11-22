import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("results") as batch:
        batch.add_column(sa.Column("competition_name", sa.String(120), nullable=True))
        batch.add_column(sa.Column("competition_date", sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("results") as batch:
        batch.drop_column("competition_date")
        batch.drop_column("competition_name")
