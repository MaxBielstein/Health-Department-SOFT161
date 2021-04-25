import enum
from json import dumps
from time import sleep

import sqlalchemy
from kivy import Config

Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '1000')
Config.set('graphics', 'minimum_width', '1200')
Config.set('graphics', 'minimum_height', '1000')

from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivymd.uix.label import MDLabel
from kivy.app import App
from kivy.factory import Factory
from kivy.properties import NumericProperty, StringProperty
from kivymd.app import MDApp
from kivy.core.window import Window  # For inspection.
from kivy.modules import inspector  # For inspection.
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from database import *
import mysql.connector
from openmrs import RESTConnection


class HomeScreen(Screen):
    pass


class LoadingLogin(Screen):
    pass


class DataPreview(Screen):
    pass


class ImportingLoading(Screen):
    pass


class RecordType(enum.Enum):
    OTHER_RECORD = 'OTHER_RECORD'
    IMPORT_RECORD = 'IMPORT_RECORD'
    UNMATCHED_RECORD = 'UNMATCHED_RECORD'


class Health_departmentApp(MDApp):
    host = StringProperty()
    database_name = StringProperty()
    user = StringProperty()
    password = StringProperty()
    port = StringProperty()

    openmrs_host = StringProperty()
    openmrs_user = StringProperty()
    openmrs_password = StringProperty()
    openmrs_port = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_defaults()

    def build(self):
        self.theme_cls.primary_palette = "Blue"

        inspector.create_inspector(Window, self)  # For inspection (press control-e to toggle).
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(LoadingLogin(name='LoadingLogin'))
        sm.add_widget(DataPreview(name='DataPreview'))
        sm.add_widget(ImportingLoading(name='ImportingLoading'))

        return sm

    def load_defaults(self):
        self.load_credentials_file()
        self.port = '3306'
        self.openmrs_port = '8080'
        self.openmrs_host = 'localhost'
        self.openmrs_user = 'admin'
        # TODO remove line below
        self.openmrs_password = 'Admin123'

    def login_button(self):
        global app_reference
        app_reference = self
        if self.load_login_credentials():
            if connect_to_databases(self):
                test_openmrs_connection()

    def load_login_credentials(self):
        try:
            path = self.root.get_screen('home').ids
            self.host = path.database_host.text
            self.database_name = path.database_database.text
            self.user = path.database_username.text
            self.password = path.database_password.text

            self.port = path.database_port.text

            self.openmrs_port = path.openmrs_port.text

            self.openmrs_user = path.openmrs_username.text
            self.openmrs_host = path.openmrs_host.text
            self.openmrs_password = path.openmrs_password.text
            return True
        except ValueError:
            print('value error')
            return False

    def abort_button(self):
        self.clear_data_preview_screen()
        self.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value = 0

    def clear_data_preview_screen(self):
        global number_of_records_to_load
        global number_of_records_loaded
        global patient_uuids
        global unmatched_records
        global other_records
        global location_to_import_records
        global import_records
        global existing_observations
        global openmrs_disconnected
        global concepts
        number_of_records_to_load = 0
        number_of_records_loaded = 0
        patient_uuids = {}
        unmatched_records = []
        import_records = []
        existing_observations = []
        location_to_import_records = []
        openmrs_disconnected = False
        concepts = []
        self.root.get_screen('DataPreview').ids.scrollview_left.clear_widgets()
        self.root.get_screen('DataPreview').ids.scrollview_right.clear_widgets()

    def import_button(self):
        import_data_into_openmrs()

    def load_credentials_file(self):
        try:
            with open('credentials.json', 'r') as credentials_file:
                credentials = json.load(credentials_file)
                self.host = credentials['host']
                self.database_name = credentials['database']
                self.user = credentials['username']
                self.password = credentials['password']
        except FileNotFoundError:
            # Replace this with error prompt in app
            print('Database connection failed!')
            print('credentials.json not found')
            exit(1)


# Sends a test query to openmrs to check that the connection worked
def test_openmrs_connection():
    get_parameters = {'limit': '100', 'startIndex': '0', 'q': 'TestConnection'}
    rest_connection.send_request('patient', get_parameters, None, connection_verified, connection_failed,
                                 connection_failed)


# This loads the observations of a given patient
def load_observations(patient_uuid):
    get_parameters = {'v': 'full', 'patient': patient_uuid, 'concept': '5088AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'}
    rest_connection.send_request('obs', get_parameters, None, on_observations_loaded, on_observations_not_loaded,
                                 on_observations_not_loaded)


# Queries for a single patient given a patient ID
def load_patient(patient_id):
    get_parameters = {'limit': '100', 'startIndex': '0', 'q': patient_id}
    rest_connection.send_request('patient', get_parameters, None, add_patient_uuid, patient_not_loaded,
                                 patient_not_loaded)


