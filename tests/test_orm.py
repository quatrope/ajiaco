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

"""Test cases for ajiaco.orm module"""


# =============================================================================
# IMPORTS
# =============================================================================

import os
from inspect import isclass

import sqlalchemy as sa
from sqlalchemy.ext import declarative

import sqlalchemy_utils as sau

import pytest

from ajiaco import orm


# =============================================================================
# CONSTANTS
# =============================================================================

TEST_DB_URL = os.getenv("AJIACO_TEST_DATABASE", "sqlite:///")


# =============================================================================
# TESTCASES
# =============================================================================

class _TestCustomTypes:
    """Related to test every custom type created in ajiaco ORM"""

    def setup_method(self, method):
        self.engine = sa.create_engine("sqlite:///")
        self.Base = declarative.declarative_base(name="Base", bind=self.engine)
        self.session_factory = sa.orm.sessionmaker(bind=self.engine)

        sau.functions.create_database(self.engine.url)

    def create_model_class(self, custom_type):
        class Model(self.Base):
            __tablename__ = "my_model"
            id = sa.Column(
                sa.Integer, sa.Sequence('my_model_id_seq'),
                primary_key=True, autoincrement=True)
            test_field = sa.Column(custom_type())

        self.Base.metadata.create_all()

        return Model

    def check_type(self, custom_type, good, bad):
        Model = self.create_model_class(custom_type)

        # this must work
        model = Model(test_field=good)
        try:
            session = self.session_factory()
            session.add(model)
            session.commit()
        finally:
            session.close()

        # this must fail
        with pytest.raises(sa.exc.StatementError):
            model = Model(test_field=bad)
            try:
                session = self.session_factory()
                session.add(model)
                session.commit()
            finally:
                session.close()


class TestListType(_TestCustomTypes):

    def test_ListType(self):
        custom_type, good, bad = orm.ListType, [], None
        self.check_type(custom_type, good, bad)

    def test_ListType_mutability(self):
        Model = self.create_model_class(orm.ListType.as_mutable)
        model = Model(test_field=[1])

        # store the original
        session = self.session_factory()
        session.add(model)
        session.commit()
        model_id = model.id
        session.close()

        # change the original
        session = self.session_factory()
        model = session.query(Model).filter_by(id=model_id).one()
        model.test_field.append(2)
        model.test_field.extend([3, 4, 5])
        model.test_field.pop()
        session.commit()
        session.close()

        # checks
        session = self.session_factory()
        model = session.query(Model).filter_by(id=model_id).one()
        assert model.test_field == [1, 2, 3, 4]
        assert isinstance(model.test_field, orm.MutableList)
        session.close()


class TestDictType(_TestCustomTypes):

    def test_DictType(self):
        custom_type, good, bad = orm.DictType, {}, None
        self.check_type(custom_type, good, bad)

    def test_DictType_mutability(self):
        Model = self.create_model_class(orm.DictType.as_mutable)
        model = Model(test_field={"a": 1, "b": [1, 2, 3]})

        # store the original
        session = self.session_factory()
        session.add(model)
        session.commit()
        model_id = model.id
        session.close()

        # change the original
        session = self.session_factory()
        model = session.query(Model).filter_by(id=model_id).one()
        model.test_field["c"] = 3.4
        model.test_field.update(d={})
        del model.test_field["a"]
        session.commit()
        session.close()

        # checks
        session = self.session_factory()
        model = session.query(Model).filter_by(id=model_id).one()
        assert model.test_field == {"b": [1, 2, 3], "c": 3.4, "d": {}}
        assert isinstance(model.test_field, orm.MutableDict)
        session.close()


class TestTuplesType(_TestCustomTypes):

    def test_TupleType(self):
        custom_type, good, bad = orm.TupleType, (), None
        self.check_type(custom_type, good, bad)


