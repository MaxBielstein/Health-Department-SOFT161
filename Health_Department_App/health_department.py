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
        path = self.root.get_screen('home').ids
        loading_bar = self.root.get_screen('LoadingLogin').ids.loading_login_progress_bar

        self.host = path.database_host.text
        self.database_name = path.database_database.text
        self.user = path.database_username.text
        self.password = path.database_password.text
        self.port = path.database_port.text

        self.openmrs_user = path.openmrs_username.text
        self.openmrs_host = path.openmrs_host.text
        self.openmrs_port = path.openmrs_port.text
        self.openmrs_password = path.openmrs_password.text
        connect_to_databases(self)
        Clock.schedule_once(lambda dt: load_records_into_app(loading_bar), 2)

    def abort_button(self):
        global number_of_records_to_load
        global number_of_records_loaded
        global patient_uuids
        global unmatched_records
        global old_records
        global records_to_import
        number_of_records_to_load = 0
        number_of_records_loaded = 0
        patient_uuids = {}
        unmatched_records = []
        old_records = []
        records_to_import = []
        self.root.get_screen('DataPreview').ids.scrollview_left.clear_widgets()

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


def connect_to_sql(self):
    try:
        url = RecordDatabase.construct_mysql_url(self.host, self.port, self.database_name, self.user, self.password)
        record_database = RecordDatabase(url)
        record_database.ensure_tables_exist()
        global session
        session = record_database.create_session()
    except DatabaseError:
        pass
        # Database connection error


def load_visits(patient_uuid):
    get_parameters = {'v': 'full', 'patient': patient_uuid}
    rest_connection.send_request('visit', get_parameters, None, on_visits_loaded, on_visits_not_loaded,
                                 on_visits_not_loaded)


def load_patient(patient_id):
    get_parameters = {'limit': '100', 'startIndex': '0', 'q': patient_id}
    rest_connection.send_request('patient', get_parameters, None, add_patient_uuid, patient_not_loaded,
                                 patient_not_loaded)


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


def patient_not_loaded(_, response):
    print('not loaded')


def on_visits_loaded(_, response):
    print(dumps(response, indent=4, sort_keys=True))
    for result in response['results']:
        if result['stopDatetime'] is None:
            if len(result['encounters']) is not 0:
                if len(result['encounters']) is not 0:
                    if len(result['encounters'][-1]['obs']) is not 0:
                        for observation in result['encounters'][-1]['obs']:
                            if 'Temperature' in observation['display']:
                                remove_from_unmatched_records(result)
                                add_data_to_records(RecordType.OLD_RECORD, result)
                                print('to old records')
                                return
            remove_from_unmatched_records(result)
            add_data_to_records(RecordType.IMPORT_RECORD, result)
            print('to import')


def remove_from_unmatched_records(result):
    record_to_remove = None
    for record in unmatched_records:
        print(result['patient']['display'].split(' - ')[0])
        print(record.patient_id)
        print(str(result['patient']['display'].split(' - ')[0]) in record.patient_id)
        if str(result['patient']['display'].split(' - ')[0]) in record.patient_id:
            record_to_remove = record
    if record_to_remove in unmatched_records:
        unmatched_records.remove(record_to_remove)


def remove_old_records_to_import():
    records_to_remove = []
    for record in records_to_import:
        for record2 in records_to_import:
            if record['display'] is record2['display']:
                if record['startDatetime'] < record2['startDatetime']:
                    records_to_remove.append(record)
    for record in records_to_remove:
        if record in records_to_import:
            records_to_import.remove(record)


def on_visits_not_loaded(_, error):
    print(error)
    pass


def connect_to_openmrs(openmrs_host, openmrs_port, openmrs_user, openmrs_password):
    global rest_connection
    rest_connection = RESTConnection(openmrs_host, openmrs_port, openmrs_user, openmrs_password)


def connect_to_databases(self):
    connect_to_sql(self)
    connect_to_openmrs(self.openmrs_host, self.openmrs_port, self.openmrs_user, self.openmrs_password)


def update_records():
    print('ran')
    print(len(patient_uuids))
    for id in patient_uuids:
        print('loading')
        load_visits(patient_uuids[id]['UUID'])


def load_records_into_app(loading_bar):
    global session
    people_lots = session.query(PeopleLots)
    global number_of_records_to_load
    loading_bar.value = 0
    for appointment in people_lots:
        unmatched_records.append(appointment)
        patient_uuids[appointment.patient_id] = {'latest_appointment': appointment.vaccination_date}
        number_of_records_to_load += 1
        load_patient(appointment.patient_id)


def add_data_to_records(record_type, record):
    if record_type is RecordType.OLD_RECORD:
        old_records.append(record)
    elif record_type is RecordType.IMPORT_RECORD:
        records_to_import.append(record)
    global number_of_records_loaded
    global number_of_records_to_load
    number_of_records_loaded += 1
    if number_of_records_loaded is number_of_records_to_load:
        populate_data_preview_screen(app_reference.root)
        if app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value is 0:
            app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value = 10
        else:
            app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value += (
                                                                                                          100 - app_reference.root.get_screen(
                                                                                                      'LoadingLogin').ids.loading_login_progress_bar.value) / 4


def populate_data_preview_screen(root):
    path_to_scrollview_left = root.get_screen('DataPreview').ids.scrollview_left
    global unmatched_records
    print('unmatched records below')
    print(len(unmatched_records))
    for record in unmatched_records:
        date_as_string = f'{record.vaccination_date}'
        split_date = date_as_string.split(' ')[0]
        date = f'\nVaccination Date: {split_date}'
        path_to_scrollview_left.add_widget(
            MDLabel(
                text=f'\nVaccination Record\nPatient ID: {record.patient_id} \nVaccine Lot: {record.lot_id}\n Vaccine: {record.lot.vaccine.vaccine_name}{date}',
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
old_records = []
records_to_import = []

if __name__ == '__main__':
    app = Health_departmentApp()
    app.run()
