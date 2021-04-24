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
    OLD_RECORD = 'OLD_RECORD'
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
        self.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value = 1

    def clear_data_preview_screen(self):
        global number_of_records_to_load
        global number_of_records_loaded
        global patient_uuids
        global unmatched_records
        global old_records
        global location_to_import_records
        global records_to_import
        number_of_records_to_load = 0
        number_of_records_loaded = 0
        patient_uuids = {}
        unmatched_records = []
        old_records = []
        location_to_import_records = []
        records_to_import = []
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


# Queries for all visits of a certain patient given their UUID
def load_visits(patient_uuid):
    get_parameters = {'v': 'full', 'patient': patient_uuid}
    rest_connection.send_request('visit', get_parameters, None, on_visits_loaded, on_visits_not_loaded,
                                 on_visits_not_loaded)


# Queries for a single patient given a patient ID
def load_patient(patient_id):
    get_parameters = {'limit': '100', 'startIndex': '0', 'q': patient_id}
    rest_connection.send_request('patient', get_parameters, None, add_patient_uuid, patient_not_loaded,
                                 patient_not_loaded)


# *INCOMPLETE* Posts a patient's given temperature record to one of their given visits
def post_temperature_to_visit(visit, record):
    print(dumps(visit, indent=2, sort_keys=True))
    print(record)
    encounterProvider = {
        "provider": "bb1a7781-7896-40be-aaca-7d1b41d843a6",
        "encounterRole": "240b26f9-dd88-4172-823d-4a8bfeb7841f"
    }
    post_parameters = {'encounterDatetime': f'{record.vaccination_date}', 'patient': visit['patient']['uuid'],
                       'encounterType': '67a71486-1a54-468f-ac3e-7091a9a79584', 'location': visit['location']['uuid'],
                       'visit': visit['uuid'], 'encounterProviders': [encounterProvider]}
    rest_connection.send_request('encounter', None, post_parameters, temperature_posted, temperature_not_posted,
                                 temperature_not_posted)


# Temperature posted correctly callback
def temperature_posted(_, results):
    print('it worked, it posted')
    print('results')


def connection_verified(_, response):
    global openmrs_disconnected
    openmrs_disconnected = False
    loading_bar = app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar
    Clock.schedule_once(lambda dt: load_records_into_app(loading_bar), 2)
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


# Patient's visits were not loaded correctly callback
def on_visits_not_loaded(_, error):
    print(error)
    global openmrs_disconnected
    openmrs_disconnected = True
    on_openmrs_disconnect()


def connection_failed(_, error):
    print('Connection failed')
    # Launch window saying the connection to openmrs failed


def on_openmrs_disconnect():
    print('openmrs disconnected error')
    app_reference.root.transition.direction = 'right'
    app_reference.root.current = 'home'
    # Show popup saying openmrs disconnected

# Patient was loaded correctly callback
# Adds a patient UUID to a dictionary of patient ids and their information.
# Also queries to load their visits to determine if they have records that need to be imported.
# If the patient was loaded correctly, but there doesn't not exist a patient with that ID, the method that counts to make sure all
# patient callbacks came through is called to insure that the app knows that this callback did come back
def add_patient_uuid(_, response):
    if len(response['results']) is not 0:
        print('in')
        print(response)
        id_and_name = response['results'][0]['display'].split(' - ')
        id = id_and_name[0]
        name = id_and_name[1]
        uuid = response['results'][0]['uuid']
        global patient_uuids
        patient_uuids[id]['Name'] = name
        patient_uuids[id]['UUID'] = uuid
        load_visits(uuid)
    else:
        print('unmatched')
        add_data_to_records(RecordType.UNMATCHED_RECORD, None)


# Visits of a patient loaded correctly callback
# Checks to see if the patient has a current visit with the latest encounter not having their temperature as an observation
# If this is the case, this visit is added to the locations in which we will later import their records into.
def on_visits_loaded(_, response):
    print(dumps(response, indent=4, sort_keys=True))
    for result in response['results']:
        if result['stopDatetime'] is None:
            if len(result['encounters']) is not 0:
                if len(result['encounters']) is not 0:
                    if len(result['encounters'][-1]['obs']) is not 0:
                        for observation in result['encounters'][-1]['obs']:
                            if 'Temperature' in observation['display']:
                                remove_from_unmatched_records(result, False)
                                add_data_to_records(RecordType.OLD_RECORD, result)
                                print('to old records')
                                return
            remove_from_unmatched_records(result, True)
            add_data_to_records(RecordType.IMPORT_RECORD, result)
            print('to import')


