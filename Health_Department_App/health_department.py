from json import dumps

import sqlalchemy
from kivy import Config
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '1200')
Config.set('graphics', 'minimum_width', '800')
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


class Health_departmentApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        load_credentials_file()
        connect_to_databases()

    def build(self):
        self.theme_cls.primary_palette = "Blue"

        inspector.create_inspector(Window, self)  # For inspection (press control-e to toggle).
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))

        return sm


def connect_to_sql():
    try:
        url = RecordDatabase.construct_mysql_url(host, 3306, database_name, user, password)
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
    rest_connection.send_request('patient', get_parameters, None, on_visits_loaded, on_visits_not_loaded,
                                 on_visits_not_loaded)


def on_visits_loaded(_, response):
    print(dumps(response, indent=4, sort_keys=True))


def on_visits_not_loaded(_, error):
    pass


def connect_to_openmrs():
    global rest_connection
    rest_connection = RESTConnection('localhost', 8080, 'admin', 'Admin123')


def get_all_people_lots():
    vaccination_appointments = session.query(PeopleLots)
    return vaccination_appointments


def load_credentials_file():
    global host
    global database_name
    global user
    global password
    try:
        with open('credentials.json', 'r') as credentials_file:
            credentials = json.load(credentials_file)
            host = credentials['host']
            database_name = credentials['database']
            user = credentials['username']
            password = credentials['password']
    except FileNotFoundError:
        # Replace this with error prompt in app
        print('Database connection failed!')
        print('credentials.json not found')
        exit(1)


def connect_to_databases():
    connect_to_sql()
    connect_to_openmrs()
    # TODO move to proper place, this is here for testing
    load_visits()
    load_patient('1000HU')


# Global variables:
global host
global database_name
global user
global password
global database
global session
global rest_connection

if __name__ == '__main__':
    app = Health_departmentApp()
    app.run()
