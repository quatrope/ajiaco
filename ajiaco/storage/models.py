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


def _utcnow():
    return dt.datetime.now(dt.timezone.utc)


def create_models(base_model_cls):

    # First the abstracts =====================================================
    class AJCModel(base_model_cls):
        """Base model with creation timestamp."""

        __abstract__ = True

        id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
        created_at: orm.Mapped[dt.datetime] = orm.mapped_column(
            sa.DateTime(timezone=True),
            default=_utcnow,
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
    class SessionModel(CodeAndExtraModel):
        """Represents an experimental session."""

        __tablename__ = "ajc_sessions"

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

    the_models.add(SessionModel)

    # SUBJECT =================================================================
    class SubjectModel(CodeAndExtraModel):
        """Represents a subject participating in a session."""

        __tablename__ = "ajc_subjects"

        current_stage: orm.Mapped[int] = orm.mapped_column(
            sa.Integer, nullable=False
        )

        # Relationships
        session_id: orm.Mapped[int] = orm.mapped_column(
            sa.ForeignKey("ajc_sessions.id"), nullable=False
        )
        session: orm.Mapped[SessionModel] = orm.relationship(
            back_populates="subjects", lazy=False
        )

    the_models.add(SubjectModel)

    # ROUND ===================================================================
    class RoundModel(CodeAndExtraModel):
        """Represents a round within a session."""

        __tablename__ = "ajc_rounds"

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
        session_id: orm.Mapped[int] = orm.mapped_column(
            sa.ForeignKey("ajc_sessions.id"), nullable=False
        )
        session: orm.Mapped[SessionModel] = orm.relationship(
            back_populates="rounds", lazy=False
        )

    the_models.add(RoundModel)

    # GROUP ===================================================================
    class GroupModel(CodeAndExtraModel):
        """Represents a group of subjects within a round."""

        __tablename__ = "ajc_groups"

        # Relationships
        round_id: orm.Mapped[int] = orm.mapped_column(
            sa.ForeignKey("ajc_rounds.id"), nullable=False
        )
        round: orm.Mapped[RoundModel] = orm.relationship(
            back_populates="groups", lazy=False
        )

    the_models.add(GroupModel)

    # ROLE ====================================================================
    class Role(CodeAndExtraModel):
        """Represents a subject's role within a group."""

        __tablename__ = "ajc_roles"

        number: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)
        in_group_number: orm.Mapped[int] = orm.mapped_column(
            sa.Integer, nullable=False
        )

        group_id: orm.Mapped[int] = orm.mapped_column(
            sa.ForeignKey("ajc_groups.id"), nullable=False
        )
        group: orm.Mapped[GroupModel] = orm.relationship(
            back_populates="roles"
        )

        subject_id: orm.Mapped[int] = orm.mapped_column(
            sa.ForeignKey("ajc_subjects.id"), nullable=False
        )
        subject: orm.Mapped[SubjectModel] = orm.relationship(
            back_populates="roles", lazy=False
        )

    the_models.add(Role)

    # # HISTORY =================================================================
    class StageHistory(AJCModel):
        """Records the history of a subject's progression through stages."""

        __tablename__ = "ajc_stage_histories"

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
        role_id: orm.Mapped[id] = orm.mapped_column(
            sa.ForeignKey("ajc_roles.id"), nullable=False
        )
        role: orm.Mapped[Role] = orm.relationship(back_populates="stages")

        subject_id: orm.Mapped[int] = orm.mapped_column(
            sa.ForeignKey("ajc_subjects.id"), nullable=False
        )
        subject: orm.Mapped[SubjectModel] = orm.relationship(
            back_populates="stages", lazy=False
        )

        @property
        def expired(self):
            return bool(
                self.timeout
                and self.enter_dt
                and self.expire_dt
                and _utcnow() >= self.expire_dt
            )

    the_models.add(StageHistory)

    return the_models
