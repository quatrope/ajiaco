import datetime as dt
import inspect
import uuid

import datetime as dt
import uuid
from typing import Any, Optional

import sqlalchemy as sa
import sqlalchemy.orm as orm


# =============================================================================
# MODELS CREATION
# =============================================================================


def create_models(base_model_cls):

    # First the abstracts =====================================================
    class AJCModel(base_model_cls):
        """Base model with creation timestamp."""

        __abstract__ = True

        id: orm.Mapped[int] = orm.mapped_column(sa.Integer, primary_key=True)
        created_at: orm.Mapped[dt.datetime] = orm.mapped_column(
            sa.DateTime(timezone=True),
            default=lambda: dt.datetime.now(dt.timezone.utc),
            nullable=False,
        )

    class CodeAndExtraModel(AJCModel):
        """Abstract base model with UUID primary key and extra JSON data."""

        __abstract__ = True

        code: orm.Mapped[uuid.UUID] = orm.mapped_column(
            sa.String, unique=True, default=uuid.uuid4
        )
        extra: orm.Mapped[dict] = orm.mapped_column(sa.JSON, default=dict)
        extra_schema: orm.Mapped[Optional[bytes]] = orm.mapped_column(
            sa.String, nullable=True
        )

    # Store all models for easy return ========================================
    the_models = set()

    # SESSION =================================================================
    class Session(AJCModel):
        """Represents an experimental session."""

        __tablename__ = "sessions"

        experiment_name: orm.Mapped[str] = orm.mapped_column(
            sa.String, nullable=False
        )
        subjects_number: orm.Mapped[int] = orm.mapped_column(
            sa.Integer, nullable=False
        )
        demo: orm.Mapped[bool] = orm.mapped_column(sa.Boolean, nullable=False)
        len_stages: orm.Mapped[int] = orm.mapped_column(
            sa.Integer, nullable=False
        )

        # Relationships
        subjects: orm.Mapped[list["Subject"]] = orm.relationship(
            back_populates="session", cascade="all, delete-orphan"
        )
        rounds: orm.Mapped[list["Round"]] = orm.relationship(
            back_populates="session", cascade="all, delete-orphan"
        )

    the_models.add(Session)

    # SUBJECT =================================================================
    class Subject(AJCModel):
        """Represents a subject participating in a session."""

        __tablename__ = "subjects"

        session_code: orm.Mapped[uuid.UUID] = orm.mapped_column(
            sa.ForeignKey("sessions.code", ondelete="CASCADE"), nullable=False
        )
        current_stage: orm.Mapped[int] = orm.mapped_column(
            sa.Integer, nullable=False
        )

        # Relationships
        session: orm.Mapped[Session] = orm.relationship(
            back_populates="subjects"
        )
        roles: orm.Mapped[list["Role"]] = orm.relationship(
            back_populates="subject", cascade="all, delete-orphan"
        )

    the_models.add(Subject)

    # ROUND ===================================================================
    class Round(AJCModel):
        """Represents a round within a session."""

        __tablename__ = "rounds"

        session_code: orm.Mapped[uuid.UUID] = orm.mapped_column(
            sa.ForeignKey("sessions.code", ondelete="CASCADE"), nullable=False
        )
        game_name: orm.Mapped[str] = orm.mapped_column(
            sa.String, nullable=False
        )
        part: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)
        number: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)
        is_first: orm.Mapped[bool] = orm.mapped_column(
            sa.Boolean, nullable=False
        )
        is_last: orm.Mapped[bool] = orm.mapped_column(
            sa.Boolean, nullable=False
        )

        # Relationships
        session: orm.Mapped[Session] = orm.relationship(
            back_populates="rounds"
        )
        groups: orm.Mapped[list["Group"]] = orm.relationship(
            back_populates="round", cascade="all, delete-orphan"
        )

    the_models.add(Round)

    # GROUP ===================================================================
    class Group(AJCModel):
        """Represents a group of subjects within a round."""

        __tablename__ = "groups"

        round_code: orm.Mapped[uuid.UUID] = orm.mapped_column(
            sa.ForeignKey("rounds.code", ondelete="CASCADE"), nullable=False
        )

        # Relationships
        round: orm.Mapped[Round] = orm.relationship(back_populates="groups")
        roles: orm.Mapped[list["Role"]] = orm.relationship(
            back_populates="group", cascade="all, delete-orphan"
        )

    the_models.add(Group)

    # ROLE ====================================================================
    class Role(AJCModel):
        """Represents a subject's role within a group."""

        __tablename__ = "roles"

        group_code: orm.Mapped[uuid.UUID] = orm.mapped_column(
            sa.ForeignKey("groups.code", ondelete="CASCADE"), nullable=False
        )
        subject_code: orm.Mapped[uuid.UUID] = orm.mapped_column(
            sa.ForeignKey("subjects.code", ondelete="CASCADE"), nullable=False
        )
        number: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)
        in_group_number: orm.Mapped[int] = orm.mapped_column(
            sa.Integer, nullable=False
        )

        # Relationships
        group: orm.Mapped[Group] = orm.relationship(back_populates="roles")
        subject: orm.Mapped[Subject] = orm.relationship(back_populates="roles")
        stages: orm.Mapped[list["StageHistory"]] = orm.relationship(
            back_populates="role", cascade="all, delete-orphan"
        )

    the_models.add(Role)

    # HISTORY =================================================================
    class StageHistory(AJCModel):
        """Records the history of a subject's progression through stages."""

        __tablename__ = "stage_histories"

        role_code: orm.Mapped[uuid.UUID] = orm.mapped_column(
            sa.ForeignKey("roles.code", ondelete="CASCADE"), nullable=False
        )
        stage_idx: orm.Mapped[int] = orm.mapped_column(
            sa.Integer, nullable=False
        )
        timeout: orm.Mapped[float] = orm.mapped_column(
            sa.Float, nullable=False
        )
        enter_at: orm.Mapped[dt.datetime] = orm.mapped_column(
            sa.DateTime(timezone=True), nullable=False
        )
        expire_at: orm.Mapped[dt.datetime] = orm.mapped_column(
            sa.DateTime(timezone=True), nullable=False
        )
        exit_at: orm.Mapped[Optional[dt.datetime]] = orm.mapped_column(
            sa.DateTime(timezone=True), nullable=True
        )
        timed_out: orm.Mapped[bool] = orm.mapped_column(
            sa.Boolean, nullable=False, default=False
        )

        # Relationships
        role: orm.Mapped[Role] = orm.relationship(back_populates="stages")

    the_models.add(StageHistory)

    return the_models