class TestSetType(_TestCustomTypes):

    def test_SetType(self):
        custom_type, good, bad = orm.SetType, set([]), None
        self.check_type(custom_type, good, bad)

    def test_SetType_mutability(self):
        Model = self.create_model_class(orm.SetType.as_mutable)
        model = Model(test_field={"a", 1, 3, None})

        # store the original
        session = self.session_factory()
        session.add(model)
        session.commit()
        model_id = model.id
        session.close()

        # change the original
        session = self.session_factory()
        model = session.query(Model).filter_by(id=model_id).one()
        model.test_field.add(1)
        model.test_field.update([4, 5])
        session.commit()
        session.close()

        # checks
        session = self.session_factory()
        model = session.query(Model).filter_by(id=model_id).one()
        assert model.test_field == {"a", 1, 3, None, 4, 5}
        assert isinstance(model.test_field, orm.MutableSet)
        session.close()


class TestFrozenSetType(_TestCustomTypes):

    def test_FrozenSetType(self):
        custom_type, good, bad = orm.FrozenSetType, frozenset([]), None
        self.check_type(custom_type, good, bad)


# =============================================================================
# TESTS DATABASES
# =============================================================================

class TestDatabase:
    """Tests related to the creation, and destruction of the database and
    the subjacent tables (without transactions)

    """
    def setup_method(self, method):
        self.db = orm.Database.from_url(dburl=TEST_DB_URL)
        self.memsdb = [
            orm.Database.from_url(dburl=memurl)
            for memurl in orm.IN_MEMORY_URLS]

    def teardown_method(self, method):
        if self.db.exists():
            self.db.drop_database()

    def test_in_memory_database(self):
        for db in self.memsdb:
            assert db.is_memory_database()
        assert not self.db.is_memory_database()

    def test_exists_and_create(self):
        for db in self.memsdb:
            assert db.exists()  # mem database always return True
            db.create_database()
            assert db.exists()

        assert not self.db.exists()
        self.db.create_database()
        assert self.db.exists()

    def tests_exists_and_drop(self):
        for db in self.memsdb:
            db.create_database()
            assert db.exists()
            db.drop_database()
            assert db.exists()  # mem database always return True

        self.db.create_database()
        assert self.db.exists()
        self.db.drop_database()
        assert not self.db.exists()

    def test_create_tables(self):
        self.db.create_database()

        class SomeModel(self.db.models.Base):
            __tablename__ = "some_table"
            id = sa.Column(
                sa.Integer, sa.Sequence(f'some_table_id_seq'),
                primary_key=True, autoincrement=True)

        assert not SomeModel.__table__.exists()
        self.db.create_tables()
        assert SomeModel.__table__.exists()

    def test_drop_tables(self):
        self.db.create_database()

        class SomeModel(self.db.models.Base):
            __tablename__ = "some_table"
            id = sa.Column(
                sa.Integer, sa.Sequence(f'some_table_id_seq'),
                primary_key=True, autoincrement=True)

        self.db.create_tables()
        assert SomeModel.__table__.exists()
        self.db.drop_tables()
        assert not SomeModel.__table__.exists()


# =============================================================================
# MODEL CREATION CASES
# =============================================================================

class _TestModelsCreation:
    """Base class to extend all the test related to create the model classes"""

    def setup_method(self, method):
        self.db = orm.Database.from_url(dburl="sqlite:///")
        self.db.create_database()

    def teardown_method(self, method):
        if self.db.exists():
            self.db.drop_database()

    def assert_fields_created(self, model, extra_fields, base_class):

        # first create our two dicts to compare
        fields = dict(base_class.__ajc_model_conf__.fields)
        fields.update(extra_fields)

        columns = {c.name: type(c.type) for c in model.__table__.c}

        # check if all fields has a column
        diff = set(fields).difference(columns)
        assert not diff, f"Fields {', '.join(diff)} not created"

        # check all the fields in the model
        for f_name, f_type in fields.items():
            if isclass(f_type) and issubclass(f_type, orm.Model):
                expected_type = sa.Integer
            elif isinstance(f_type, sa.Column):
                expected_type = type(f_type.type)
            elif f_type == orm.PRIMARY_KEY:
                expected_type = sa.Integer
            else:
                expected_type = orm.PY_TO_SA[f_type]

            c_type = columns[f_name]
            if getattr(c_type, "mutability_manager", None):
                c_type = c_type.as_mutable

            assert c_type == expected_type


