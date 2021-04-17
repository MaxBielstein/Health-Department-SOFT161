from kivy.app import App
from kivy.factory import Factory
from kivy.properties import NumericProperty, StringProperty
from kivymd.app import MDApp
from kivy.core.window import Window  # For inspection.
from kivy.modules import inspector  # For inspection.
from kivy.uix.screenmanager import ScreenManager, Screen
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from database import *
import mysql.connector


class ClinicScreen(Screen):
    pass


class ManufacturerForVaccine(Screen):
    pass


class ExistingClinic(Screen):
    pass


class SelectManufacturerForClinic(Screen):
    pass


class NewVaccineScreen(Screen):
    pass


class OrderVaccineScreen(Screen):
    pass


class OrderManufacturer(Screen):
    pass


class HomeScreen(Screen):
    pass


Persisted = declarative_base()


# noinspection PyInterpreter
class DistributionDatabase(object):
    @staticmethod
    def construct_mysql_url(authority, port, database, username, password):
        return f'mysql+mysqlconnector://{username}:{password}@{authority}:{port}/{database}'

    @staticmethod
    def construct_in_memory_url():
        return 'sqlite:///'

    def __init__(self, url):
        self.engine = create_engine(url)
        self.Session = sessionmaker()  # pylint: disable=invalid-name
        self.Session.configure(bind=self.engine)

    def ensure_tables_exist(self):
        Persisted.metadata.create_all(self.engine)

    def create_session(self):
        return self.Session()


class DistributionApp(MDApp):
    input_error_message = StringProperty('')
    new_clinic_name_property = StringProperty()
    new_clinic_address_property = StringProperty()
    new_clinic_ID_property = NumericProperty()

    def build(self):
        self.theme_cls.primary_palette = "Blue"

        inspector.create_inspector(Window, self)  # For inspection (press control-e to toggle).
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ClinicScreen(name='clinic'))
        sm.add_widget(NewVaccineScreen(name='new_vaccine'))
        sm.add_widget(ManufacturerForVaccine(name='m_for_vaccine'))
        sm.add_widget(ExistingClinic(name='ExistingClinic'))
        sm.add_widget(OrderVaccineScreen(name='order_vaccine'))
        sm.add_widget(OrderManufacturer(name='m_for_order'))
        sm.add_widget(SelectManufacturerForClinic(name='m_for_clinic'))

        return sm

    def existing_clinic_clicked(self):
        self.root.get_screen('ExistingClinic').ids.clinics_spinner.values = get_sql_data('vaccination_clinics',
                                                                                         'clinic_name')

    def load_manufacturer_spinners_for_clinics(self):
        self.root.get_screen('m_for_clinic').ids.select_manufacturer_to_add_for_clinic_spinner.values = get_sql_data(
            'manufacturers',
            'manufacturer_name')

    def load_manufacturer_spinners_for_vaccines(self):
        self.root.get_screen('new_vaccine').ids.select_manufacturer_for_new_vaccine_spinner.values = get_sql_data(
            'manufacturers',
            'manufacturer_name')

# The following methods handle creating a new clinic, checking its requirements, and adding it to the database
    def create_new_clinic(self):
        id_path = self.root.get_screen('clinic').ids
        if id_path.new_clinic_name.text is not '':
            self.new_clinic_name_property = id_path.new_clinic_name.text

        if id_path.new_clinic_id.text is not '':
            self.new_clinic_ID_property = id_path.new_clinic_id.text

        if id_path.new_clinic_address.text is not '':
            self.new_clinic_address_property = id_path.new_clinic_address.text

        if self.check_for_required_inputs_new_clinic():
            new_clinic(self, self.new_clinic_name_property, self.new_clinic_address_property,
                       self.new_clinic_ID_property)

    def check_for_required_inputs_new_clinic(self):
        if self.new_clinic_name_property is '':
            self.input_error_message = 'Name field must be filled'
            # Factory.NewInputError().open()
            return False
        elif self.new_clinic_name_property in get_sql_data('vaccination_clinics', 'clinic_name'):
            self.input_error_message = 'Clinic with this name already exists'
            # Factory.NewInputError().open()
            return False
        if self.new_clinic_ID_property is '':
            self.input_error_message = 'no id found'
            # Factory.NewInputError().open()
            return False
        elif self.new_clinic_ID_property in get_sql_data('vaccination_clinics', 'clinic_id'):
            self.input_error_message = 'Clinic with this ID already exists'
            # Factory.NewInputError().open()
            return False
        if self.new_clinic_address_property is '':
            self.input_error_message = 'Address field must be filled'
            # Factory.NewInputError().open()
            return False
        elif self.new_clinic_address_property in get_sql_data('vaccination_clinics', 'clinic_address'):
            self.input_error_message = 'Clinic with this address already exists'
            # Factory.NewInputError().open()
            return False
        return True


def new_clinic(self, name, address, id):
    clinic = VaccinationClinics(clinic_id=id, clinic_name=name, clinic_address=address)
    if int(clinic.clinic_id) not in get_sql_data('vaccination_clinics', 'clinic_id'):
        sql_input(clinic)
        # self.confirm_screen('new_person_confirmed')
    else:
        Factory.MatchingIDError().open()


# These methods below query data from the database and return the specified data

# if column name is None then it returns the whole table
def get_sql_data(table_name, column_name):
    database = mysql.connector.connect(host='localhost', database='combined', user='root', password='cse1208')
    finder = database.cursor(buffered=True)
    if column_name is None:
        finder.execute(f'SELECT * FROM {table_name}')
        return finder.fetchall()
    else:
        finder.execute(f'SELECT {column_name} FROM {table_name}')
        list_of_columns = []
        for element in finder.fetchall():
            list_of_columns.append(element[0])
        return list_of_columns


# returns a single element from table
def get_specific_sql_data(table_name, column, identifier_column, oracle):
    database = mysql.connector.connect(host='localhost', database='combined', user='root', password='cse1208')
    finder = database.cursor(buffered=True)
    finder.execute(f'select {column} from {table_name} where {identifier_column} = \"{oracle}\"')
    result = finder.fetchall()
    return_list = []
    for item in result:
        return_list.append(item[0])

    if len(return_list) is not 0:
        return return_list
    else:
        return []


# This is a simple method for adding data to the sql database
def sql_input(data):
    url = DistributionDatabase.construct_mysql_url('localhost', 3306, 'combined', 'root', 'cse1208')
    record_database = DistributionDatabase(url)
    session = record_database.create_session()
    session.add(data)
    session.commit()


if __name__ == '__main__':
    app = DistributionApp()
    app.run()
