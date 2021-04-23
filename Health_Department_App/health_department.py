from json import dumps

import sqlalchemy
from kivy import Config

Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '1000')
Config.set('graphics', 'minimum_width', '1200')

Config.set('graphics', 'minimum_height', '1000')

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
        connect_to_databases(self)

    def build(self):
        self.theme_cls.primary_palette = "Blue"

        inspector.create_inspector(Window, self)  # For inspection (press control-e to toggle).
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(LoadingLogin(name='LoadingLogin'))
        sm.add_widget(DataPreview(name='DataPreview'))

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
        path = self.root.get_screen('home').ids

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


def load_visits():
    get_parameters = {'v': 'full'}
    rest_connection.send_request('visit', get_parameters, None, on_visits_loaded, on_visits_not_loaded,
                                 on_visits_not_loaded)


def load_patient(patient_id):
    get_parameters = {'limit': '100', 'startIndex': '0', 'q': patient_id}
    rest_connection.send_request('patient', get_parameters, None, add_patient_uuid, patient_not_loaded,
                                 patient_not_loaded)


def load_patient_ids_from_database():
    global session
    people = session.query(People)
    patient_ids = []
    for person in people:
        patient_ids.append(person.patient_id)

    load_patient_uuids_from_openmrs(patient_ids)


def load_patient_uuids_from_openmrs(patient_ids):
    for patient_id in patient_ids:
        load_patient(patient_id)


def add_patient_uuid(_, response):
    if len(response['results']) is not 0:
        print('in')
        print(response)
        id_and_name = response['results'][0]['display'].split(' - ')
        id = id_and_name[0]
        name = id_and_name[1]
        uuid = response['results'][0]['uuid']
        global patient_uuids
        patient_uuids[id] = {'Name': name, 'UUID': uuid}
        print(patient_uuids)


def patient_not_loaded(_, response):
    print('not loaded')


def on_visits_loaded(_, response):
    print(dumps(response, indent=4, sort_keys=True))


def on_visits_not_loaded(_, error):
    pass


def connect_to_openmrs(openmrs_host, openmrs_port, openmrs_user, openmrs_password):
    global rest_connection
    rest_connection = RESTConnection(openmrs_host, openmrs_port, openmrs_user, openmrs_password)


def get_all_people_lots():
    vaccination_appointments = session.query(PeopleLots)
    return vaccination_appointments


def connect_to_databases(self):
    connect_to_sql(self)
    connect_to_openmrs(self.openmrs_host, self.openmrs_port, self.openmrs_user, self.openmrs_password)
    # TODO move to proper place, this is here for testing
    load_visits()
    load_patient_ids_from_database()


# Global variables:

global database
global session
global rest_connection
patient_uuids = {}

if __name__ == '__main__':
    app = Health_departmentApp()
    app.run()