class TestDatabaseFieldCreation(_TestModelsCreation):
    """This testcase ensure the funcionalities of the field creation"""

    def test_all_types(self):
        fields = {
            f"attr_{ftype.__name__}": ftype for ftype in orm.PY_TO_SA}
        model = self.db.create_model(
            "MyModel", orm.Model, fields,
            table_name="MyModel", related_name="my_models")
        self.assert_fields_created(model, fields, orm.Model)

    def test_forbiden_duplicated_field(self):
        with pytest.raises(orm.FieldError):

            class MyModel(orm.Model):
                table_name = "my_models"
                related_name = "my_models"
                fields = {"id": int}

        with pytest.raises(orm.FieldError):
            self.db.create_model(
                "MyModel", orm.Model, {"id": int},
                table_name="my_models", related_name="my_models")

    def test_forbiden_suffix_unders_start(self):
        with pytest.raises(orm.FieldError):

            class MyModel(orm.Model):
                table_name = "my_models"
                related_name = "my_models"
                fields = {"_foo": int}

        with pytest.raises(orm.FieldError):
            self.db.create_model(
                "MyModel", orm.Model, {"_foo": int},
                table_name="my_models", related_name="my_models")

    def test_invalid_type(self):
        with pytest.raises(orm.FieldError):

            class MyModel(orm.Model):
                table_name = "my_models"
                related_name = "my_models"
                fields = {"foo": type}

        with pytest.raises(orm.FieldError):
            self.db.create_model(
                "MyModel", orm.Model, {"foo": type},
                table_name="my_models", related_name="my_models")

    def test_undefined_field(self):
        with pytest.raises(orm.FieldError):

            class MyModel(orm.Model):
                table_name = "my_models"
                related_name = "my_models"
                fields = {"foo": None}

        with pytest.raises(orm.FieldError):
            self.db.create_model(
                "MyModel", orm.Model, {"foo": None},
                table_name="my_models", related_name="my_models")

    def test_undefined_table_name(self):
        with pytest.raises(AttributeError):

            class MyModel(orm.Model):
                related_name = "my_models"
                fields = {"foo": type}

    def test_undefined_related_name(self):
        with pytest.raises(AttributeError):

            class MyModel(orm.Model):
                table_name = "my_models"
                fields = {"foo": type}

    def test_get_model_fields(self):

        class MyModel(orm.Model):
            table_name = "my_models"
            related_name = "my_models"
            fields = {"foo": int}

        extracted_fields = dict(MyModel.__ajc_model_conf__.fields)
        assert set(extracted_fields.keys()) == {"id", "data", "foo"}

        assert extracted_fields["id"] == orm.PRIMARY_KEY
        assert extracted_fields["data"] == dict
        assert extracted_fields["foo"] == int

    def test_register_model(self):

        class MyModel(orm.Model):
            table_name = "my_models"
            related_name = "my_models"
            fields = {"foo": int}

        reg_model = self.db.register_model(MyModel)

        with pytest.raises(TypeError):
            self.db.register_model(int)

        with pytest.raises(TypeError):

            class AModel(orm.Model):
                table_name = "my_models"
                related_name = "my_models"
                fields = {"foo": int}
                abstract = True

            self.db.register_model(AModel)

        with pytest.raises(TypeError):
            self.db.register_model(reg_model)

        with pytest.raises(ValueError):
            self.db.register_model(MyModel)

    def test_related_name_foreign_key(self):

        @self.db.register_model
        class Link(orm.Model):
            table_name = "links"
            related_name = "links"
            fields = {}

        self.db.create_model(
            name="MyModel",
            base_model=orm.Model,
            fields={"link": Link},
            table_name="my_models",
            related_name="my_models")

        link = Link()
        assert hasattr(link, "my_models")

    def test_two_types_foreing_key(self):

        class Link(orm.Model):
            table_name = "links"
            related_name = "links"
            fields = {}

        RegLink = self.db.register_model(Link)

        Model1 = self.db.create_model(
            "Model1", orm.Model, {"link": Link},
            table_name="my_models1", related_name="my_models1")

        Model2 = self.db.create_model(
            "Model2", orm.Model, {"link": RegLink},
            table_name="my_models2", related_name="my_models2")

        link1 = [
            l.target_fullname
            for l in Model1.__table__.c["link"].foreign_keys]
        link2 = [
            l.target_fullname
            for l in Model2.__table__.c["link"].foreign_keys]

        assert link1 == link2


