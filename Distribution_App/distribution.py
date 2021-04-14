from kivy.app import App
from kivymd.app import MDApp
from kivy.core.window import Window  # For inspection.
from kivy.modules import inspector  # For inspection.
from kivy.uix.screenmanager import ScreenManager, Screen
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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


class Clinic(Persisted):
    __tablename__ = 'Clinics'
    name = Column(String(256), nullable=False)
    address = Column(String(256), nullable=False)
    clinic_id = Column(Integer, primary_key=True)
    manufacturer_id = Column(Integer, ForeignKey('Manufacturers.manufacturer_id'))


class Manufacturer(Persisted):
    __tablename__ = 'Manufacturers'
    manufacturer_id = Column(Integer, primary_key=True)
    location = Column(String(256), nullable=False)
    name = Column(String(256), nullable=False)


class Vaccine(Persisted):
    __tablename__ = 'Vaccines'
    vaccine_id = Column(Integer, primary_key=True)
    doses = Column(Integer, nullable=False)
    name = Column(String(256), nullable=False)
    disease = Column(String(256), nullable=False)
    manufacturer_id = Column(Integer, ForeignKey('Manufacturers.manufacturer_id'))


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


# These methods below query data from the database and return the specified data

# if column name is None then it returns the whole table
def get_sql_data(table_name, column_name):
    database = mysql.connector.connect(host='localhost', database='milestone_one', user='root', password='cse1208')
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
    database = mysql.connector.connect(host='localhost', database='milestone_one', user='root', password='cse1208')
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
    url = DistributionDatabase.construct_mysql_url('localhost', 3306, 'milestone_one', 'root', 'cse1208')
    record_database = DistributionDatabase(url)
    session = record_database.create_session()
    session.add(data)
    session.commit()


if __name__ == '__main__':
    app = DistributionApp()
    app.run()
