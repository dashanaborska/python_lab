import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
    )
    op.create_table(
        "athletes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column(
            "sport_id",
            sa.Integer(),
            sa.ForeignKey("sports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint("name", "sport_id", name="uq_athlete_sport"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_athlete_name"),
    )
    op.create_table(
        "results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "athlete_id",
            sa.Integer(),
            sa.ForeignKey("athletes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "score >= 0 AND score <= 100", name="ck_result_score"
        ),
    )


def downgrade() -> None:
    op.drop_table("results")
    op.drop_table("athletes")
    op.drop_table("sports")
