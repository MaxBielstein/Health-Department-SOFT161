import mysql.connector
from kivy.core.window import Window  # For inspection.
from kivy.modules import inspector  # For inspection.
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp

from database import *

import mysql.connector
import json


# Screen Classes
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


class ReviewOrdersClinic(Screen):
    pass


class ReviewOrdersManufacturer(Screen):
    pass


class SelectOrder(Screen):
    pass


class OrderInformation(Screen):
    pass


class HomeScreen(Screen):
    pass


Persisted = declarative_base()


# Database
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


# App Class
def get_manufacturers_for_clinic(clinic_name):
    clinics_manufacturers = set()
    for clinic_id in get_sql_data('manufacturer_clinics', 'clinic_id'):
        if clinic_id == get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                              clinic_name)[0]:

            for manufacturer_id in (get_specific_sql_data('manufacturer_clinics', 'manufacturer_id',
                                                          'clinic_id', clinic_id)):
                clinics_manufacturers.add(
                    get_specific_sql_data('manufacturers', 'manufacturer_name', 'manufacturer_id', manufacturer_id)[
                        0])
    return clinics_manufacturers


class DistributionApp(MDApp):
    # clinics
    input_error_message = StringProperty('')
    new_clinic_name_property = StringProperty()
    new_clinic_address_property = StringProperty()
    new_clinic_ID_property = NumericProperty()
    new_clinic_current_clinic = StringProperty()
    # vaccines
    new_vaccine_name_property = StringProperty()
    new_vaccine_disease_property = StringProperty('Select a Disease')
    new_vaccine_ID_property = NumericProperty()
    new_vaccine_doses_property = NumericProperty()
    new_vaccine_manufacturer_ID_property = NumericProperty()
    # Orders
    new_order_ID_property = NumericProperty()
    new_order_manufacturer_ID_property = NumericProperty()
    new_order_vaccine_ID_property = NumericProperty()
    new_order_clinic_ID_property = NumericProperty()
    new_order_doses_property = NumericProperty()

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
        sm.add_widget(SelectManufacturerForClinic(name='m_for_clinic'))
        sm.add_widget(ReviewOrdersClinic(name='review_orders_clinic'))
        sm.add_widget(ReviewOrdersManufacturer(name='review_orders_manufacturer'))
        sm.add_widget(SelectOrder(name='select_order'))
        sm.add_widget(OrderInformation(name='order_information'))

        return sm

    def fulfillment_confirmation(self):
        self.root.get_screen('OrderInformation').ids.done_order_button.disabled = False

    def existing_clinic_clicked(self):
        self.root.get_screen('ExistingClinic').ids.clinics_spinner.values = get_sql_data('vaccination_clinics',
                                                                                         'clinic_name')

    def clear_new_vaccine_text(self):
        self.root.get_screen('m_for_vaccine').ids.new_vaccine_name.text = ""
        self.root.get_screen('m_for_vaccine').ids.new_vaccine_id.text = ""
        self.root.get_screen('m_for_vaccine').ids.new_vaccine_disease.text = "Select a Disease"
        self.root.get_screen('m_for_vaccine').ids.new_vaccine_required_doses.text = ""
        self.new_vaccine_disease_property = "Select a Disease"
        pass

    def prefill_existing_clinic(self):
        if 'Select a Clinic' not in self.root.get_screen(
                'ExistingClinic').ids.clinics_spinner.text:
            self.new_clinic_current_clinic = self.root.get_screen(
                'ExistingClinic').ids.clinics_spinner.text
            self.root.get_screen('ExistingClinic').ids.clinic_name_label.text = self.new_clinic_current_clinic

            self.root.get_screen('ExistingClinic').ids.clinic_address_label.text = \
                get_specific_sql_data('vaccination_clinics', 'clinic_address',
                                      'clinic_name', self.root.get_screen(
                        'ExistingClinic').ids.clinics_spinner.text)[0]

    def load_edit_clinic(self):
        self.root.get_screen(
            'm_for_clinic').ids.edit_clinic_label.text = "Add or Remove Manufacturers for: " + self.new_clinic_current_clinic

    # Spinner Loading Functions
    def load_manufacturer_spinners_for_clinics(self):
        if self.new_clinic_current_clinic is not '':
            clinics_manufacturers = get_manufacturers_for_clinic(self.new_clinic_current_clinic)
            self.root.get_screen(
                'm_for_clinic').ids.select_manufacturer_to_add_for_clinic_spinner.values = get_sql_data(
                'manufacturers',
                'manufacturer_name')

            self.root.get_screen(
                'm_for_clinic').ids.select_manufacturer_to_remove_for_clinic_spinner.values = clinics_manufacturers
        else:
            print('this will be an error message')

    def load_manufacturer_spinners_for_vaccines(self):
        self.root.get_screen('new_vaccine').ids.select_manufacturer_for_new_vaccine_spinner.values = get_sql_data(
            'manufacturers',
            'manufacturer_name')

    def load_spinners_for_orders(self):
        self.root.get_screen('review_orders_manufacturer').ids.select_manufacturer_review_order.values = get_sql_data(
            'manufacturers',
            'manufacturer_name')
        self.root.get_screen('review_orders_clinic').ids.select_clinic_review_order.values = get_sql_data(
            'vaccination_clinics',
            'clinic_name')

    def load_clinics_for_new_orders(self):
        self.root.get_screen('order_vaccine').ids.clinic_order_vaccine_spinner.values = get_sql_data(
            'vaccination_clinics',
            'clinic_name')
        # self.root.get_screen('order_vaccine').ids.order_manufacturer_spinner.text = ''
        self.root.get_screen('order_vaccine').ids.order_manufacturer_spinner.values = get_sql_data(
            'manufacturers',
            'manufacturer_name')

    def load_manufacturers_for_new_orders(self):
        self.root.get_screen('order_vaccine').ids.order_manufacturer_spinner.text = 'Select a Manufacturer'
        clinics_manufacturers = get_manufacturers_for_clinic(
            get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                  self.root.get_screen(
                                      'order_vaccine').ids.clinic_order_vaccine_spinner.text)[0])
        if len(clinics_manufacturers) == 0:
            self.root.get_screen(
                'order_vaccine').ids.order_manufacturer_spinner.text = 'No manufacturers \n        available\nfor selected clinic'
        else:
            self.root.get_screen('order_vaccine').ids.order_manufacturer_spinner.values = clinics_manufacturers

        self.root.get_screen('order_vaccine').ids.order_select_disease.text = 'Not Available'
        self.root.get_screen('order_vaccine').ids.order_select_disease.values = []

    def load_diseases_for_new_orders(self):
        self.root.get_screen('order_vaccine').ids.order_select_disease.text = 'Select a Disease'
        self.root.get_screen('order_vaccine').ids.order_select_disease.values = ['Covid', 'Measles', 'Smallpox',
                                                                                 'Anthrax', 'Mumps', 'Polio']

    # Selection Getting Methods
    def get_selected_manufacturer_for_vaccines(self):
        if 'Select a Manufacturer' in self.root.get_screen(
                'new_vaccine').ids.select_manufacturer_for_new_vaccine_spinner.text:
            print("no selection made(this will be an error message)")
        else:
            self.new_vaccine_manufacturer_ID_property = get_specific_sql_data('manufacturers', 'manufacturer_id',
                                                                              'manufacturer_name', self.root.get_screen(
                    'new_vaccine').ids.select_manufacturer_for_new_vaccine_spinner.text)[0]
            self.root.get_screen('m_for_vaccine').ids.manufacturer_chosen_for_new_vaccine.text = \
                get_specific_sql_data('manufacturers', 'manufacturer_name',
                                      'manufacturer_id', self.new_vaccine_manufacturer_ID_property)[0]

    # Methods called to start the process of creating new table entries
    def create_new_clinic(self):
        id_path = self.root.get_screen('clinic').ids
        if id_path.new_clinic_name.text is not '':
            self.new_clinic_name_property = id_path.new_clinic_name.text
            self.new_clinic_current_clinic = id_path.new_clinic_name.text

        if id_path.new_clinic_id.text is not '':
            self.new_clinic_ID_property = id_path.new_clinic_id.text

        if id_path.new_clinic_address.text is not '':
            self.new_clinic_address_property = id_path.new_clinic_address.text

        if self.check_for_required_inputs_new_clinic():
            new_clinic(self, self.new_clinic_name_property, self.new_clinic_address_property,
                       self.new_clinic_ID_property)

    def create_new_vaccine(self):
        id_path = self.root.get_screen('m_for_vaccine').ids
        if id_path.new_vaccine_name.text is not '':
            self.new_vaccine_name_property = id_path.new_vaccine_name.text

        if id_path.new_vaccine_id.text is not '':
            self.new_vaccine_ID_property = id_path.new_vaccine_id.text

        if id_path.new_vaccine_required_doses.text is not '':
            self.new_vaccine_doses_property = id_path.new_vaccine_required_doses.text

        if 'Select a Disease' not in id_path.new_vaccine_disease.text:
            self.new_vaccine_disease_property = id_path.new_vaccine_disease.text

        if self.check_for_required_inputs_new_vaccine():
            new_vaccine(self, self.new_vaccine_ID_property, self.new_vaccine_doses_property,
                        self.new_vaccine_disease_property, self.new_vaccine_name_property,
                        self.new_vaccine_manufacturer_ID_property)

    def create_new_order(self):
        # This one is incorrect and incomplete for now
        id_path = self.root.get_screen('order_vaccine').ids
        if 'Select a Clinic' not in id_path.clinic_order_vaccine_spinner.text:
            self.new_order_clinic_ID_property = get_specific_sql_data('vaccination_clinics', 'clinic_id',
                                                                      'clinic_name', self.root.get_screen(
                    'order_vaccine').ids.clinic_order_vaccine_spinner.text)[0]

        if 'Select a Disease' not in id_path.order_select_disease.text:
            self.new_order_clinic_ID_property = get_specific_sql_data('vaccination_clinics', 'clinic_id',
                                                                      'clinic_name', self.root.get_screen(
                    'order_vaccine').ids.clinic_order_vaccine_spinner.text)[0]

        if self.check_for_required_inputs_new_order():
            new_order(self, self.new_clinic_name_property, self.new_clinic_address_property,
                      self.new_clinic_ID_property)

    # Methods to check if all the needed fields to create new table entries are filled
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

    def check_for_required_inputs_new_vaccine(self):
        if self.new_vaccine_name_property is '':
            self.input_error_message = 'Name field must be filled'
            # Factory.NewInputError().open()
            return False
        elif self.new_vaccine_name_property in get_sql_data('vaccines', 'vaccine_name'):
            self.input_error_message = 'Vaccine with this name already exists'
            # Factory.NewInputError().open()
            return False
        if self.new_vaccine_ID_property is '':
            self.input_error_message = 'No ID for the vaccine was provided'
            # Factory.NewInputError().open()
            return False
        elif self.new_vaccine_ID_property in get_sql_data('vaccines', 'vaccine_id'):
            self.input_error_message = 'Vaccine with this ID already exists'
            # Factory.NewInputError().open()
            return False
        if self.new_vaccine_disease_property == 'Select a Disease':
            self.input_error_message = 'Disease field must be filled'
            # Factory.NewInputError().open()
            return False
        if self.new_vaccine_doses_property is '':
            self.input_error_message = 'Required Doses field must be filled'
            # Factory.NewInputError().open()
            return False
        if self.new_vaccine_manufacturer_ID_property is '':
            self.input_error_message = 'A Manufacturer ID was not correctly passed in'
            # Factory.NewInputError().open()
            return False
        return True

    def check_for_required_inputs_new_order(self):
        if self.new_order_ID_property is '':
            self.input_error_message = 'Order ID field must be filled'
            # Factory.NewInputError().open()
            return False
        elif self.new_order_ID_property in get_sql_data('orders', 'order_id'):
            self.input_error_message = 'Order with this ID already exists'
            # Factory.NewInputError().open()
            return False
        if self.new_order_vaccine_ID_property is '':
            self.input_error_message = 'Vaccine ID field must be filled'
            # Factory.NewInputError().open()
            return False
        if self.new_order_manufacturer_ID_property is '':
            self.input_error_message = 'Manufacturer ID field must be filled'
            # Factory.NewInputError().open()
            return False
        if self.new_order_clinic_ID_property is '':
            self.input_error_message = 'Clinic ID field must be filled'
            # Factory.NewInputError().open()
            return False
        if self.new_order_doses_property is '':
            self.input_error_message = 'Doses field must be filled'
            # Factory.NewInputError().open()
            return False
        return True


