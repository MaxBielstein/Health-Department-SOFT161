import sqlalchemy
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


class HomeScreen(Screen):
    pass


class Health_departmentApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"

        inspector.create_inspector(Window, self)  # For inspection (press control-e to toggle).
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))

        return sm


def connect_to_sql():
    try:
        url = RecordDatabase.construct_mysql_url(host, 3303, database_name, user, password)
        record_database = RecordDatabase(url)
        record_database.ensure_tables_exist()
        global session
        session = record_database.create_session()
    except DatabaseError:
        pass
        # Database connection error


def get_all_people_lots():
    vaccination_appointments = session.query(PeopleLots)
    return vaccination_appointments


def load_credentials_file():
    try:
        with open('credentials.json', 'r') as credentials_file:
            credentials = json.load(credentials_file)
            global host
            global database_name
            global user
            global password
            host = credentials['host']
            database_name = credentials['database']
            user = credentials['username']
            password = credentials['password']
    except FileNotFoundError:
        # Replace this with error prompt in app
        print('Database connection failed!')
        print('credentials.json not found')
        exit(1)


# Global variables:
global host
global database_name
global user
global password
global database
global session

if __name__ == '__main__':
    app = Health_departmentApp()
    app.run()
    load_credentials_file()
    connect_to_sql()
