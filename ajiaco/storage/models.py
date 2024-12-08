from datetime import datetime
import uuid

import peewee as pw


class Session(pw.Model):
    code = pw.UUIDField(primary_key=True, default=uuid.uuid4)
    experiment_name = pw.CharField()
    subjects_number = pw.IntegerField()
    demo = pw.BooleanField()
    len_stages = pw.IntegerField()
    created_at = pw.DateTimeField(default=datetime.now)

    class Meta:
        table_name = "sessions"


class Subject(pw.Model):
    code = pw.UUIDField(primary_key=True, default=uuid.uuid4)
    session = pw.ForeignKeyField(Session, backref="subjects")
    current_stage = pw.IntegerField()
    created_at = pw.DateTimeField(default=datetime.now)

    class Meta:
        table_name = "subjects"


class Round(pw.Model):
    code = pw.UUIDField(primary_key=True, default=uuid.uuid4)
    session = pw.ForeignKeyField(Session, backref="rounds")
    game_name = pw.CharField()
    part = pw.IntegerField()
    number = pw.IntegerField()
    is_first = pw.BooleanField()
    is_last = pw.BooleanField()
    created_at = pw.DateTimeField(default=datetime.now)

    class Meta:
        table_name = "rounds"


class Group(pw.Model):
    code = pw.UUIDField(primary_key=True, default=uuid.uuid4)
    round = pw.ForeignKeyField(Round, backref="groups")
    created_at = pw.DateTimeField(default=datetime.now)

    class Meta:
        table_name = "groups"


class Role(pw.Model):
    code = pw.UUIDField(primary_key=True, default=uuid.uuid4)
    group = pw.ForeignKeyField(Group, backref="roles")
    subject = pw.ForeignKeyField(Subject, backref="roles")
    number = pw.IntegerField()
    in_group_number = pw.IntegerField()
    created_at = pw.DateTimeField(default=datetime.now)

    class Meta:
        table_name = "roles"


class StageHistory(pw.Model):
    code = pw.UUIDField(primary_key=True, default=uuid.uuid4)
    role = pw.ForeignKeyField(Role, backref="stages")
    stage_idx = pw.IntegerField()
    timeout = pw.FloatField()
    enter_at = pw.DateTimeField()
    expire_at = pw.DateTimeField()
    exit_at = pw.DateTimeField(null=True)
    timed_out = pw.BooleanField(default=False)
    created_at = pw.DateTimeField(default=datetime.now)

    class Meta:
        table_name = "stage_histories"