# =============================================================================
# BASE MODEL CLASSES TESTS
# =============================================================================

class TestBaseSession(_TestModelsCreation):

    def test_extend_BaseSession(self):
        Session = self.db.create_model(
            name="Session", base_model=orm.BaseSession,
            fields={}, table_name="sessions", related_name="sessions")
        self.assert_fields_created(Session, {}, orm.BaseSession)

    def test_Session_instantiation(self):

        Session = self.db.create_model(
            name="Session", base_model=orm.BaseSession,
            fields={}, table_name="sessions", related_name="sessions")

        self.db.create_tables()

        transaction = self.db.tfactory()
        try:
            session = Session(
                experiment_name="foo", subjects_number=42,
                demo=True, len_stages=716, data={"foo": (1, 2, 3)})
            transaction.add(session)
            transaction.commit()
            session_id = session.id
            session_code = session.code
        finally:
            transaction.close()

        transaction = self.db.tfactory()
        try:
            session = transaction.query(Session).filter_by(id=session_id).one()
            assert session.code == session_code
            assert session.experiment_name == "foo"
            assert session.subjects_number == 42
            assert session.demo is True
            assert session.len_stages == 716
            assert session.data == {"foo": (1, 2, 3)}
        finally:
            transaction.close()


class TestBaseSubject(_TestModelsCreation):

    def test_extend_BaseSubject(self):
        Session = self.db.create_model(
            name="Session", base_model=orm.BaseSession, fields={},
            table_name="sessions", related_name="sessions")

        fields = {"session": Session}

        Subject = self.db.create_model(
            name="Subject", base_model=orm.BaseSubject, fields=fields,
            table_name="subjects", related_name="subjects")

        self.assert_fields_created(Subject, fields, orm.BaseSubject)

    def test_not_redefine_BaseSubject_session(self):
        with pytest.raises(orm.FieldError):
            self.db.create_model(
                name="Subject", base_model=orm.BaseSubject, fields={},
                table_name="subjects", related_name="subjects")

    def test_Subject_instantiation(self):
        Session = self.db.create_model(
            name="Session", base_model=orm.BaseSession, fields={},
            table_name="sessions", related_name="sessions")

        Subject = self.db.create_model(
            name="Subject",
            base_model=orm.BaseSubject,
            fields={"session": Session},
            table_name="subjects",
            related_name="subjects")

        self.db.create_tables()

        transaction = self.db.tfactory()
        try:
            session = Session(
                experiment_name="foo", subjects_number=42,
                demo=True, len_stages=716, data={})
            transaction.add(session)

            subject = Subject(session=session, data={"foo": 716},)
            transaction.add(subject)

            transaction.commit()
            session_id = session.id
            subject_id = subject.id
            subject_code = subject.code
        finally:
            transaction.close()

        transaction = self.db.tfactory()
        try:
            session = transaction.query(Session).filter_by(id=session_id).one()
            subject = session.subjects[0]

            assert subject.id == subject_id
            assert subject.code == subject_code
            assert subject.current_stage == 0
            assert subject.session.id == session_id
            assert subject.data == {"foo": 716}

        finally:
            transaction.close()


