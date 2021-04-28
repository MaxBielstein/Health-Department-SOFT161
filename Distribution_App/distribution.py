import mysql.connector
import mysql.connector
import requests
from kivy.core.window import Window  # For inspection.
from kivy.factory import Factory
from kivy.modules import inspector  # For inspection.
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
import urllib.request

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from database import *


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


def get_manufacturers_for_clinic(clinic_name):
    clinics_manufacturers = set()
    for clinic_id in get_sql_data('manufacturer_clinics', 'clinic_id'):
        if len(get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                     clinic_name)) > 0:
            if clinic_id == get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                                  clinic_name)[0]:

                for manufacturer_id in (get_specific_sql_data('manufacturer_clinics', 'manufacturer_id',
                                                              'clinic_id', clinic_id)):
                    clinics_manufacturers.add(
                        get_specific_sql_data('manufacturers', 'manufacturer_name', 'manufacturer_id', manufacturer_id)[
                            0])
    return clinics_manufacturers


# App Class
class DistributionApp(MDApp):
    # Start property declarations

    # connection
    connection_message = StringProperty('')
    # message contents
    success_message = StringProperty('')
    input_error_message = StringProperty('')
    # clinics
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
    new_order_current_clinic = StringProperty()
    new_order_current_manufacturer = StringProperty()
    new_order_manufacturer_ids = set()
    # View orders
    view_order_manufacturer = StringProperty()
    view_order_clinic = StringProperty()
    view_order_current_order_id = NumericProperty()

    # end property declarations


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

    # Start Methods for miscellaneous kivy interaction

    def open_success_message(self, message):
        self.success_message = message
        Factory.NewConfirmation().open()

    def clear_edit_manufacturer_screen(self):
        self.root.get_screen(
            'select_order').ids.select_manufacturer_to_add_for_clinic_spinner.text = 'Available Manufacturers'
        self.root.get_screen(
            'select_order').ids.select_manufacturer_to_remove_for_clinic_spinner.text = 'Current Manufacturers'

    def order_selected_continue(self):
        spinner_text = self.root.get_screen('select_order').ids.select_order_to_review.text
        if spinner_text != 'No Orders for Selected Clinic' and spinner_text != 'No Orders for Selected Manufacturer' and \
                spinner_text != 'Not Available' and spinner_text != 'Select an Order':
            self.view_order_current_order_id = int(spinner_text.replace('Order with ID ', ''))
            self.root.current = 'order_information'

            self.root.get_screen('order_information').ids.order_information_order_id.text = str(
                self.view_order_current_order_id)
            self.root.get_screen('order_information').ids.order_information_clinic.text = \
                get_specific_sql_data('vaccination_clinics', 'clinic_name', 'clinic_id',
                                      get_specific_sql_data('orders', 'clinic_id', 'order_id',
                                                            self.view_order_current_order_id)[0])[0]
            self.root.get_screen('order_information').ids.order_information_manufacturer.text = \
                get_specific_sql_data('manufacturers', 'manufacturer_name', 'manufacturer_id',
                                      get_specific_sql_data('orders', 'manufacturer_id', 'order_id',
                                                            self.view_order_current_order_id)[0])[0]
            self.root.get_screen('order_information').ids.order_information_doses.text = \
                str(get_specific_sql_data('orders', 'doses_in_order', 'order_id',
                                          self.view_order_current_order_id)[0])
            self.root.get_screen('order_information').ids.order_information_fulfillment.text = \
                get_specific_sql_data('orders', 'order_fulfilled', 'order_id',
                                      self.view_order_current_order_id)[0]
        else:
            self.input_error_message = 'Order must be selected'
            Factory.NewInputError().open()

    def fulfill_order(self):
        try:
            order = session.query(Orders).filter(Orders.order_id == self.view_order_current_order_id).one()
            order.order_fulfilled = 'True'
            session.commit()
        except NoResultFound:
            self.input_error_message = 'Order not found'
            Factory.NewInputError().open()
        except MultipleResultsFound:
            self.input_error_message = 'Multiple order results found!'
            Factory.NewInputError().open()
        except SQLAlchemyError:
            self.input_error_message = 'Database setup failed!'
            Factory.NewInputError().open()

    def fulfillment_confirmation(self):
        self.root.get_screen('OrderInformation').ids.done_order_button.disabled = False

    def existing_clinic_select_clinic(self):
        if self.root.get_screen('ExistingClinic').ids.clinics_spinner.text != "Clinics":
            self.root.current = 'm_for_clinic'

        else:
            self.input_error_message = 'Clinic must be selected'
            Factory.NewInputError().open()
            self.on_done()

    def continue_order_manufacturer(self):
        if self.root.get_screen(
                'review_orders_manufacturer').ids.select_manufacturer_review_order.text != "Select a Manufacturer":
            self.view_order_manufacturer = self.root.get_screen(
                'review_orders_manufacturer').ids.select_manufacturer_review_order.text
            self.root.current = 'select_order'

        else:
            self.input_error_message = 'Manufacturer must be selected'
            Factory.NewInputError().open()

    def continue_order_clinic(self):
        if self.root.get_screen('review_orders_clinic').ids.select_clinic_review_order.text != "Select a Clinic":
            self.view_order_clinic = self.root.get_screen('review_orders_clinic').ids.select_clinic_review_order.text
            self.root.current = 'select_order'
        else:
            self.input_error_message = 'Clinic must be selected'
            Factory.NewInputError().open()

    def prefill_existing_clinic(self):
        if 'Select a Clinic' not in self.root.get_screen(
                'ExistingClinic').ids.clinics_spinner.text:
            self.new_clinic_current_clinic = self.root.get_screen(
                'ExistingClinic').ids.clinics_spinner.text
            self.root.get_screen('ExistingClinic').ids.clinic_name_label.text = self.new_clinic_current_clinic

            if len(get_specific_sql_data('vaccination_clinics', 'clinic_address',
                                         'clinic_name', self.root.get_screen(
                        'ExistingClinic').ids.clinics_spinner.text)) > 0:
                self.root.get_screen('ExistingClinic').ids.clinic_address_label.text = \
                    get_specific_sql_data('vaccination_clinics', 'clinic_address',
                                          'clinic_name', self.root.get_screen(
                            'ExistingClinic').ids.clinics_spinner.text)[0]

    def load_edit_clinic(self):
        self.root.get_screen(
            'm_for_clinic').ids.edit_clinic_label.text = "Add or Remove Manufacturers for: " + self.new_clinic_current_clinic

    def select_vaccine_for_new_order(self):
        disease = self.root.get_screen('order_vaccine').ids.order_select_disease.text
        if disease != 'No diseases \n        available\n for selected manufacturer' and disease != 'Not Available' and \
                disease != '' and disease != 'Select a Disease':
            vaccines_filtered_by_manufacturer = set(get_specific_sql_data('vaccines', 'vaccine_name', 'manufacturer_id',
                                                                          self.new_order_manufacturer_ids[0]))

            vaccines_filtered_by_disease = set(get_specific_sql_data('vaccines', 'vaccine_name', 'relevant_disease',
                                                                     self.root.get_screen(
                                                                         'order_vaccine').ids.order_select_disease.text))
            approved_vaccines = vaccines_filtered_by_manufacturer.intersection(vaccines_filtered_by_disease)
            if len(approved_vaccines) != 0:
                self.new_order_vaccine_ID_property = get_specific_sql_data('vaccines', 'vaccine_id', 'vaccine_name',
                                                                           list(approved_vaccines)[0])[0]
                self.root.get_screen('order_vaccine').ids.new_order_vaccine.text = 'Assigned Vaccine: ' + \
                                                                                   list(approved_vaccines)[0]

    def get_selected_manufacturer_for_vaccines(self):
        if 'Select a Manufacturer' in self.root.get_screen(
                'new_vaccine').ids.select_manufacturer_for_new_vaccine_spinner.text:
            self.input_error_message = 'You must select a manufacturer'
            Factory.NewInputError().open()
            self.on_done()
        else:
            self.new_vaccine_manufacturer_ID_property = get_specific_sql_data('manufacturers', 'manufacturer_id',
                                                                              'manufacturer_name', self.root.get_screen(
                    'new_vaccine').ids.select_manufacturer_for_new_vaccine_spinner.text)[0]
            self.root.get_screen('m_for_vaccine').ids.manufacturer_chosen_for_new_vaccine.text = \
                get_specific_sql_data('manufacturers', 'manufacturer_name',
                                      'manufacturer_id', self.new_vaccine_manufacturer_ID_property)[0]

            self.root.current = 'm_for_vaccine'

    def add_manufacturer_to_clinic(self):
        selected_manufacturer = self.root.get_screen(
            'm_for_clinic').ids.select_manufacturer_to_add_for_clinic_spinner.text
        if selected_manufacturer == 'Available Manufacturers':
            self.input_error_message = 'You must select a manufacturer'
            Factory.NewInputError().open()
        else:

            if len(get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                         self.new_clinic_current_clinic)) > 0:
                clinic_id = get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                                  self.new_clinic_current_clinic)[0]
                if len(get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                             self.new_clinic_current_clinic)) > 0:
                    manufacturer_id = get_specific_sql_data('manufacturers', 'manufacturer_id', 'manufacturer_name',
                                                            selected_manufacturer)[0]
                    new_manufacturer_clinic(self, manufacturer_id, clinic_id)
                    self.load_manufacturer_spinners_for_clinics()
                else:
                    self.input_error_message = 'Manufacturer ID not found'
                    Factory.NewInputError().open()

            else:
                self.input_error_message = 'Clinic ID not found'
                Factory.NewInputError().open()

    def remove_manufacturer_from_clinic(self):
        selected_manufacturer = self.root.get_screen(
            'm_for_clinic').ids.select_manufacturer_to_remove_for_clinic_spinner.text
        if selected_manufacturer == 'Current Manufacturers':
            self.input_error_message = 'You must select a manufacturer'
            Factory.NewInputError().open()
        else:

            if len(get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                         self.new_clinic_current_clinic)) > 0:
                clinic_id = get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                                  self.new_clinic_current_clinic)[0]
                if len(get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                             self.new_clinic_current_clinic)) > 0:
                    manufacturer_id = get_specific_sql_data('manufacturers', 'manufacturer_id', 'manufacturer_name',
                                                            selected_manufacturer)[0]
                    try:
                        delete_manufacturer_clinic(session, manufacturer_id, clinic_id)
                    except ValueError:
                        print('value error')
                        self.input_error_message = 'Manufacturer Clinic Not Found'
                        Factory.NewInputError().open()
                    except SQLAlchemyError:
                        print('sql alchemy error')
                        self.input_error_message = 'Could Not Open Database'
                        Factory.NewInputError().open()
                    self.open_success_message(
                        f'Manufacturer Clinic with Manufacturer id {manufacturer_id}\n and Clinic id {clinic_id} deleted')
                    self.load_manufacturer_spinners_for_clinics()
                else:
                    self.input_error_message = 'Manufacturer ID not found'
                    Factory.NewInputError().open()

            else:
                self.input_error_message = 'Clinic ID not found'
                Factory.NewInputError().open()

    # End Methods for miscellaneous kivy interaction
    #
    #
    # Start Spinner Loading Functions Section

    def existing_clinic_clicked(self):
        self.root.get_screen('ExistingClinic').ids.clinics_spinner.values = get_sql_data('vaccination_clinics',
                                                                                         'clinic_name')

    def populate_view_orders_select_order_spinner(self):
        values = []
        formatted_values = list()
        if self.view_order_manufacturer != '':
            man_id = get_specific_sql_data('manufacturers', 'manufacturer_id', 'manufacturer_name',
                                           self.view_order_manufacturer)[0]
            self.root.get_screen('select_order').ids.select_order_to_review.text = 'Select an Order'
            values = get_specific_sql_data('orders', 'order_id', 'manufacturer_id', man_id)
            for value in values:
                formatted_values.append('Order with ID ' + str(value))
            if len(formatted_values) == 0:
                self.root.get_screen(
                    'select_order').ids.select_order_to_review.text = 'No Orders for Selected Manufacturer'
            self.root.get_screen('select_order').ids.select_order_to_review.values = formatted_values

        if self.view_order_clinic != '':
            clin_id = get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name', self.view_order_clinic)[
                0]
            self.root.get_screen('select_order').ids.select_order_to_review.text = 'Select an Order'
            values = get_specific_sql_data('orders', 'order_id', 'clinic_id', clin_id)
            for value in values:
                formatted_values.append('Order with ID ' + str(value))
            if len(formatted_values) == 0:
                self.root.get_screen('select_order').ids.select_order_to_review.text = 'No Orders for Selected Clinic'
            self.root.get_screen('select_order').ids.select_order_to_review.values = formatted_values

    def load_manufacturer_spinners_for_clinics(self):
        if self.new_clinic_current_clinic is not '':
            all_manufacturers = get_sql_data('manufacturers', 'manufacturer_name')
            clinics_manufacturers = get_manufacturers_for_clinic(self.new_clinic_current_clinic)
            unused_manufacturers = []
            for manufacturer in all_manufacturers:
                if manufacturer not in clinics_manufacturers:
                    unused_manufacturers.append(manufacturer)
            self.root.get_screen(
                'm_for_clinic').ids.select_manufacturer_to_add_for_clinic_spinner.values = unused_manufacturers
            self.root.get_screen(
                'm_for_clinic').ids.select_manufacturer_to_add_for_clinic_spinner.text = 'Available Manufacturers'

            self.root.get_screen(
                'm_for_clinic').ids.select_manufacturer_to_remove_for_clinic_spinner.values = clinics_manufacturers
            self.root.get_screen(
                'm_for_clinic').ids.select_manufacturer_to_remove_for_clinic_spinner.text = 'Current Manufacturers'

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
        if len(get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                     self.root.get_screen(
                                         'order_vaccine').ids.clinic_order_vaccine_spinner.text)) > 0:
            self.new_order_clinic_ID_property = get_specific_sql_data('vaccination_clinics', 'clinic_id', 'clinic_name',
                                                                      self.root.get_screen(
                                                                          'order_vaccine').ids.clinic_order_vaccine_spinner.text)[
                0]
        self.root.get_screen('order_vaccine').ids.new_order_clinic.text = 'Chosen Clinic: ' + self.root.get_screen(
            'order_vaccine').ids.clinic_order_vaccine_spinner.text
        self.root.get_screen('order_vaccine').ids.order_manufacturer_spinner.text = 'Select a Manufacturer'
        clinics_manufacturers = get_manufacturers_for_clinic(
            self.root.get_screen('order_vaccine').ids.clinic_order_vaccine_spinner.text)
        if len(clinics_manufacturers) == 0:
            self.root.get_screen(
                'order_vaccine').ids.order_manufacturer_spinner.text = 'No manufacturers \n        available\nfor selected clinic'
            self.root.get_screen('order_vaccine').ids.order_manufacturer_spinner.values = set()
        else:
            self.root.get_screen('order_vaccine').ids.order_manufacturer_spinner.values = clinics_manufacturers

        self.root.get_screen('order_vaccine').ids.order_select_disease.text = 'Not Available'
        self.root.get_screen('order_vaccine').ids.order_select_disease.values = []

    def load_diseases_for_new_orders(self):
        self.new_order_manufacturer_ids = get_specific_sql_data('manufacturers', 'manufacturer_id', 'manufacturer_name',
                                                                self.root.get_screen(
                                                                    'order_vaccine').ids.order_manufacturer_spinner.text)
        if len(self.new_order_manufacturer_ids) > 0:
            self.new_order_manufacturer_ID_property = self.new_order_manufacturer_ids[0]
            new_order_disease_list = get_specific_sql_data('vaccines', 'relevant_disease', 'manufacturer_id',
                                                           self.new_order_manufacturer_ID_property)
            self.root.get_screen('order_vaccine').ids.order_select_disease.values = new_order_disease_list
        else:
            self.root.get_screen(
                'order_vaccine').ids.order_select_disease.text = 'No diseases \n        available\n for selected manufacturer'
            self.root.get_screen('order_vaccine').ids.order_select_disease.values = []

        self.root.get_screen('order_vaccine').ids.order_select_disease.text = 'Select a Disease'

    # End Spinner Loading Functions Section
    #
    #
    # Start methods called to start the process of creating new table entries

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
            self.root.current = 'm_for_clinic'
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

        if id_path.order_id.text != '':
            self.new_order_ID_property = id_path.order_id.text

        if id_path.order_doses.text != '':
            self.new_order_doses_property = id_path.order_id.text

        if self.check_for_required_inputs_new_order():
            new_order(self, self.new_order_ID_property, self.new_order_manufacturer_ID_property,
                      self.new_order_clinic_ID_property, self.new_order_vaccine_ID_property,
                      self.new_order_doses_property)

    # End methods called to start the process of creating new table entries
    #
    #
    # Start methods to check if all the needed fields to create new table entries are filled

    def check_for_required_inputs_new_clinic(self):
        if self.new_clinic_name_property is '':
            self.input_error_message = 'Name field must be filled'
            Factory.NewInputError().open()
            self.on_done()
            return False
        elif self.new_clinic_name_property in get_sql_data('vaccination_clinics', 'clinic_name'):
            self.input_error_message = 'Clinic with this name already exists'
            Factory.NewInputError().open()
            self.on_done()
            return False
        if self.new_clinic_ID_property is 0:
            self.input_error_message = 'no id found'
            Factory.NewInputError().open()
            self.on_done()
            return False
        elif self.new_clinic_ID_property in get_sql_data('vaccination_clinics', 'clinic_id'):
            self.input_error_message = 'Clinic with this ID already exists'
            Factory.NewInputError().open()
            self.on_done()
            return False
        if self.new_clinic_address_property is '':
            self.input_error_message = 'Address field must be filled'
            Factory.NewInputError().open()
            self.on_done()
            return False
        elif self.new_clinic_address_property in get_sql_data('vaccination_clinics', 'clinic_address'):
            self.input_error_message = 'Clinic with this address already exists'
            Factory.NewInputError().open()
            self.on_done()
            return False
        return True

    def check_for_required_inputs_new_vaccine(self):
        if self.new_vaccine_name_property is '':
            self.input_error_message = 'Name field must be filled'
            Factory.NewInputError().open()
            self.on_done()
            return False
        elif self.new_vaccine_name_property in get_sql_data('vaccines', 'vaccine_name'):
            self.input_error_message = 'Vaccine with this name already exists'
            Factory.NewInputError().open()
            self.on_done()
            return False
        if self.new_vaccine_ID_property is 0:
            self.input_error_message = 'No ID for the vaccine was provided'
            Factory.NewInputError().open()
            self.on_done()
            return False
        elif self.new_vaccine_ID_property in get_sql_data('vaccines', 'vaccine_id'):
            self.input_error_message = 'Vaccine with this ID already exists'
            Factory.NewInputError().open()
            self.on_done()
            return False
        if self.new_vaccine_disease_property == 'Select a Disease':
            self.input_error_message = 'Disease field must be filled'
            Factory.NewInputError().open()
            self.on_done()
            return False
        if self.new_vaccine_doses_property is 0:
            self.input_error_message = 'Required Doses field must be filled'
            Factory.NewInputError().open()
            self.on_done()
            return False
        if self.new_vaccine_manufacturer_ID_property is 0:
            self.input_error_message = 'A Manufacturer ID was not correctly passed in'
            Factory.NewInputError().open()
            self.on_done()
            return False
        return True

    def check_for_required_inputs_new_order(self):
        if self.new_order_ID_property is 0:
            self.input_error_message = 'Order ID field must be filled'
            Factory.NewInputError().open()
            self.on_done()
            return False
        elif self.new_order_ID_property in get_sql_data('orders', 'order_id'):
            self.input_error_message = 'Order with this ID already exists'
            Factory.NewInputError().open()
            self.on_done()
            return False
        if self.new_order_vaccine_ID_property is 0:
            self.input_error_message = 'No Vaccine found'
            Factory.NewInputError().open()
            self.on_done()
            return False
        if self.new_order_manufacturer_ID_property is 0:
            self.input_error_message = 'Manufacturer ID field must be filled'
            Factory.NewInputError().open()
            self.on_done()
            return False
        if self.new_order_clinic_ID_property is 0:
            self.input_error_message = 'No Clinic Selected'
            Factory.NewInputError().open()
            self.on_done()
            return False
        if self.new_order_doses_property is 0:
            self.input_error_message = 'Doses field must be filled'
            Factory.NewInputError().open()
            self.on_done()
            return False
        return True

    # End methods to check if all the needed fields to create new table entries are filled

    # Method that clears literally everything in the app. This is called every time 'done' is selected, and at other various times
    # that things need to be cleared.
    def on_done(self):

        self.new_vaccine_name_property = ''
        self.new_vaccine_ID_property = 0
        self.new_vaccine_disease_property = 'Select a Disease'
        self.new_vaccine_doses_property = 0
        self.new_vaccine_manufacturer_ID_property = 0
        self.new_order_ID_property = 0
        self.new_order_manufacturer_ID_property = 0
        self.new_order_vaccine_ID_property = 0
        self.new_order_clinic_ID_property = 0
        self.new_order_doses_property = 0
        self.new_order_current_clinic = ''
        self.new_order_current_manufacturer = ''
        self.new_clinic_name_property = ''
        self.new_clinic_address_property = ''
        self.new_clinic_ID_property = 0
        self.new_clinic_current_clinic = ''
        self.view_order_manufacturer = ''
        self.view_order_clinic = ''
        self.view_order_current_order_id = 0

        self.root.get_screen('clinic').ids.new_clinic_name.text = ''
        self.root.get_screen('clinic').ids.new_clinic_address.text = ''
        self.root.get_screen('clinic').ids.new_clinic_id.text = ''

        self.root.get_screen('ExistingClinic').ids.clinics_spinner.text = 'Clinics'
        self.root.get_screen('ExistingClinic').ids.clinic_name_label.text = ''
        self.root.get_screen('ExistingClinic').ids.clinic_address_label.text = ''

        self.root.get_screen('m_for_clinic').ids.edit_clinic_label.text = ''
        self.root.get_screen(
            'm_for_clinic').ids.select_manufacturer_to_remove_for_clinic_spinner.text = 'Current Manufacturers'
        self.root.get_screen(
            'm_for_clinic').ids.select_manufacturer_to_add_for_clinic_spinner.text = 'Available Manufacturers'

        self.root.get_screen(
            'new_vaccine').ids.select_manufacturer_for_new_vaccine_spinner.text = 'Select a Manufacturer'

        self.root.get_screen('m_for_vaccine').ids.manufacturer_chosen_for_new_vaccine.text = ''
        self.root.get_screen('m_for_vaccine').ids.new_vaccine_name.text = ''
        self.root.get_screen('m_for_vaccine').ids.new_vaccine_id.text = ''
        self.root.get_screen('m_for_vaccine').ids.new_vaccine_required_doses.text = ''
        self.root.get_screen('m_for_vaccine').ids.new_vaccine_disease.text = 'Select a Disease'

        self.root.get_screen('order_vaccine').ids.clinic_order_vaccine_spinner.text = 'Select a Clinic'
        self.root.get_screen('order_vaccine').ids.order_manufacturer_spinner.text = 'Not Available'
        self.root.get_screen('order_vaccine').ids.order_select_disease.text = 'Not Available'
        self.root.get_screen('order_vaccine').ids.new_order_clinic.text = 'Chosen Clinic: '
        self.root.get_screen('order_vaccine').ids.new_order_vaccine.text = 'Assigned Vaccine: '
        self.root.get_screen('order_vaccine').ids.order_doses.text = ''
        self.root.get_screen('order_vaccine').ids.order_id.text = ''

        self.root.get_screen('review_orders_clinic').ids.select_clinic_review_order.text = 'Select a Clinic'

        self.root.get_screen(
            'review_orders_manufacturer').ids.select_manufacturer_review_order.text = 'Select a Manufacturer'

        self.root.get_screen('select_order').ids.select_order_to_review.text = 'Not Available'
        self.root.get_screen('select_order').ids.select_order_to_review.values = list()

        self.root.get_screen('order_information').ids.order_information_order_id.text = ''
        self.root.get_screen('order_information').ids.order_information_clinic.text = ''
        self.root.get_screen('order_information').ids.order_information_manufacturer.text = ''
        self.root.get_screen('order_information').ids.order_information_doses.text = ''
        self.root.get_screen('order_information').ids.order_information_fulfillment.text = ''


