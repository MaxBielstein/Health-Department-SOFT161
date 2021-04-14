from datetime import datetime
from sys import stderr

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Persisted = declarative_base()  # pylint: disable=invalid-name


class RecordDatabase(object):
    @staticmethod
    def construct_mysql_url(authority, port, database, vaccinename, password):
        return f'mysql+mysqlconnector://{vaccinename}:{password}@{authority}:{port}/{database}'

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


class VaccinationClinics(Persisted):
    __tablename__ = 'vaccination_clinics'
    clinic_id = Column(Integer, primary_key=True)
    clinic_name = Column(String(256), nullable=False)
    clinic_address = Column(String(256), nullable=False)
    manufacturer_id = Column(Integer, ForeignKey('manufacturers.manufacturer_id', ondelete='CASCADE'), nullable=False)
    manufacturer_clinics = relationship('ManufacturerClinics', uselist=True, back_populates='vaccination_clinic')
    orders = relationship('Orders', uselist=True, back_populates='vaccination_clinic')
    manufacturers = relationship('Manufacturers', uselist=True, secondary='manufacturer_clinics',
                                 back_populates='vaccination_clinics')


class ManufacturerClinics(Persisted):
    __tablename__ = 'manufacturer_clinics'
    manufacturer_id = Column(Integer, ForeignKey('manufacturers.manufacturer_id', ondelete='CASCADE'), primary_key=True)
    clinic_id = Column(Integer, ForeignKey('vaccination_clinics.clinic_id', ondelete='CASCADE'), primary_key=True)
    vaccination_clinic = relationship('VaccinationClinics', back_populates='manufacturer_clinics')
    manufacturer = relationship('Manufacturers', back_populates='manufacturer_clinics')


class Orders(Persisted):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True)
    manufacturer_id = Column(Integer, ForeignKey('manufacturers.manufacturer_id', ondelete='CASCADE'),
                             primary_key=False, nullable=False)
    clinic_id = Column(Integer, ForeignKey('vaccination_clinics.clinic_id', ondelete='CASCADE'), primary_key=False,
                       nullable=False)
    vaccine_id = Column(Integer, ForeignKey('vaccines.vaccine_id', ondelete='CASCADE'), primary_key=False,
                        nullable=False)
    vaccine = relationship('Vaccines', back_populates='orders')
    vaccination_clinic = relationship('VaccinationClinics', back_populates='orders')
    manufacturer = relationship('Manufacturers', back_populates='orders')


class Manufacturers(Persisted):
    __tablename__ = 'manufacturers'
    manufacturer_id = Column(Integer, primary_key=True)
    manufacturer_location = Column(String(256), nullable=False)
    manufacturer_name = Column(String(256), nullable=False)
    manufacturer_clinics = relationship('ManufacturerClinics', uselist=True, back_populates='manufacturer')
    orders = relationship('Orders', uselist=True, back_populates='manufacturer')
    vaccination_clinics = relationship('VaccinationClinics', uselist=True, secondary='manufacturer_clinics',
                                       back_populates='manufacturers')
    vaccines = relationship('Vaccines', uselist=True, back_populates='manufacturer')


class Vaccines(Persisted):
    __tablename__ = 'vaccines'
    vaccine_id = Column(Integer, primary_key=True)
    required_doses = Column(Integer, nullable=False)
    relevant_disease = Column(String(256))
    vaccine_name = Column(String(256), nullable=False)
    manufacturer_id = Column(Integer, ForeignKey('manufacturers.manufacturer_id', ondelete='CASCADE'), nullable=False)
    lots = relationship('Lots', uselist=True, back_populates='vaccine')
    manufacturer = relationship('Manufacturers', back_populates='vaccines')
    orders = relationship('Orders', back_populates='vaccine')


class Lots(Persisted):
    __tablename__ = 'lots'
    lot_id = Column(Integer, primary_key=True)
    vaccine_id = Column(Integer, ForeignKey('vaccines.vaccine_id', ondelete='CASCADE'), nullable=False)
    manufacture_date = Column(DateTime, nullable=False)
    vaccine = relationship('Vaccines', back_populates='lots')
    people_lots = relationship('PeopleLots', uselist=True, back_populates='lot')
    people = relationship('People', uselist=True, secondary='people_lots', back_populates='lots')


class People(Persisted):
    __tablename__ = 'people'
    patient_id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    birthdate = Column(DateTime)
    people_lots = relationship('PeopleLots', uselist=True, back_populates='person')
    lots = relationship('Lots', uselist=True, secondary='people_lots', back_populates='people')