class TestBaseRound(_TestModelsCreation):

    def test_extend_BaseRound(self):

        Session = self.db.create_model(
            name="Session", base_model=orm.BaseSession, fields={},
            table_name="sessions", related_name="sessions")

        fields = {"session": Session}

        Round = self.db.create_model(
            name="Round", base_model=orm.BaseRound, fields=fields,
            table_name="rounds", related_name="rounds")

        self.assert_fields_created(Round, fields, orm.BaseRound)

    def test_not_redefine_BaseRound_session(self):
        with pytest.raises(orm.FieldError):
            self.db.create_model(
                name="Round", base_model=orm.BaseRound, fields={},
                table_name="rounds", related_name="rounds")

    def test_Round_instantiation(self):
        Session = self.db.create_model(
            name="Session", base_model=orm.BaseSession, fields={},
            table_name="sessions", related_name="sessions")

        Round = self.db.create_model(
            name="Round", base_model=orm.BaseRound,
            fields={"session": Session}, table_name="rounds",
            related_name="rounds")

        self.db.create_tables()

        transaction = self.db.tfactory()
        try:
            session = Session(
                experiment_name="foo", subjects_number=42,
                demo=True, len_stages=716, data={})
            transaction.add(session)

            round = Round(
                game_name="foo", part=1, number=3,
                is_first=False, is_last=False,
                session=session, data={"foo": 716},)
            transaction.add(round)

            transaction.commit()
            session_id = session.id
            round_id = round.id
        finally:
            transaction.close()

        transaction = self.db.tfactory()
        try:
            session = transaction.query(Session).filter_by(id=session_id).one()
            round = session.rounds[0]

            assert round.id == round_id
            assert round.game_name == "foo"
            assert round.part == 1
            assert round.number == 3
            assert round.is_first is False
            assert round.is_last is False
            assert round.session.id == session_id
            assert round.data == {"foo": 716}

        finally:
            transaction.close()


class TestBaseGroup(_TestModelsCreation):

    def test_extend_BaseGroup(self):

        Session = self.db.create_model(
            name="Session", base_model=orm.BaseSession, fields={},
            table_name="sessions", related_name="sessions")

        Round = self.db.create_model(
            name="Round",
            base_model=orm.BaseRound,
            fields={"session": Session},
            table_name="rounds", related_name="rounds")

        fields = {"round": Round}

        Group = self.db.create_model(
            name="Group", base_model=orm.BaseGroup, fields=fields,
            table_name="groups", related_name="groups")

        self.assert_fields_created(Group, fields, orm.BaseGroup)

    def test_not_redefine_Baseround_session(self):
        with pytest.raises(orm.FieldError):
            self.db.create_model(
                name="Group", base_model=orm.BaseGroup, fields={},
                table_name="groups", related_name="groups")

    def test_Group_instantiation(self):
        Session = self.db.create_model(
            name="Session", base_model=orm.BaseSession, fields={},
            table_name="sessions", related_name="sessions")

        Round = self.db.create_model(
            name="Round",
            base_model=orm.BaseRound,
            fields={"session": Session},
            table_name="rounds", related_name="rounds")

        Group = self.db.create_model(
            name="Group", base_model=orm.BaseGroup, fields={"round": Round},
            table_name="groups", related_name="groups")

        self.db.create_tables()

        transaction = self.db.tfactory()
        try:
            session = Session(
                experiment_name="foo", subjects_number=42,
                demo=True, len_stages=716, data={})
            transaction.add(session)

            round = Round(
                game_name="foo", part=1, number=3,
                is_first=False, is_last=False,
                session=session, data={"foo": 716},)
            transaction.add(round)

            group = Group(round=round, data={"foo": 716})
            transaction.add(group)

            transaction.commit()
            session_id = session.id
            round_id = round.id
            group_id = group.id
        finally:
            transaction.close()

        transaction = self.db.tfactory()
        try:
            session = transaction.query(Session).filter_by(id=session_id).one()
            round = session.rounds[0]
            group = round.groups[0]

            assert group.id == group_id
            assert group.round.id == round_id
            assert group.round.session.id == session_id
            assert group.data == {"foo": 716}

        finally:
            transaction.close()