# methods that finalize creating new table entries, and committing them to the database
def new_clinic(self, name, address, id):
    clinic = VaccinationClinics(clinic_id=id, clinic_name=name, clinic_address=address)
    if int(clinic.clinic_id) not in get_sql_data('vaccination_clinics', 'clinic_id'):
        sql_input(clinic)
        # self.confirm_screen('new_person_confirmed')
    else:
        pass
        # Factory.MatchingIDError().open()


def new_vaccine(self, id, doses, disease, name, manufacturer_id):
    vaccine = Vaccines(vaccine_id=id, required_doses=doses, relevant_disease=disease, vaccine_name=name,
                       manufacturer_id=manufacturer_id)
    if int(vaccine.vaccine_id) not in get_sql_data('vaccines', 'vaccine_id'):
        sql_input(vaccine)
        # self.confirm_screen('new_person_confirmed')
    else:
        pass
        # Factory.MatchingIDError().open()


def new_order(self, order_id, manufacturer_id, clinic_id, vaccine_id, doses):
    order = VaccinationClinics(order_id=order_id, manufacturer_id=manufacturer_id, clinic_id=clinic_id,
                               vaccine_id=vaccine_id, doses_in_order=doses)
    if int(order.order_id) not in get_sql_data('orders', 'order_id'):
        sql_input(order)
        # self.confirm_screen('new_person_confirmed')
    else:
        pass
        # Factory.MatchingIDError().open()


# Loads the database credentials from the credentials.json file
with open('credentials.json', 'r') as credentials_file:
    data = json.load(credentials_file)
    host = data['host']
    database_name = data['database']
    user = data['username']
    password = data['password']


# These methods below query data from the database and return the specified data

# if column name is None then it returns the whole table
def get_sql_data(table_name, column_name):
    database = mysql.connector.connect(host=host, database=database_name, user=user, password=password)
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
    database = mysql.connector.connect(host=host, database=database_name, user=user, password=password)
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
    url = DistributionDatabase.construct_mysql_url(host, 3306, database_name, user, password)
    record_database = DistributionDatabase(url)
    session = record_database.create_session()
    session.add(data)
    session.commit()


if __name__ == '__main__':
    app = DistributionApp()
    app.run()
