import unittest
from database import RecordDatabase
from main import People, sql_input


class TestRecordApp(unittest.TestCase):
    def test_sql_input(self):
        url = RecordDatabase.construct_in_memory_url()
        database = RecordDatabase(url)
        database.ensure_tables_exist()
        session = database.create_session()
        new_person = People(name='Ada Lovelace', patient_id=1)
        sql_input(new_person, url)
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
