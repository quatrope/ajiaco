from collections.abc import Mapping
import datetime as dt
import itertools as it
import uuid
from typing import Optional

import attrs

import sqlalchemy as sa
import sqlalchemy.orm as orm

from ..utils import sysinfo


# =============================================================================
# MODELS CONTAINER
# =============================================================================


@attrs.define(frozen=True, repr=False)
class AjcModelsContainer(Mapping):
    BaseModel: ...
    Stamp: ...
    models: frozenset

    def items(self):
        for model in it.chain([self.BaseModel, self.Stamp], self.models):
            name = model.__name__
            yield name, model

    def __dir__(self):
        return super().__dir__() + list(self)

    def __getitem__(self, k):
        for name, model in self.items():
            if k == name:
                return model
        raise KeyError(k)

    def __getattr__(self, a):
        try:
            return self[a]
        except KeyError:
            raise AttributeError(a)

    def __iter__(self):
        return (name for name, _ in self.items())

    def __len__(self):
        return len(self.models) + 2  # + BaseModel + StampModel

    def __repr__(self):
        models = set(self.keys())
        return f"<models {models!r}>"


# =============================================================================
# MODELS CREATION
# =============================================================================


def create_models(metadata: sa.MetaData):

    # First the Base Model ====================================================
    BaseModel = orm.declarative_base(name="BaseModel", metadata=metadata)

    # Second the abstracts ====================================================
    class IDAndCreatedAtModelABC(BaseModel):
        """Base model with id and creation timestamp."""

        __abstract__ = True

        id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
        created_at: orm.Mapped[dt.datetime] = orm.mapped_column(
            sa.DateTime(timezone=True),
            default=sysinfo.utcnow,
            nullable=False,
        )

    class CodeAndExtraModelABC(IDAndCreatedAtModelABC):
        """Abstract base model with UUID  and extra JSON data."""

        __abstract__ = True

        code: orm.Mapped[uuid.UUID] = orm.mapped_column(
            sa.String, unique=True, default=uuid.uuid4
        )
        extra: orm.Mapped[dict] = orm.mapped_column(sa.JSON, default=dict)
        extra_schema: orm.Mapped[Optional[bytes]] = orm.mapped_column(
            sa.String, nullable=True
        )

    # Third the stamp =========================================================

    class Stamp(IDAndCreatedAtModelABC):

        __tablename__ = "ajc_stamp"

        data: orm.Mapped[dict] = orm.mapped_column(sa.JSON)

    # Store all models for easy return ========================================
    the_models = set()

    # SESSION =================================================================
    class ExperimentSessionModel(CodeAndExtraModelABC):
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

    the_models.add(ExperimentSessionModel)

    # SUBJECT =================================================================
    class SubjectModel(CodeAndExtraModelABC):
        """Represents a subject participating in a session."""

        __tablename__ = "ajc_subjects"

        current_stage: orm.Mapped[int] = orm.mapped_column(
            sa.Integer, nullable=False
        )

        # Relationships
        session_id: orm.Mapped[int] = orm.mapped_column(
            sa.ForeignKey("ajc_sessions.id"), nullable=False
        )
        session: orm.Mapped[ExperimentSessionModel] = orm.relationship(
            backref="subjects", lazy=False
        )

    the_models.add(SubjectModel)

    # ROUND ===================================================================
    class RoundModel(CodeAndExtraModelABC):
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
        session: orm.Mapped[ExperimentSessionModel] = orm.relationship(
            backref="rounds", lazy=False
        )

    the_models.add(RoundModel)

    # GROUP ===================================================================
    class GroupModel(CodeAndExtraModelABC):
        """Represents a group of subjects within a round."""

        __tablename__ = "ajc_groups"

        # Relationships
        round_id: orm.Mapped[int] = orm.mapped_column(
            sa.ForeignKey("ajc_rounds.id"), nullable=False
        )
        round: orm.Mapped[RoundModel] = orm.relationship(
            backref="groups", lazy=False
        )

    the_models.add(GroupModel)

    # ROLE ====================================================================
    class Role(CodeAndExtraModelABC):
        """Represents a subject's role within a group."""

        __tablename__ = "ajc_roles"

        number: orm.Mapped[int] = orm.mapped_column(sa.Integer, nullable=False)
        in_group_number: orm.Mapped[int] = orm.mapped_column(
            sa.Integer, nullable=False
        )

        group_id: orm.Mapped[int] = orm.mapped_column(
            sa.ForeignKey("ajc_groups.id"), nullable=False
        )
        group: orm.Mapped[GroupModel] = orm.relationship(backref="roles")

        subject_id: orm.Mapped[int] = orm.mapped_column(
            sa.ForeignKey("ajc_subjects.id"), nullable=False
        )
        subject: orm.Mapped[SubjectModel] = orm.relationship(
            backref="roles", lazy=False
        )

    the_models.add(Role)

    # # HISTORY =================================================================
    class StageHistory(IDAndCreatedAtModelABC):
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
        role: orm.Mapped[Role] = orm.relationship(backref="stages")

        subject_id: orm.Mapped[int] = orm.mapped_column(
            sa.ForeignKey("ajc_subjects.id"), nullable=False
        )
        subject: orm.Mapped[SubjectModel] = orm.relationship(
            backref="stages", lazy=False
        )

        @property
        def expired(self):
            return bool(
                self.timeout
                and self.enter_dt
                and self.expire_dt
                and sysinfo.utcnow() >= self.expire_dt
            )

    the_models.add(StageHistory)

    models_container = AjcModelsContainer(
        BaseModel=BaseModel,
        Stamp=Stamp,
        models=frozenset(the_models),
    )

    return models_container
