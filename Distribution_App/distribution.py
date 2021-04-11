from kivy.app import App
from kivy.core.window import Window  # For inspection.
from kivy.modules import inspector  # For inspection.
from kivy.uix.screenmanager import ScreenManager, Screen
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class ClinicScreen(Screen):
    pass


class ManufacturerForVaccine(Screen):
    pass


class ClinicScreen0(Screen):
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


class DistributionApp(App):

    def build(self):
        inspector.create_inspector(Window, self)  # For inspection (press control-e to toggle).
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ClinicScreen(name='clinic'))
        sm.add_widget(NewVaccineScreen(name='new_vaccine'))
        sm.add_widget(ManufacturerForVaccine(name='m_for_vaccine'))
        sm.add_widget(ClinicScreen0(name='clinic_0'))
        sm.add_widget(OrderVaccineScreen(name='order_vaccine'))
        sm.add_widget(OrderManufacturer(name='m_for_order'))
        sm.add_widget(SelectManufacturerForClinic(name='m_for_clinic'))

        return sm







if __name__ == '__main__':
    app = DistributionApp()
    app.run()