# Start methods that finalize creating or removing table entries, and committing them to the database
def new_clinic(self, name, address, id):
    clinic = VaccinationClinics(clinic_id=id, clinic_name=name, clinic_address=address)
    if int(clinic.clinic_id) not in get_sql_data('vaccination_clinics', 'clinic_id'):
        sql_input(clinic, session)
        self.on_done()
        self.open_success_message('Clinic Created Successfully')
    else:
        Factory.MatchingIDError().open()
        self.on_done()


def new_manufacturer_clinic(self, manufacturer_id, clinic_id):
    manufacturer_clinic = ManufacturerClinics(clinic_id=clinic_id, manufacturer_id=manufacturer_id)
    sql_input(manufacturer_clinic, session)
    self.open_success_message('Manufacturer Clinic Created Successfully')


def delete_manufacturer_clinic(session, manufacturer_id, clinic_id):
    manufacturer_clinics = session.query(ManufacturerClinics).filter(
        ManufacturerClinics.manufacturer_id == manufacturer_id and
        ManufacturerClinics.manufacturer_id == clinic_id).count
    if manufacturer_clinics is 0:
        raise ValueError(
            f"No Manufacturer Clinics with Manufacturer id {manufacturer_id}\n and Clinic id {clinic_id}")
    session.query(ManufacturerClinics).filter(ManufacturerClinics.manufacturer_id == manufacturer_id and
                                              ManufacturerClinics.manufacturer_id == clinic_id).delete()
    session.commit()