# This method adds the temperature observation to a patient in openMRS given their record (appointment)
def post_observation_to_patient(record):
    print(record)
    print(f'{record.vaccination_date}')

    post_parameters = {'person': patient_uuids[record.patient_id]['UUID'], 'obsDatetime': f'{record.vaccination_date}',
                       'concept': '5088AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
                       'value': record.patient_temperature}
    rest_connection.send_request('obs', None, post_parameters, temperature_posted, temperature_not_posted,
                                 temperature_not_posted)


# Temperature posted correctly callback
def temperature_posted(_, results):
    print('it worked, it posted')
    print('results')


# Connection to openmrs verified method.  This completes the credentials check and moves the app to the next screen
def connection_verified(_, response):
    global openmrs_disconnected
    openmrs_disconnected = False
    Clock.schedule_once(lambda dt: load_records_into_app(), 2)
    app_reference.root.transition.direction = 'left'
    app_reference.root.current = 'LoadingLogin'


# Temperature did not post correctly callback
def temperature_not_posted(_, error):
    print(dumps(error, indent=2, sort_keys=True))
    print('it didnt work')
    global openmrs_disconnected
    openmrs_disconnected = True
    on_openmrs_disconnect()


# Patient was not loaded correctly callback
def patient_not_loaded(_, response):
    print('not loaded')
    global openmrs_disconnected
    openmrs_disconnected = True
    on_openmrs_disconnect()


# Observations were not loaded correctly callback
def on_observations_not_loaded(_, error):
    global openmrs_disconnected
    openmrs_disconnected = True
    print(error)
    print('observations not loaded')


# Initial openmrs connection test failed, could be because of login credentials.
# This is a callback to a test query on openmrs
def connection_failed(_, error):
    print('Connection failed')
    # Launch window saying the connection to openmrs failed


# This method should be called after openmrs disconnects during an operation.
def on_openmrs_disconnect():
    print('openmrs disconnected error')
    app_reference.root.transition.direction = 'right'
    app_reference.root.current = 'home'
    # Show popup saying openmrs disconnected


# Patient was loaded correctly callback
# Adds a patient UUID to a dictionary of patient ids and their information.
# Also queries to load their observations to determine if they have already existing observations.
def add_patient_uuid(_, response):
    if len(response['results']) is not 0:
        global number_of_records_to_load
        number_of_records_to_load += 1
        print('in')
        print(response)
        id_and_name = response['results'][0]['display'].split(' - ')
        id = id_and_name[0]
        name = id_and_name[1]
        uuid = response['results'][0]['uuid']
        global patient_uuids
        patient_uuids[id] = {'Name': name, 'UUID': uuid}
        print(name + ";;")
        load_observations(uuid)
    else:
        print('unmatched')


# Observations for a patient loaded callback
# Adds their observations to the existing observations list and confirms that the query came back
def on_observations_loaded(_, response):
    print(dumps(response, indent=4, sort_keys=True))
    print('got to on observations loaded')
    if len(response) is not 0:
        for result in response['results']:
            existing_observations.append(result)

    global number_of_records_loaded
    number_of_records_loaded += 1
    loading_bar_increment()
    if number_of_records_loaded is number_of_records_to_load:
        sort_records()
        populate_data_preview_screen(app_reference.root)


# Determines which records are records to import and which records are unmatched records
def sort_records():
    app_reference.root.get_screen(
        'LoadingLogin').ids.current_action_loading_login.text = 'Sorting records'
    to_remove_from_unmatched = []
    to_remove_from_import = []

    # Goes through each patient finding the latest temperature observation that is currently in openmrs
    # If this observation is before one of the possible unmatched records, that record is added to the import records list
    # (As long as that patient exists in openmrs)
    for patient_id in patient_uuids:
        print(patient_id)
        observations_of_this_patient = []
        for observation in existing_observations:
            if observation['person']['display'].split(' - ')[0] == patient_id:
                observations_of_this_patient.append(observation)
        if len(observations_of_this_patient) is not 0:
            latest_observation = None
            for observation in observations_of_this_patient:
                if latest_observation is not None:
                    if datetime.strptime(observation['obsDatetime'][:len(observation['obsDatetime']) - 5],
                                         '%Y-%m-%dT%H:%M:%S.%f') > latest_observation:
                        latest_observation = datetime.strptime(
                            observation['obsDatetime'][:len(observation['obsDatetime']) - 5], '%Y-%m-%dT%H:%M:%S.%f')
                else:
                    latest_observation = datetime.strptime(
                        observation['obsDatetime'][:len(observation['obsDatetime']) - 5], '%Y-%m-%dT%H:%M:%S.%f')
            for unmatched_record in unmatched_records:
                if unmatched_record.vaccination_date > latest_observation:
                    if unmatched_record.patient_id == patient_id:
                        import_records.append(unmatched_record)

    loading_bar_increment()

    # For each patient, only their latest record from within import records is kept.  The rest are removed.
    for patient in patient_uuids:
        record_with_latest_vaccination_date = None
        for record in import_records:
            if patient == record.patient_id:
                if record_with_latest_vaccination_date is not None:
                    if record.vaccination_date < record_with_latest_vaccination_date.vaccination_date:
                        to_remove_from_import.append(record)
                    else:
                        to_remove_from_import.append(record_with_latest_vaccination_date)
                        record_with_latest_vaccination_date = record
                else:
                    record_with_latest_vaccination_date = record
    for record in to_remove_from_import:
        import_records.remove(record)

    # All records that are matched with a patient in openmrs are removed from unmatched_records
    for record in unmatched_records:
        for patient_id in patient_uuids:
            if patient_id == record.patient_id:
                to_remove_from_unmatched.append(record)
    for record in to_remove_from_unmatched:
        if record in unmatched_records:
            unmatched_records.remove(record)
    loading_bar_increment()


