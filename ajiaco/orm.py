#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of the
#   Ajiaco Project (https://github.com/leliel12/ajiaco/).
# Copyright (c) 2018-2019, Juan B Cabral
# License: BSD-3-Clause
#   Full Text: https://github.com/leliel12/ajiaco/blob/master/LICENSE


# =============================================================================
# DOCS
# =============================================================================

"""This module provides an simple ORM based on
SQLAlchemy (https://www.sqlalchemy.org/)

This module provides the functionalities to define tables with using primitive
types of Python (``int``, ``float``, ``bool``, ``list``, ``dict``, etc.)
and optionally use the ``sqlalchemy.Column`` if is necessary more features.

Likewise these functionalities are accessible through simple function calls
or more flexible object oriented interface.

"""


# =============================================================================
# IMPORTS
# =============================================================================

import copy
import contextlib
import datetime as dt
import decimal as dec
from inspect import isclass

import shortuuid

import attr

import sqlalchemy as sa
from sqlalchemy.ext import declarative
from sqlalchemy.ext.mutable import MutableDict, MutableList, MutableSet

import sqlalchemy_utils as sau

from .utils import Bunch

# =============================================================================
# PYTHON CONF
# =============================================================================

__all__ = [
    "PRIMARY_KEY",
    "FieldError",
    "Model",
    "BaseSession",
    "BaseSubject",
    "BaseRound",
    "BaseRole",
    "Database",
    "Connection"]


# =============================================================================
# SOME CONSTANTS
# =============================================================================

# Internal constant for defining which are the urls that are used in sqlalchemy
# as in-memory databases.
IN_MEMORY_URLS = ("sqlite:///", "sqlite://")

# Constant for defining primary keys fields.
PRIMARY_KEY = "<PRIMARY_KEY>"


# =============================================================================
# AJIACO CUSTOM TYPES
# =============================================================================

class _PickleTypeValidator(sa.PickleType):
    """Check if the object you are trying o write is instance of the
    ``expected_type`` class attribute, also if the object define some
    ``mutability_manager`` the custom type is wrapped inside it with
    ``mutability_manager.as_mutable(custom_type_instance)``

    """
    expected_type = None
    mutability_manager = None

    def bind_processor(self, dialect):
        processor = super().bind_processor(dialect)
        expected_type = self.expected_type

        def check_type_processor(value):
            if not isinstance(value, expected_type):
                msg = f"Must be '{expected_type}' type. Found {type(value)}"
                raise TypeError(msg)
            return processor(value)

        return check_type_processor

    @classmethod
    def as_mutable(cls, *args, **kwargs):
        obj = cls(*args, **kwargs)
        return cls.mutability_manager.as_mutable(obj)


class ListType(_PickleTypeValidator):
    """Provide a way to store ``list`` instances as pickle"""
    expected_type = list
    mutability_manager = MutableList


class DictType(_PickleTypeValidator):
    """Provide a way to store ``dict`` instances as pickle"""
    expected_type = dict
    mutability_manager = MutableDict


class TupleType(_PickleTypeValidator):
    """Provide a way to store ``tuple`` instances as pickle"""
    expected_type = tuple


class SetType(_PickleTypeValidator):
    """Provide a way to store ``set`` instances as pickle"""
    expected_type = set
    mutability_manager = MutableSet


class FrozenSetType(_PickleTypeValidator):
    """Provide a way to store ``frozenset`` instances as pickle"""
    expected_type = frozenset


# =============================================================================
# MAP TYPES
# =============================================================================

# This dictionary i most for internal use, it defined how a Python built-ins
# Map to an equivalent SQLAlchemy Column-Type.
PY_TO_SA = {
    object: sa.PickleType,
    int: sa.BigInteger,
    float: sa.Float,
    bool: sa.Boolean,
    str: sa.Text,

    list: ListType.as_mutable,
    dict: DictType.as_mutable,
    tuple: TupleType,
    set: SetType.as_mutable,
    frozenset: FrozenSetType,

    dec.Decimal: sa.Numeric,

    dt.date: sa.Date,
    dt.datetime: sa.DateTime,
    dt.time: sa.Time}


