import datetime as dt
import inspect
import uuid

import peewee as pw
from playhouse import fields, signals

import ujson


# =============================================================================
# CUSTOM FIELDS
# =============================================================================


class DateTimeISOFormatField(pw.TextField):
    """A timestamp field that supports timezone by serializing with isoformat.

    This field extends TextField to store datetime values in ISO format string,
    preserving timezone information.

    Parameters
    ----------
    value : datetime.datetime, optional
        The datetime value to be stored

    Returns
    -------
    str
        ISO formatted string representation of the datetime

    Raises
    ------
    ValueError
        If the input value is not a datetime object
    """

    def db_value(self, value: dt.datetime) -> str:
        """Convert datetime object to ISO format string for database storage.

        Parameters
        ----------
        value : datetime.datetime
            The datetime value to convert

        Returns
        -------
        str
            ISO formatted string or None if value is None

        Raises
        ------
        ValueError
            If value is not a datetime object
        """
        if not isinstance(value, dt.datetime):
            vtype = type(value)
            cls_name = type(self).__name__
            raise ValueError(f"Invalid type {vtype} for {cls_name!r}")
        return None if value else value.isoformat()

    def python_value(self, value: str) -> dt.datetime:
        """Convert stored ISO format string back to datetime object.

        Parameters
        ----------
        value : str
            The ISO formatted datetime string

        Returns
        -------
        datetime.datetime
            The parsed datetime object or None if value is None
        """
        return None if value else dt.datetime.fromisoformat(value)


class UJSONField(pw.TextField):
    """Custom field for storing JSON data using ujson serialization.

    Extends TextField to provide JSON serialization/deserialization using ujson.
    """

    def db_value(self, value: ...) -> str:
        """Serialize value to JSON string.

        Parameters
        ----------
        value : Any
            The value to serialize

        Returns
        -------
        str
            JSON string representation
        """
        return ujson.dumps(value)

    def python_value(self, value: str) -> ...:
        """Deserialize JSON string to Python object.

        Parameters
        ----------
        value : str
            JSON string to deserialize

        Returns
        -------
        Any
            Deserialized Python object
        """
        return ujson.loads(value)


# =============================================================================
# BASEMODELS
# =============================================================================


def _utcnow():
    """Get current UTC datetime.

    Returns
    -------
    datetime.datetime
        Current UTC datetime with timezone information
    """
    return dt.datetime.now(dt.timezone.utc)


class AJCModel(signals.Model):
    """Base model class with creation timestamp.

    Attributes
    ----------
    created_at : DateTimeISOFormatField
        Timestamp when the record was created, defaults to current UTC time
    """

    created_at = DateTimeISOFormatField(default=_utcnow)


class CodeAndExtraModel(AJCModel):
    """Base model with UUID primary key and extra JSON data.

    Attributes
    ----------
    code : UUIDField
        Primary key UUID for the record
    extra : UJSONField
        Additional JSON data stored for the record
    extra_schema : PickleField
        Schema definition for the extra field
    """

    code = pw.UUIDField(primary_key=True, default=uuid.uuid4)
    extra = UJSONField(default={})
    extra_schema = fields.PickleField(default=None)


# =============================================================================
# MODELS CREATION
# =============================================================================

_SIGNALS = {
    "pre_save": signals.pre_save,
    "post_save": signals.post_save,
    "pre_delete": signals.pre_delete,
    "post_delete": signals.post_delete,
    "pre_init": signals.pre_init,
}


def _connect_signals(the_models):
    for Model in the_models:
        for signal_name, signal in _SIGNALS.items():
            handler = getattr(Model, signal_name, None)
            if handler and inspect.ismethod(handler):
                signal.connect(handler, sender=Model)


