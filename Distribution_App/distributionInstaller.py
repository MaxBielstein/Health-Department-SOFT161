from sys import stderr

from sqlalchemy.exc import SQLAlchemyError

from distribution import DistributionDatabase, Manufacturer, vaccination_clinics


def add_starter_data(session):
    manufacturer1 = Manufacturer(name='manufacturer 1', location='Nebraska')
    manufacturer2 = Manufacturer(name='manufacturer 2', location='Colorado')
    manufacturer3 = Manufacturer(name='manufacturer 3', location='California')
    session.add(manufacturer1)
    session.add(manufacturer2)
    session.add(manufacturer3)
    clinic1 = vaccination_clinics(name='clinic 1', address='Nebraska')
    clinic2 = vaccination_clinics(name='clinic 2', address='Colorado')
    clinic3 = vaccination_clinics(name='clinic 3', address='California')
    session.add(clinic1)
    session.add(clinic2)
    session.add(clinic3)


def main():
    try:
        url = DistributionDatabase.construct_mysql_url('localhost', 3306, 'combined', 'root', 'cse1208')
        distribution_database = DistributionDatabase(url)

        distribution_database.ensure_tables_exist()
        print('Tables created.')
        session = distribution_database.create_session()
        add_starter_data(session)
        session.commit()
        print('Records created.')
    except SQLAlchemyError as exception:
        print('Database setup failed!', file=stderr)
        print(f'Cause: {exception}', file=stderr)
        exit(1)


if __name__ == '__main__':
    main()