# Returns false if something goes wrong while trying to connect to OpenMRS server
def connect_to_openmrs(openmrs_host, openmrs_port, openmrs_user, openmrs_password):
    global rest_connection
    try:
        rest_connection = RESTConnection(openmrs_host, openmrs_port, openmrs_user, openmrs_password)
        return True
    except NameError:
        return False


# Returns false if something goes wrong while connecting to the sql databsae
def connect_to_sql(self):
    try:
        url = RecordDatabase.construct_mysql_url(self.host, self.port, self.database_name, self.user, self.password)
        record_database = RecordDatabase(url)
        record_database.ensure_tables_exist()
        global session
        session = record_database.create_session()
        return True
    except DatabaseError:
        print('database error')
        return False
    except NameError:
        print('name error')
        return False
    except ValueError:
        print('SQL connection value error')
        return False


# Returns false if one of the databases fails to connect
def connect_to_databases(self):
    if connect_to_sql(self) and connect_to_openmrs(self.openmrs_host, self.openmrs_port, self.openmrs_user,
                                                   self.openmrs_password):
        return True
    else:
        return False


# Increments the loading bar a small amount
def loading_bar_increment():
    app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value += \
        (100 - app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value) / 4


# This method imports the 'records to import' into open_mrs
def import_data_into_openmrs():
    print('ok')
    for record in import_records:
        print(record)
        post_observation_to_patient(record)


# This method loads all needed records from openMRS into the app
def load_records_into_app():
    global session
    people_lots = session.query(PeopleLots)
    app_reference.root.get_screen('LoadingLogin').ids.current_action_loading_login.text = 'Loading records from OpenMRS'
    for appointment in people_lots:
        if openmrs_disconnected is False:
            unmatched_records.append(appointment)
            load_patient(appointment.patient_id)
        else:
            on_openmrs_disconnect()
            break


# Populates the data preview screen with the import and unmatched records
def populate_data_preview_screen(root):
    app_reference.root.get_screen(
        'LoadingLogin').ids.current_action_loading_login.text = 'Populating unmatched records into data preview screen'
    path_to_scrollview_left = root.get_screen('DataPreview').ids.scrollview_left
    path_to_scrollview_right = root.get_screen('DataPreview').ids.scrollview_right
    global unmatched_records
    print('unmatched records below')
    print(len(unmatched_records))
    loading_bar_increment()

    # Displaying unmatched records
    for record in unmatched_records:
        date_as_string = f'{record.vaccination_date}'
        split_date = date_as_string.split(' ')[0]
        date = f'\nVaccination Date: {split_date}'
        path_to_scrollview_left.add_widget(
            MDLabel(
                text=f'\nVaccination Record\nPatient ID: {record.patient_id} \nTemperature Taken During Vaccination: {record.patient_temperature}{date}\n-----------------\n',
                halign="center", )
        )

    # Displaying records to import
    app_reference.root.get_screen(
        'LoadingLogin').ids.current_action_loading_login.text = 'Populating records to import into data preview screen'
    for record in import_records:
        date_as_string = f'{record.vaccination_date}'
        split_date = date_as_string.split(' ')[0]
        date = f'\nVaccination Date: {split_date}'
        path_to_scrollview_right.add_widget(
            MDLabel(
                text=f'\nVaccination Record\nPatient ID: {record.patient_id} \nTemperature taken during vaccination: {record.patient_temperature}{date}\n-----------------\n',
                halign="center", )
        )
    app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value = 100
    root.current = 'DataPreview'
    root.transition.direction = 'left'


# Global variables:

global database
global session
global rest_connection
# Assuming only one app runs at once so we can make a static reference to the app
global app_reference

number_of_records_to_load = 0
number_of_records_loaded = 0
patient_uuids = {}
unmatched_records = []
import_records = []
existing_observations = []
openmrs_disconnected = False

if __name__ == '__main__':
    app = Health_departmentApp()
    app.run()