# This method keeps track of all patient records that are queried for and makes sure that each one comes back.
# It also adds the data into its correct list
# It moves the loading bar up a bit when this method is called
def add_data_to_records(record_type, record):
    if record_type is RecordType.OLD_RECORD:
        old_records.append(record)
    elif record_type is RecordType.IMPORT_RECORD:
        location_to_import_records.append(record)
    global number_of_records_loaded
    global number_of_records_to_load
    number_of_records_loaded += 1
    if app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value is 0:
        app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value = 10
    else:
        app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value += \
            (100 - app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value) / 4
    if number_of_records_loaded is number_of_records_to_load:
        app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value = 100
        remove_old_import_records()
        populate_data_preview_screen(app_reference.root)


# This method removes any records which are currently in the unmatched records list which been determined to be matched
def remove_from_unmatched_records(result, to_import):
    record_to_remove = None
    for record in unmatched_records:
        print(result['patient']['display'].split(' - ')[0])
        print(record.patient_id)
        print(str(result['patient']['display'].split(' - ')[0]) in record.patient_id)
        if str(result['patient']['display'].split(' - ')[0]) in record.patient_id:
            record_to_remove = record
    if record_to_remove in unmatched_records:
        unmatched_records.remove(record_to_remove)
        if to_import:
            records_to_import.append(record_to_remove)


# THis removes old records when the sql database which have already been imported into openmrs
def remove_old_import_records():
    app_reference.root.get_screen(
        'LoadingLogin').ids.current_action_loading_login.text = 'Filtering out historical records'
    records_to_remove = []
    for record in records_to_import:
        for record2 in records_to_import:
            if record.vaccination_date < record2.vaccination_date:
                records_to_remove.append(record)
    for record in records_to_remove:
        if record in records_to_import:
            records_to_import.remove(record)


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


# *INCOMPLETE* this method imports the 'records to import' into open_mrs
def import_data_into_openmrs():
    print('ok')
    for record in records_to_import:
        print(record)
        for visit in location_to_import_records:
            print(visit)
            if visit['patient']['display'].split(' - ')[0] in record.patient_id:
                post_temperature_to_visit(visit, record)
                print('in')


# This method loads all needed records from openMRS into the app
def load_records_into_app(loading_bar):
    global session
    global number_of_records_to_load
    people_lots = session.query(PeopleLots)
    loading_bar.value = 0
    app_reference.root.get_screen('LoadingLogin').ids.current_action_loading_login.text = 'Loading records from OpenMRS'
    for appointment in people_lots:
        if openmrs_disconnected is False:
            unmatched_records.append(appointment)
            patient_uuids[appointment.patient_id] = {'latest_appointment': appointment.vaccination_date}
            number_of_records_to_load += 1
            load_patient(appointment.patient_id)
        else:
            on_openmrs_disconnect()
            break


def populate_data_preview_screen(root):
    app_reference.root.get_screen(
        'LoadingLogin').ids.current_action_loading_login.text = 'Populating unmatched records into data preview screen'
    path_to_scrollview_left = root.get_screen('DataPreview').ids.scrollview_left
    path_to_scrollview_right = root.get_screen('DataPreview').ids.scrollview_right
    global unmatched_records
    print('unmatched records below')
    print(len(unmatched_records))
    for record in unmatched_records:
        date_as_string = f'{record.vaccination_date}'
        split_date = date_as_string.split(' ')[0]
        date = f'\nVaccination Date: {split_date}'
        path_to_scrollview_left.add_widget(
            MDLabel(
                text=f'\nVaccination Record\nPatient ID: {record.patient_id} \nTemperature Taken During Vaccination: {record.patient_temperature}{date}\n-----------------\n',
                halign="center", )
        )

    app_reference.root.get_screen(
        'LoadingLogin').ids.current_action_loading_login.text = 'Populating records to import into data preview screen'
    for record in records_to_import:
        date_as_string = f'{record.vaccination_date}'
        split_date = date_as_string.split(' ')[0]
        date = f'\nVaccination Date: {split_date}'
        path_to_scrollview_right.add_widget(
            MDLabel(
                text=f'\nVaccination Record\nPatient ID: {record.patient_id} \nTemperature taken during vaccination: {record.patient_temperature}{date}\n-----------------\n',
                halign="center", )
        )
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
records_to_import = []
old_records = []
location_to_import_records = []
openmrs_disconnected = False

if __name__ == '__main__':
    app = Health_departmentApp()
    app.run()