# =============================================================================
# BASE MODEL AND EXCEPTION
# =============================================================================

class FieldError(AttributeError):
    """Represent any missconfiguration of a model field"""


class Model:
    """Base type of all models of this ORM.  This class automatically add an
    autoincremental integer as primary-key of all models called 'id', and
    an ``ajiaco.util.Bunch`` instance called 'data'.

    All subclasses must define a  classlevel attribute ``fields`` that must be
    a dictionary where the key are the name of the field, and the value is the
    type.

    The types can be:

    - A Python primitive (the allowed primitives are present in the
      ``db.PY_TO_SA`` dictionary).
    - A ``sqlalchemy.Column`` instance.
    - Another `db.Model` subclass (for relationships).
    - `None`. This is an "abstract" field and must be redefined if
      the class is concrete.

    Finally the rules for the names are:

    - Only 'abstract' fields can be redefined.
    - Then name can't starts with an underscore "_".

    Attributes
    ----------

    All the model configuration are copied to class level attributes to
    an internal dict-like object called ``__ajc_model_conf__``

    This attributes are:

    name : str
        The name of this model is directly copyes drom the ``__name__``
        attribute.
    copy_conf : bool (default: False)
        If it's True all but ``model_name`` configuration is coppied from
        the super class ``__ajc_model_conf__``.
    abstract : bool (default: False)
        If it True, ``table_name``and ``related_name`` definitions can be
        omited
    fields : dict
        A dictionary with the keys as the field name and the value as the field
        type.
    table_name : str
        The table name of this model.
    related_name : str
        Related name of the class to be used on the relations. When this class
        have a link to another model the backref is created with this name.

    """

    __ajc_model_conf__ = Bunch(
        bunch_name="Model.conf",
        abstract=True,
        copy_conf=False,
        name="Model",
        fields=(("id", PRIMARY_KEY), ("data", dict)),
        table_name="",
        related_name="")

    @classmethod
    def _ensure_attr(cls, name):
        try:
            return getattr(cls, name)
        except AttributeError:
            raise AttributeError(
                f"Model subclass '{cls}' "
                f"must define the attribute {name}")

    @classmethod
    def _check_type(cls, f_type):
        return (
            f_type is None or
            f_type == PRIMARY_KEY or
            f_type in PY_TO_SA or
            isinstance(f_type, sa.Column) or
            (isclass(f_type) and issubclass(f_type, Model)))

    @classmethod
    def _build_doc(cls, conf):
        base_doc = cls.__doc__ or f"Model {conf.name}"
        parameters = []
        for field_name, field_type in conf.fields:
            optional = False
            field_help = None
            if isinstance(field_type, sa.Column):
                optional = bool(field_type.default)
                field_help = field_type.doc or field_type.comment
                field_type = field_type.type.python_type.__name__

            if isclass(field_type):
                field_type = getattr(field_type, "__name__", field_type)

            if field_type is None:
                field_type = f"{field_type} (Abstract field)"

            line = f"{field_name} : {field_type}"
            if optional:
                line = f"{line} (optional)"
            if field_help:
                line = f"{line}\n    {field_help}"
            parameters.append(line)

        doc = "\n".join(
            [base_doc, "Parameters", "----------", ""] + parameters)

        return doc

    def __init_subclass__(cls, *args, **kwargs):
        model_name = cls.__name__

        copy_conf = bool(getattr(cls, "copy_conf", False))

        if copy_conf:
            conf = Bunch(
                bunch_name=f"{model_name}.__ajc_model_conf__",
                **cls.__ajc_model_conf__)
        else:
            abstract = bool(getattr(cls, "abstract", False))

            table_name = "" if abstract else cls._ensure_attr("table_name")
            related_name = "" if abstract else cls._ensure_attr("related_name")
            fields = dict(cls.__ajc_model_conf__.fields)

            cls_fields = getattr(cls, "fields", {})
            for field_name, field_type in cls_fields.items():

                if not cls._check_type(field_type):
                    qual_name = f"{model_name}.{field_name}"
                    raise FieldError(
                        f"Invalid type {field_type} of '{qual_name}'")

                elif field_name.startswith("_"):
                    qual_name = f"{model_name}.{field_name}"
                    raise FieldError(
                        f"Field can't start with an underscore: '{qual_name}'")

                elif field_name in fields and fields[field_name] is not None:
                    raise FieldError(
                        f"'{model_name}' cant't redefine field '{field_name}'")

                fields[field_name] = copy.deepcopy(field_type)

            # need a second iteration if we still have a abstract field
            # in a concrete class
            if abstract is False:
                for field_name, field_type in fields.items():
                    if field_type is None:
                        raise FieldError(
                            f"Field '{model_name}.{field_name}' must be "
                            "redefined if the model is concrete")

            conf = Bunch(
                bunch_name=f"{model_name}.__ajc_model_conf__",
                copy_conf=False,
                name=model_name,
                abstract=abstract,
                fields=tuple(fields.items()),
                table_name=table_name,
                related_name=related_name)

        cls.__doc__ = cls._build_doc(conf)
        cls.__ajc_model_conf__ = conf

        for k in conf:
            if hasattr(cls, k):
                delattr(cls, k)