def _concrete_models(the_database):

    # here we store all the models for an easy return
    the_models = set()

    # SESSION =================================================================
    class Session(CodeAndExtraModel):
        """Represents an experimental session.

        Attributes
        ----------
        experiment_name : CharField
            Name of the experiment
        subjects_number : IntegerField
            Number of subjects in the session
        demo : BooleanField
            Whether this is a demo session
        len_stages : IntegerField
            Number of stages in the session
        """

        experiment_name = pw.CharField()
        subjects_number = pw.IntegerField()
        demo = pw.BooleanField()
        len_stages = pw.IntegerField()

        class Meta:
            database = the_database
            table_name = "sessions"

    the_models.add(Session)

    # SUBJECT =================================================================
    class Subject(CodeAndExtraModel):
        """Represents a subject participating in a session.

        Attributes
        ----------
        session : ForeignKeyField
            Reference to the session this subject belongs to
        current_stage : IntegerField
            Current stage number for this subject
        """

        session = pw.ForeignKeyField(Session, backref="subjects")
        current_stage = pw.IntegerField()

        class Meta:
            database = the_database
            table_name = "subjects"

    the_models.add(Subject)

    # ROUND ===================================================================
    class Round(CodeAndExtraModel):
        """Represents a round within a session.

        Attributes
        ----------
        session : ForeignKeyField
            Reference to the parent session
        game_name : CharField
            Name of the game being played
        part : IntegerField
            Part number within the session
        number : IntegerField
            Round number
        is_first : BooleanField
            Whether this is the first round
        is_last : BooleanField
            Whether this is the last round
        """

        session = pw.ForeignKeyField(Session, backref="rounds")
        game_name = pw.CharField()
        part = pw.IntegerField()
        number = pw.IntegerField()
        is_first = pw.BooleanField()
        is_last = pw.BooleanField()

        class Meta:
            database = the_database
            table_name = "rounds"

    the_models.add(Round)

    # GROUP ===================================================================
    class Group(CodeAndExtraModel):
        """Represents a group of subjects within a round.

        Attributes
        ----------
        round : ForeignKeyField
            Reference to the round this group belongs to
        """

        round = pw.ForeignKeyField(Round, backref="groups")

        class Meta:
            database = the_database
            table_name = "groups"

    the_models.add(Group)

    # ROLE ====================================================================
    class Role(CodeAndExtraModel):
        """Represents a subject's role within a group.

        Attributes
        ----------
        group : ForeignKeyField
            Reference to the group this role belongs to
        subject : ForeignKeyField
            Reference to the subject assigned this role
        number : IntegerField
            Role number
        in_group_number : IntegerField
            Number identifying this role within the group
        """

        group = pw.ForeignKeyField(Group, backref="roles")
        subject = pw.ForeignKeyField(Subject, backref="roles")
        number = pw.IntegerField()
        in_group_number = pw.IntegerField()

        class Meta:
            database = the_database
            table_name = "roles"

    the_models.add(Role)

    # HISTORY =================================================================
    class StageHistory(AJCModel):
        """Records the history of a subject's progression through stages.

        Attributes
        ----------
        role : ForeignKeyField
            Reference to the role this history belongs to
        stage_idx : IntegerField
            Index of the stage
        timeout : FloatField
            Timeout duration for the stage
        enter_at : DateTimeISOFormatField
            When the subject entered this stage
        expire_at : DateTimeISOFormatField
            When the stage will expire
        exit_at : DateTimeISOFormatField
            When the subject exited this stage (null if not yet exited)
        timed_out : BooleanField
            Whether the stage timed out
        """

        role = pw.ForeignKeyField(Role, backref="stages")
        stage_idx = pw.IntegerField()
        timeout = pw.FloatField()
        enter_at = DateTimeISOFormatField()
        expire_at = DateTimeISOFormatField()
        exit_at = DateTimeISOFormatField(null=True)
        timed_out = pw.BooleanField(default=False)

        class Meta:
            database = the_database
            table_name = "stage_histories"

    the_models.add(StageHistory)

    # RETURN ==================================================================

    return the_models


def create_models(database):
    the_models = _concrete_models(the_database=database)
    _connect_signals(the_models)
    return the_models
