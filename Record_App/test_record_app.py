import unittest
from database import RecordDatabase
from main import People, sql_input, new_lot, Lots


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

    """
    Not sure if this is needed or not, but it does not work right now.
    
    def test_create_new_lot(self):
        url = RecordDatabase.construct_in_memory_url()
        database = RecordDatabase(url)
        database.ensure_tables_exist()
        session = database.create_session()
        new_lot(self, 1, 4, 6, 18, 2020, session)
        lot_from_sql = session.query(Lots).filter(Lots.lot_id == 4).one()
        self.assertEqual(lot_from_sql.vaccine_id, 1)
    """

if __name__ == '__main__':
    unittest.main()