# =============================================================================
# DOM STORAGES
# =============================================================================

class BaseSession(Model):
    """Base class to store en experiment session.

    A session is an execution of an experiment assigned to
    several subjects.

    """
    abstract = True
    fields = {
        "code": sa.Column(
            sa.String(30), unique=True, default=shortuuid.uuid, index=True),
        "experiment_name":
            sa.Column(sa.String(255), index=True, nullable=False),
        "subjects_number": sa.Column(sa.Integer, nullable=False),
        "demo": sa.Column(sa.Boolean, nullable=False),
        "len_stages": sa.Column(sa.Integer, nullable=False)}

    def __repr__(self):
        model_name = self.__ajc_model_conf__.name
        return f"{model_name}(id={self.id}, code='{self.code}')"


class BaseSubject(Model):
    """Base class to store subjects.

    The subject is a real person inside of a Session experiment.

    """
    abstract = True
    fields = {
        "code": sa.Column(
            sa.String(30), unique=True, default=shortuuid.uuid, index=True),
        "current_stage": sa.Column(sa.Integer, nullable=False, default=0),
        "session": None}

    def __repr__(self):
        model_name = self.__ajc_model_conf__.name
        return f"{model_name}(id={self.id}, code='{self.code}')"


class BaseRound(Model):
    """Base class to store rounds.

    A round is a game execution associated with some session

    """
    abstract = True
    fields = {
        "game_name": sa.Column(sa.String(255), nullable=False),
        "part": sa.Column(sa.Integer, nullable=False),
        "number": sa.Column(sa.Integer, nullable=False),
        "is_first": sa.Column(sa.Boolean, nullable=False),
        "is_last": sa.Column(sa.Boolean, nullable=False),
        "session": None}


class BaseGroup(Model):
    """Base class to store groups.

    A group is normally a group of subject in interaction on experiments, there
    are your companion or you adversaries.

    """
    abstract = True
    fields = {
        "round": None}


class BaseRole(Model):
    """Base class to store roles.

    A Role is a subject inside a group.

    """
    abstract = True
    fields = {
        "number": sa.Column(sa.Integer, nullable=False),
        "in_group_number": sa.Column(sa.Integer, nullable=False),
        "group": None, "round": None, "subject": None}


# =============================================================================
# DATABASE
# =============================================================================

