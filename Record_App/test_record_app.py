import unittest
from database import RecordDatabase, add_starter_data


class TestRecordApp(unittest.TestCase):
    def test(self):
        url = RecordDatabase.construct_in_memory_url()
        database = RecordDatabase(url)
        session = database.create_session()
        add_starter_data(session)

        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
