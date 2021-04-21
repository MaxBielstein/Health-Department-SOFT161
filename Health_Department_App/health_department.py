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

if __name__ == '__main__':
    app = Health_departmentApp()
    app.run()
    load_credentials_file()