@attr.s(frozen=True, cmp=False)
class Database:
    """High level interface of a Database. The only required parameter is
    the database SQLAlchemy engine (``engine``) or the url (``dburl``), if
    you want to use the ``Database.from_url`` class-method.

    This class can construct and store (in the ``models`` attribute)
    SQLAlchemy models based on `db.Model` subclasses or plain dictionaries
    definitions of fields.

    Finally the databases instances provides methods for: create and drop the
    tables; and create, delete and check the existence of the database
    itself.

    Attributes
    ----------

    engine: sa.engine.Engine
        The engine of the database
    models: Bunch
        Dict-like object containing all the registered models
    cfactory: sa.orm.session.sessionmaker
        The engine connection/session maker

    Examples
    --------

    This two initializations are equivalent

    .. code-block:: python

        import sqlalchemy as sa

        from ajiaco import orm

        db = orm.Database(engine=sa.create_engine("sqlite:///"))

        db = orm.Database.from_url("sqlite:///")

    And the models can be created as follows

    .. code-block:: python

        @db.register_model
        class Foo(Model):
            tablename = "foo"
            related_name = "foo"
            fields = {"a": int, "b": str}

    is equivalent to

    .. code-block:: python

        Foo = db.create_model(
            "Foo", Model, {"a": int, "b": str},
            tablename="foo", related_name="foo")

    or more loosesly equivalent:

    .. code-block:: python

        db = orm.Database.from_url("sqlite:///")

        class Foo(db.models.Base):
            __tablename__ = "foo"
            id = sa.Column(
                sa.Integer, sa.Sequence(f'{cls.table_name()}_id_seq'),
                primary_key=True, autoincrement=True)
            a = sa.Column(sa.Integer, nullable=True, default=None)
            b = sa.column(sa.Text, nullable=True, default=None)

        db.models["Foo"] = Foo

    """
    engine: sa.engine.Engine = attr.ib()
    models: Bunch = attr.ib(init=False, repr=False)
    cfactory: sa.orm.session.sessionmaker = attr.ib(init=False, repr=False)

    @models.default
    def _models_default(self):
        Base = declarative.declarative_base(name="Base", bind=self.engine)
        return Bunch(bunch_name="db.models", Base=Base)

    @cfactory.default
    def _connection_factory_default(self):
        return sa.orm.sessionmaker(
            bind=self.engine, class_=Connection, db=self)

    # PUBLIC API FROM HERE

    @classmethod
    def from_url(cls, dburl, **engine_params):
        """Create a new database based on url. Also support extra parameters
        for the engine creation.

        Examples
        --------

        This two codes are equivalent

        .. code-block:: python

            from ajiaco import orm
            db = orm.Database.from_url("sqlite:///")

        .. code-block:: python

            import sqlalchemy as sa
            from ajiaco import orm

            engine = sa.create_engine("sqlite:///")
            db = orm.Database(engine)

        """
        engine = sa.create_engine(dburl, **engine_params)
        return Database(engine=engine)

    def convert_to_column(self, model, f_name, f_type):
        """Convert a field description of the ORM to a SQLAlchemy columns"""

        if isinstance(f_type, sa.Column):
            return {f_name: f_type.copy()}

        if isclass(f_type) and issubclass(f_type, Model):
            fk_name = f_type.__ajc_model_conf__.name

            fk_model = self.models[fk_name]

            fk = f"{fk_model.__ajc_model_conf__.table_name}.id"
            sa_column = sa.Column(
                f_name, sa.Integer(), sa.ForeignKey(fk), nullable=False)

            related_name = model.__ajc_model_conf__.related_name
            relationship = sa.orm.relationship(
                fk_name, lazy='joined', backref=related_name)

            return {f"_{f_name}_id": sa_column, f_name: relationship}

        if f_type == PRIMARY_KEY:
            seq_name = f"{model.__ajc_model_conf__.table_name}_id_seq"
            sa_column = sa.Column(
                f_name, sa.Integer, sa.Sequence(seq_name),
                primary_key=True, autoincrement=True)
            return {f_name: sa_column}

        sa_type = PY_TO_SA[f_type]
        sa_column = sa.Column(
            f_name, sa_type(), nullable=True, default=None)
        return {f_name: sa_column}

    def register_model(self, model):
        """Creates and store new SQLAlchemy model using the declarative base
        ``Database.models.Base`` and the fields on the given model parameter.

        This method store the resulting SQLAlchemy model into
        ``Database.models`` return it.

        .. code-block:: python

            from ajiaco import orm

            db = Database("sqlite:///")

            @db.register_model
            class MyModel(orm.Model):
                fields = {"a": int, "b": str}

        """

        # validation
        if not (isclass(model) and issubclass(model, Model)):
            raise TypeError(f"'{model}' is not an Model subclass")
        elif model.__ajc_model_conf__.abstract:
            raise TypeError(f"'{model} is abstract")
        elif issubclass(model, self.models.Base):
            raise TypeError("'model' can't be a subclass Database.models.Base")

        model_name = model.__ajc_model_conf__.name
        if model_name in self.models:
            raise ValueError(f"Duplicated model '{model_name}'")

        # here we "compile" the fields to columns
        table_name = model.__ajc_model_conf__.table_name
        fields = model.__ajc_model_conf__.fields

        sa_model_attrs = {
            "__tablename__": table_name,
            "__ajc_fields__": fields,
            "__ajc_db__": self}

        for f_name, f_type in fields:
            columns = self.convert_to_column(model, f_name, f_type)
            sa_model_attrs.update(columns)

        sa_model_attrs["copy_conf"] = True
        real_model = type(
            model_name, (model, self.models.Base), sa_model_attrs)

        # store and return
        self.models[model_name] = real_model
        return real_model

    def create_model(self,
                     name, base_model,
                     fields, table_name,
                     related_name, **kwargs):
        """Create a model from a dictionary of fields and base model class.

        .. code-block:: python

            from ajiaco import orm
            db = Database("sqlite:///")

            MyModel = db.create_model(
                "MyModel", orm.Model,
                fields={"a": int, "b": str},
                table_name="table_my_model", related_name="my_models")

        All the extra arguments are added as class attributes to the model.

        """
        kwargs.update(
            fields=fields, table_name=table_name, related_name=related_name)
        model = type(name, (base_model,), kwargs)
        real_model = self.register_model(model)
        return real_model

    def is_memory_database(self):
        """Check if this database is a memory database"""
        return str(self.engine.url) in IN_MEMORY_URLS

    def exists(self):
        """Check if the database exists in the given ``dburl``"""
        exists = sau.functions.database_exists(self.engine.url)
        return exists

    def drop_database(self):
        """Destroy the database on the given ``dburl``"""
        return sau.functions.drop_database(self.engine.url)

    def create_database(self):
        """Create new database on the given ``dburl``"""
        return sau.functions.create_database(self.engine.url)

    def drop_tables(self, tables=None):
        """Detroy all the tables given on the ``tables`` parameter or all if
        ``None`` is given (defaul=``None``)

        """
        return self.models.Base.metadata.drop_all(tables=tables)

    def create_tables(self):
        """Creates all the tables related to this database"""
        return self.models.Base.metadata.create_all()

    def connection(self):
        """Create a connection scope for this database"""
        return _ConnectionScope(self.cfactory)


# =============================================================================
# CONNECTIONS
# =============================================================================

class _ConnectionScope(contextlib.AbstractContextManager):
    """Provide a transactional context-scope around a series of operations.

    """

    def __init__(self, maker):
        self._maker = maker

    def __enter__(self):
        self._session = self._maker()
        return self._session

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self._session.rollback()
        else:
            self._session.commit()
        self._session.close()


class Connection(sa.orm.Session):
    """Transactional session around an ``ajiaco.orm.Database``"""

    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._db = db

    def __repr__(self):
        """repr(X) <==> X.__repr__()"""
        return f"Connection('{hex(id(self))}')"

    @property
    def models(self):
        """Models container of the database"""
        return self._db.models

    def get_session(self, code_or_id):
        """Retrieve an existing session by code or by id. If the paramater
        ``code_or_id`` is an int instance the method asumes is the id,
        otherwise is the code.

        """
        Session = self.models.Session
        query = self.query(Session)
        if isinstance(code_or_id, int):
            query = query.filter(Session.id == code_or_id)
        else:
            query = query.filter(Session.code == code_or_id)
        return query.one()