def new_vaccine(self, id, doses, disease, name, manufacturer_id):
    vaccine = Vaccines(vaccine_id=id, required_doses=doses, relevant_disease=disease, vaccine_name=name,
                       manufacturer_id=manufacturer_id)
    if int(vaccine.vaccine_id) not in get_sql_data('vaccines', 'vaccine_id'):
        sql_input(vaccine, session)
        self.on_done()
        self.open_success_message('Vaccine Created Successfully')
    else:
        Factory.MatchingIDError().open()
        self.on_done()


def new_order(self, order_id, manufacturer_id, clinic_id, vaccine_id, doses):
    order = Orders(order_id=order_id, manufacturer_id=manufacturer_id, clinic_id=clinic_id,
                   vaccine_id=vaccine_id, doses_in_order=doses, order_fulfilled='False')
    if int(order.order_id) not in get_sql_data('orders', 'order_id'):
        sql_input(order, session)
        self.on_done()
        self.open_success_message('Order Created Successfully')
        self.root.current = 'home'
    else:
        Factory.MatchingIDError().open()
        self.on_done()


# End methods that finalize creating new table entries, and committing them to the database

# Loads the database credentials from the credentials.json file
try:
    with open('credentials.json', 'r') as credentials_file:
        data = json.load(credentials_file)
        host = data['host']
        database_name = data['database']
        user = data['username']
        password = data['password']
except FileNotFoundError:
    print('Database connection failed!')
    print('credentials.json not found')


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


url = DistributionDatabase.construct_mysql_url(host, 3306, database_name, user, password)
record_database = DistributionDatabase(url)
session = record_database.create_session()


# This is a simple method for adding data to the sql database
def sql_input(data, session):
    session.add(data)
    session.commit()


if __name__ == '__main__':
    app = DistributionApp()
    app.run()