class PeopleLots(Persisted):
    __tablename__ = 'people_lots'
    lot_id = Column(Integer, ForeignKey('lots.lot_id', ondelete='CASCADE'), primary_key=True)
    patient_id = Column(Integer, ForeignKey('people.patient_id', ondelete='CASCADE'), primary_key=True)
    vaccination_date = Column(DateTime)
    lot = relationship('Lots', back_populates='people_lots')
    person = relationship('People', back_populates='people_lots')


def add_starter_data(session_to_add_to):
    manufacturer1 = Manufacturers(manufacturer_id=1, manufacturer_name='manufacturer 1',
                                  manufacturer_location='Nebraska')
    manufacturer2 = Manufacturers(manufacturer_id=2, manufacturer_name='manufacturer 2',
                                  manufacturer_location='Colorado')
    manufacturer3 = Manufacturers(manufacturer_id=3, manufacturer_name='manufacturer 3',
                                  manufacturer_location='California')
    vaccination_clinic1 = VaccinationClinics(manufacturer_id=1, clinic_name='UNL Vaccination Clinic',
                                             clinic_address='123 UNL street',
                                             manufacturer_clinics=[ManufacturerClinics(manufacturer=manufacturer1),
                                                                   ManufacturerClinics(manufacturer=manufacturer2)])

    lot122_date = datetime(year=1999, month=1, day=1)
    kevin_birthdate = datetime(year=1980, month=1, day=1)
    kevin_vaccination_date = datetime(year=1990, month=6, day=1)
    walter_first_vaccination_date = datetime(year=1990, month=1, day=13)
    bob_first_vaccination_date = datetime(year=1990, month=1, day=11)
    lot123_date = datetime(year=1999, month=4, day=1)
    lot124_date = datetime(year=1999, month=4, day=2)
    lot125_date = datetime(year=1990, month=5, day=22)
    walter_second_vaccination_date = datetime(year=1999, month=5, day=2)
    birthdate_bob = datetime(year=1990, month=1, day=1)
    birthdate_walter = datetime(year=1993, month=2, day=2)
    covid19_vaccine = Vaccines(relevant_disease='Covid', required_doses=2, vaccine_name='covid19 vaccine',
                               manufacturer=manufacturer1)
    measles_vaccine = Vaccines(relevant_disease='Measles', required_doses=1, vaccine_name='measles vaccine',
                               manufacturer=manufacturer2)
    smallpox_vaccine = Vaccines(relevant_disease='Smallpox', required_doses=1, vaccine_name='smallpox vaccine',
                                manufacturer=manufacturer3)
    walter = People(name='Walter', patient_id=1, birthdate=birthdate_walter)
    kevin = People(name='kevin', patient_id=3, birthdate=kevin_birthdate)
    bob = People(name='Bob', patient_id=2, birthdate=birthdate_bob)
    lot122 = Lots(vaccine=covid19_vaccine,
                  people_lots=[PeopleLots(person=walter, vaccination_date=walter_first_vaccination_date)],
                  lot_id=122, manufacture_date=lot122_date)
    lot123 = Lots(vaccine=covid19_vaccine,
                  people_lots=[PeopleLots(person=walter, vaccination_date=walter_second_vaccination_date),
                               PeopleLots(person=bob, vaccination_date=bob_first_vaccination_date)], lot_id=123,
                  manufacture_date=lot123_date)
    lot124 = Lots(vaccine=measles_vaccine,
                  people_lots=[PeopleLots(person=bob, vaccination_date=bob_first_vaccination_date)], lot_id=124,
                  manufacture_date=lot124_date)
    lot125 = Lots(vaccine=smallpox_vaccine,
                  people_lots=[PeopleLots(person=kevin, vaccination_date=kevin_vaccination_date)], lot_id=125,
                  manufacture_date=lot125_date)
    order1 = Orders(manufacturer=manufacturer1, vaccination_clinic=vaccination_clinic1, vaccine=covid19_vaccine)
    session_to_add_to.add(lot122)
    session_to_add_to.add(lot123)
    session_to_add_to.add(lot124)
    session_to_add_to.add(lot125)
    session_to_add_to.add(vaccination_clinic1)
    session_to_add_to.add(order1)


if __name__ == '__main__':
    try:
        url = RecordDatabase.construct_mysql_url('localhost', 3306, 'combined', 'root', 'cse1208')
        record_database = RecordDatabase(url)
        record_database.ensure_tables_exist()
        session = record_database.create_session()
        add_starter_data(session)
        session.commit()
        print('Tables created and populated')
    except SQLAlchemyError as exception:
        print('Database setup failed!', file=stderr)
        print(f'Cause: {exception}', file=stderr)
        exit(1)
