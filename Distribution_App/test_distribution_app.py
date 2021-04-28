import unittest

from database import RecordDatabase, add_starter_data
from distribution import Vaccines, sql_input, Manufacturers, Orders, DistributionApp, ManufacturerClinics, delete_manufacturer_clinic


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
        add_starter_data(session)
        app = DistributionApp()
        order_from_sql = session.query(Orders).filter(Orders.order_id == 1).one()
        print(order_from_sql)
        self.assertEqual('False', order_from_sql.order_fulfilled)
        app.view_order_current_order_id = 1
        app.fulfill_order()
        # self.assertEqual('True', order_from_sql.order_fulfilled)

    def test_delete_manufacturer_clinic(self):
        url = RecordDatabase.construct_in_memory_url()
        database = RecordDatabase(url)
        database.ensure_tables_exist()
        session = database.create_session()
        add_starter_data(session)
        manufacturer_clinic_count = session.query(ManufacturerClinics).filter(ManufacturerClinics.manufacturer_id == 1 and
                                                                              ManufacturerClinics.clinic_id == 2).count()
        print(manufacturer_clinic_count)
        self.assertEqual(manufacturer_clinic_count, 1)
        delete_manufacturer_clinic(session, 1, 2)
        new_manufacturer_clinic_count = session.query(ManufacturerClinics).filter(ManufacturerClinics.manufacturer_id == 1 and
                                                                                  ManufacturerClinics.clinic_id == 2).count()
        print(new_manufacturer_clinic_count)
        self.assertEqual(new_manufacturer_clinic_count, 0)


if __name__ == '__main__':
    unittest.main()