class TestBaseRole(_TestModelsCreation):

    def test_extend_BaseRole(self):

        Session = self.db.create_model(
            name="Session", base_model=orm.BaseSession, fields={},
            table_name="sessions", related_name="sessions")

        Subject = self.db.create_model(
            name="Subject",
            base_model=orm.BaseSubject,
            fields={"session": Session},
            table_name="subjects", related_name="subjects")

        Round = self.db.create_model(
            name="Round",
            base_model=orm.BaseRound,
            fields={"session": Session},
            table_name="rounds", related_name="rounds")

        Group = self.db.create_model(
            name="Group", base_model=orm.BaseGroup, fields={"round": Round},
            table_name="groups", related_name="groups")

        fields = {"group": Group, "round": Round, "subject": Subject}
        Role = self.db.create_model(
            name="Role", base_model=orm.BaseRole, fields=fields,
            table_name="roles", related_name="roles")

        self.assert_fields_created(Role, fields, orm.BaseRole)

    def test_not_redefine_Baseround_session_or_subject_or_role(self):
        Session = self.db.create_model(
            name="Session", base_model=orm.BaseSession, fields={},
            table_name="sessions", related_name="sessions")

        Subject = self.db.create_model(
            name="Subject",
            base_model=orm.BaseSubject,
            fields={"session": Session},
            table_name="subjects", related_name="subjects")

        Round = self.db.create_model(
            name="Round",
            base_model=orm.BaseRound,
            fields={"session": Session},
            table_name="rounds", related_name="rounds")

        Group = self.db.create_model(
            name="Group", base_model=orm.BaseGroup, fields={"round": Round},
            table_name="groups", related_name="groups")

        combs = []
        for group in (None, Group):
            for round in (None, Round):
                for subject in (None, Subject):
                    if group and round and subject:
                        continue
                    combs.append({
                        "group": group, "subject": subject, "round": round})

        for idx, bad_fields in enumerate(combs):
            with pytest.raises(orm.FieldError):
                self.db.create_model(
                    name=f"Group{idx}",
                    base_model=orm.BaseGroup,
                    fields=bad_fields,
                    table_name="roles", related_name="roles")

    def test_Role_instantiation(self):
        Session = self.db.create_model(
            name="Session", base_model=orm.BaseSession, fields={},
            table_name="sessions", related_name="sessions")

        Subject = self.db.create_model(
            name="Subject",
            base_model=orm.BaseSubject,
            fields={"session": Session},
            table_name="subjects", related_name="subjects")

        Round = self.db.create_model(
            name="Round",
            base_model=orm.BaseRound,
            fields={"session": Session},
            table_name="rounds", related_name="rounds")

        Group = self.db.create_model(
            name="Group", base_model=orm.BaseGroup, fields={"round": Round},
            table_name="groups", related_name="groups")

        Role = self.db.create_model(
            name="Role", base_model=orm.BaseRole,
            fields={"group": Group, "round": Round, "subject": Subject},
            table_name="roles", related_name="roles")

        self.db.create_tables()

        transaction = self.db.tfactory()
        try:
            session = Session(
                experiment_name="foo", subjects_number=42,
                demo=True, len_stages=716, data={})
            transaction.add(session)

            subject = Subject(session=session, data={"foo": 716},)
            transaction.add(subject)

            round = Round(
                game_name="foo", part=1, number=3,
                is_first=False, is_last=False,
                session=session, data={"foo": 716},)
            transaction.add(round)

            group = Group(round=round, data={"foo": 716})
            transaction.add(group)

            role = Role(
                number=42, in_group_number=11,
                group=group, round=round, subject=subject, data={"foo": 716})

            transaction.commit()
            session_id = session.id
            subject_id = subject.id
            round_id = round.id
            group_id = group.id
            role_id = role.id
        finally:
            transaction.close()

        return

        transaction = self.db.tfactory()
        try:
            session = transaction.query(Session).filter_by(id=session_id).one()
            subject = session.subjcts[0]
            round = session.rounds[0]
            group = round.groups[0]
            role = round.roles[0]

            assert role.id == role_id
            assert role.subject.id == subject_id
            assert role.round.id == round_id
            assert role.group.id == group_id
            assert role.group.round.id == round_id
            assert role.group.round.session.id == session_id
            assert role.data == {"foo": 716}

        finally:
            transaction.close()
