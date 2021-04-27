import unittest
from datetime import datetime

from database import RecordDatabase
from main import People, sql_input, update_person_commit


class TestRecordApp(unittest.TestCase):
    def test_pull_from_table(self):
        url = RecordDatabase.construct_in_memory_url()
        database = RecordDatabase(url)
        database.ensure_tables_exist()
        session = database.create_session()
        new_person = People(name='Ada Lovelace', patient_id=1)
        session.add(new_person)
        new_person_from_sql = session.query(People).filter(People.name == 'Ada Lovelace').one()
        self.assertEqual(new_person.name, new_person_from_sql.name)

    def test_sql_input(self):
        url = RecordDatabase.construct_in_memory_url()
        database = RecordDatabase(url)
        database.ensure_tables_exist()
        session = database.create_session()
        new_person = People(name='Ada Lovelace', patient_id=1)
        sql_input(new_person, session)
        new_person_from_sql = session.query(People).filter(People.name == 'Ada Lovelace').one()
        self.assertEqual(new_person.name, new_person_from_sql.name)

    def test_update_person(self):
        url = RecordDatabase.construct_in_memory_url()
        database = RecordDatabase(url)
        database.ensure_tables_exist()
        session = database.create_session()
        new_person = People(name='Ada Lovelace', patient_id=1, birthdate=datetime.now())
        session.add(new_person)
        name = 'Ada Love'
        birthdate_month = 1
        birthdate_day = 1
        birthdate_year = 2000
        birthdate = datetime(year=birthdate_year, month=birthdate_month, day=birthdate_day)
        updated_person = session.query(People).filter(People.patient_id == new_person.patient_id).one()
        update_person_commit(birthdate, name, updated_person, session)
        new_person_from_sql = session.query(People).filter(People.patient_id == 1).one()
        self.assertEqual(updated_person.name, new_person_from_sql.name)


if __name__ == '__main__':
    unittest.main()
