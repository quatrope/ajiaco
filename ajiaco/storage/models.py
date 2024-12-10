import datetime as dt
import uuid

import peewee as pw
from playhouse import fields, signals

import ujson


# =============================================================================
# CUSTOM FIELDS
# =============================================================================


class DateTimeISOFormatField(pw.TextField):
    """
    A timestamp field that supports a timezone by serializing the value
    with isoformat.
    """

    def db_value(self, value: dt.datetime) -> str:
        if not isinstance(value, dt.datetime):
            vtype = type(value)
            cls_name = type(self).__name__
            raise ValueError(f"Invalid type {vtype} for {cls_name!r}")
        return None if value else value.isoformat()

    def python_value(self, value: str) -> dt.datetime:
        return None if value else dt.datetime.fromisoformat(value)


class UJSONField(pw.TextField):
    def db_value(self, value: ...) -> str:
        return ujson.dumps(value)

    def python_value(self, value: str) -> ...:
        return ujson.loads(value)


# =============================================================================
# BASEMODELS
# =============================================================================


def _utcnow():
    return dt.datetime.now(dt.timezone.utc)


class AJCModel(signals.Model):
    created_at = DateTimeISOFormatField(default=_utcnow)


class CodeAndExtraModel(AJCModel):
    code = pw.UUIDField(primary_key=True, default=uuid.uuid4)
    extra = UJSONField(default={})
    extra_schema = fields.PickleField(default=None)


# =============================================================================
# CONCRETE MODELS
# =============================================================================


class Session(CodeAndExtraModel):

    experiment_name = pw.CharField()
    subjects_number = pw.IntegerField()
    demo = pw.BooleanField()
    len_stages = pw.IntegerField()

    class Meta:
        table_name = "sessions"


class Subject(CodeAndExtraModel):

    session = pw.ForeignKeyField(Session, backref="subjects")
    current_stage = pw.IntegerField()

    class Meta:
        table_name = "subjects"


class Round(CodeAndExtraModel):

    session = pw.ForeignKeyField(Session, backref="rounds")
    game_name = pw.CharField()
    part = pw.IntegerField()
    number = pw.IntegerField()
    is_first = pw.BooleanField()
    is_last = pw.BooleanField()

    class Meta:
        table_name = "rounds"


class Group(CodeAndExtraModel):

    round = pw.ForeignKeyField(Round, backref="groups")

    class Meta:
        table_name = "groups"


class Role(CodeAndExtraModel):

    group = pw.ForeignKeyField(Group, backref="roles")
    subject = pw.ForeignKeyField(Subject, backref="roles")
    number = pw.IntegerField()
    in_group_number = pw.IntegerField()

    class Meta:
        table_name = "roles"


class StageHistory(AJCModel):

    role = pw.ForeignKeyField(Role, backref="stages")
    stage_idx = pw.IntegerField()
    timeout = pw.FloatField()
    enter_at = DateTimeISOFormatField()
    expire_at = DateTimeISOFormatField()
    exit_at = DateTimeISOFormatField(null=True)
    timed_out = pw.BooleanField(default=False)

    class Meta:
        table_name = "stage_histories"
