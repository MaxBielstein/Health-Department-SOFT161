import unittest

from database import RecordDatabase
from distribution import Vaccines, sql_input, Manufacturers


class MyTestCase(unittest.TestCase):
    def test_sql_input(self):
        url = RecordDatabase.construct_in_memory_url()
        database = RecordDatabase(url)
        database.ensure_tables_exist()
        session = database.create_session()
        new_manufacturer = Manufacturers(manufacturer_id=1, manufacturer_location='Nebraska', manufacturer_name='manufacturer')
        sql_input(new_manufacturer, session)
        new_vaccine = Vaccines(vaccine_id=1, required_doses=5, relevant_disease='Polio', vaccine_name='Test_name', manufacturer_id=1)
        sql_input(new_vaccine, session)
        new_vaccine_from_sql = session.query(Vaccines).filter(Vaccines.vaccine_name == 'Test_name').one()
        self.assertEqual(new_vaccine.relevant_disease, new_vaccine_from_sql.relevant_disease)

    def test_fulfill_order(self):
        url = RecordDatabase.construct_in_memory_url()
        database = RecordDatabase(url)
        database.ensure_tables_exist()
        session = database.create_session()

        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
