from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.properties import NumericProperty, StringProperty
from kivymd.app import MDApp
import mysql.connector


import json


# Loads the credentials to connect to the database
from kivymd.uix.label import MDLabel

from database import RecordDatabase, PeopleLots, Lots, People

try:
    with open('credentials.json', 'r') as credentials_file:
        credentials = json.load(credentials_file)
        host = credentials['host']
        database_name = credentials['database']
        user = credentials['username']
        password = credentials['password']
except FileNotFoundError:
    print('Database connection failed!')
    print('credentials.json not found')
    exit(1)

# Global variable for the mysql url
url = RecordDatabase.construct_mysql_url(host, 3306, database_name, user, password)
database = RecordDatabase(url)
session = database.create_session()


class VaccineRecordApp(MDApp):
    new_person_patient_id = StringProperty()
    new_person_name = StringProperty()
    new_person_birthdate_year = NumericProperty()
    new_person_birthdate_month = NumericProperty()
    new_person_birthdate_day = NumericProperty()
    new_lot_lot_id = NumericProperty()
    new_lot_manufacture_date_year = NumericProperty()
    new_lot_manufacture_date_day = NumericProperty()
    new_lot_manufacture_date_month = NumericProperty()
    new_vaccination_name = StringProperty()
    new_vaccination_temperature = NumericProperty()
    new_vaccination_date_month = NumericProperty()
    new_vaccination_date_year = NumericProperty()
    new_vaccination_date_day = NumericProperty()

    input_error_message = StringProperty('')

    update_person_prompt_open = False
    update_person_result = False

    # This method changes the screen to a certain screen
    # taking in the screen of choice and setting the transition
    # to move left.
    # This is currently only used for confirm screens
    def confirm_screen(self, confirm_screen):
        self.root.current = confirm_screen
        self.root.transition.direction = 'left'

    def clear_new_person_screen(self):
        id_path = self.root.ids
        id_path.name_entry_new_person.text = ''
        id_path.patient_id_entry_new_person.text = ''
        id_path.day_entry_new_person.text = ''
        id_path.year_entry_new_person.text = ''
        id_path.month_entry_new_person.text = ''

    def clear_new_lot_screen(self):
        id_path = self.root.ids
        id_path.lot_dropdown.text = str(id_path.lot_id_entry_new_lot.text)
        id_path.lot_id_entry_new_lot.text = ''
        id_path.day_entry_new_lot.text = ''
        id_path.year_entry_new_lot.text = ''
        id_path.month_entry_new_lot.text = ''
        list_of_vaccines = []
        for vaccine in get_sql_data('vaccines', 'vaccine_id'):
            list_of_vaccines.append(str(vaccine))
        list_of_vaccines.sort()
        list_of_vaccines_with_disease = []
        for vaccine in list_of_vaccines:
            list_of_vaccines_with_disease.append(
                vaccine + ' ' + get_specific_sql_data('vaccines', 'relevant_disease', 'vaccine_id', vaccine)[0])
        self.root.ids.new_lot_vaccine_dropdown.values = list_of_vaccines_with_disease
        self.root.ids.new_lot_vaccine_dropdown.text = 'Select an existing vaccine'

    def clear_new_vaccination_screen(self):
        id_path = self.root.ids
        id_path.name_input_new_vaccination.text = ''
        id_path.temperature_input_new_vaccination.text = ''
        id_path.day_entry_new_vaccination.text = str(datetime.now().day)
        id_path.year_entry_new_vaccination.text = str(datetime.now().year)
        id_path.month_entry_new_vaccination.text = str(datetime.now().month)
        self.set_up_lots_spinner()

    # This runs when a new lot is created
    def lot_confirmed(self):
        self.root.ids.lot_dropdown.text = str(self.root.ids.lot_id_entry_new_lot.text)

    def fill_in_person_name_new_vaccination(self):
        self.root.ids.name_input_new_vaccination.text = self.root.ids.name_entry_new_person.text

    def create_vaccination_record(self):
        id_path = self.root.ids
        self.new_vaccination_name = id_path.name_input_new_vaccination.text
        if id_path.temperature_input_new_vaccination.text is not '':
            self.new_vaccination_temperature = id_path.temperature_input_new_vaccination.text
        if id_path.day_entry_new_vaccination.text is not '':
            self.new_vaccination_date_day = id_path.day_entry_new_vaccination.text
        if id_path.month_entry_new_vaccination.text is not '':
            self.new_vaccination_date_month = id_path.month_entry_new_vaccination.text
        if id_path.year_entry_new_vaccination.text is not '':
            self.new_vaccination_date_year = id_path.year_entry_new_vaccination.text

        if self.check_for_required_inputs_new_vaccination():
            new_vaccination_record(self, int(str(id_path.lot_dropdown.text)), self.new_vaccination_name, self.new_vaccination_temperature,
                                   self.new_vaccination_date_month, self.new_vaccination_date_day,
                                   self.new_vaccination_date_year)

    def check_for_required_inputs_new_vaccination(self):
        if self.new_vaccination_name is '':
            self.input_error_message = 'Name field must be filled'
            Factory.NewInputError().open()
            return False
        elif self.new_vaccination_temperature is '':
            self.input_error_message = 'Temperature field must be filled'
            Factory.NewInputError().open()
            return False
        elif self.new_vaccination_date_month < 1 or self.new_vaccination_date_month > 12 or self.new_vaccination_date_day < 1 \
                or self.new_vaccination_date_day > 31 or self.new_vaccination_date_year > 9999 or self.new_vaccination_date_year < 1000:
            self.input_error_message = 'Vaccination date fields must be filled in format MMDDYYYY'
            Factory.NewInputError().open()
            return False
        elif 'Select Lot' in self.root.ids.lot_dropdown.text:
            self.input_error_message = 'You must select an existing lot'
            Factory.NewInputError().open()
            return False
        elif len(get_specific_sql_data('people', 'patient_id', 'name', self.new_vaccination_name)) is 0:
            self.input_error_message = 'This person does not exist in the database'
            Factory.NewInputError().open()
            return False
        try:
            datetime(month=int(self.new_vaccination_date_month), year=int(self.new_vaccination_date_year),
                     day=int(self.new_vaccination_date_day))
        except ValueError:
            self.input_error_message = 'Vaccination date fields must have a valid date'
            Factory.NewInputError().open()
            return False
        return True

    def create_new_person(self):
        id_path = self.root.ids
        if id_path.patient_id_entry_new_person.text is not '':
            self.new_person_patient_id = id_path.patient_id_entry_new_person.text
        else:
            self.new_person_patient_id = ''
        self.new_person_name = id_path.name_entry_new_person.text
        if id_path.day_entry_new_person.text is not '':
            self.new_person_birthdate_day = int(id_path.day_entry_new_person.text)
        if id_path.month_entry_new_person.text is not '':
            self.new_person_birthdate_month = int(id_path.month_entry_new_person.text)
        if id_path.year_entry_new_person.text is not '':
            self.new_person_birthdate_year = int(id_path.year_entry_new_person.text)
        if self.check_for_required_inputs_new_person():
            new_person(self, self.new_person_name, self.new_person_patient_id, self.new_person_birthdate_month,
                       self.new_person_birthdate_day, self.new_person_birthdate_year)

    def check_for_required_inputs_new_person(self):
        if self.new_person_name is '':
            self.input_error_message = 'Name field must be filled'
            Factory.NewInputError().open()
            return False
        elif self.new_person_name in get_sql_data('people', 'name'):
            self.input_error_message = 'Patient with this name already exists'
            Factory.NewInputError().open()
            return False
        elif self.root.ids.patient_id_entry_new_person.text is '0':
            self.input_error_message = 'ID cannot be 0'
            Factory.NewInputError().open()
            return False
        elif self.new_person_patient_id is '0':
            self.input_error_message = 'Patient ID field must be filled'
            Factory.NewInputError().open()
            return False
        elif self.new_person_birthdate_month < 1 or self.new_person_birthdate_month > 12 or self.new_person_birthdate_day < 1 \
                or self.new_person_birthdate_day > 31 or self.new_person_birthdate_year > 9999 or self.new_person_birthdate_year < 1000:
            self.input_error_message = 'Patient birthdate fields must be filled in format MMDDYYYY'
            Factory.NewInputError().open()
            return False
        try:
            datetime(month=self.new_person_birthdate_month, year=self.new_person_birthdate_year,
                     day=self.new_person_birthdate_day)
        except ValueError:
            self.input_error_message = 'Patient birthdate fields must have a valid date'
            Factory.NewInputError().open()
            return False
        return True

    def create_new_lot(self):
        id_path = self.root.ids
        if id_path.lot_id_entry_new_lot.text is not '':
            self.new_lot_lot_id = id_path.lot_id_entry_new_lot.text
        else:
            self.new_lot_lot_id = 0
        if id_path.month_entry_new_lot.text is not '':
            self.new_lot_manufacture_date_month = int(id_path.month_entry_new_lot.text)
        if id_path.year_entry_new_lot.text is not '':
            self.new_lot_manufacture_date_year = int(id_path.year_entry_new_lot.text)
        if id_path.day_entry_new_lot.text is not '':
            self.new_lot_manufacture_date_day = int(id_path.day_entry_new_lot.text)
        if self.check_for_required_inputs_new_lot():
            vaccine_dropdown_split = id_path.new_lot_vaccine_dropdown.text.split(' ')
            id_of_vaccine = int(vaccine_dropdown_split[0])
            new_lot(self, id_of_vaccine, self.new_lot_lot_id,
                    self.new_lot_manufacture_date_month, self.new_lot_manufacture_date_day,
                    self.new_lot_manufacture_date_year)

    def check_for_required_inputs_new_lot(self):
        if self.root.ids.lot_id_entry_new_lot.text is '0':
            self.input_error_message = 'Lot ID field cannot be 0'
            Factory.NewInputError().open()
            return False
        elif self.new_lot_lot_id is 0:
            self.input_error_message = 'Lot ID field must be filled'
            Factory.NewInputError().open()
            return False
        elif self.new_lot_manufacture_date_month < 1 or self.new_lot_manufacture_date_month > 12 or self.new_lot_manufacture_date_day < 1 \
                or self.new_lot_manufacture_date_day > 31 or self.new_lot_manufacture_date_year > 9999 or self.new_lot_manufacture_date_year < 1000:
            self.input_error_message = 'Manufacture date fields must be filled in format MMDDYYYY'
            Factory.NewInputError().open()
            return False
        elif 'Select an existing vaccine' in self.root.ids.new_lot_vaccine_dropdown.text:
            self.input_error_message = 'You must select an existing vaccine'
            Factory.NewInputError().open()
            return False
        try:
            datetime(month=self.new_lot_manufacture_date_month, year=self.new_lot_manufacture_date_year,
                     day=self.new_lot_manufacture_date_day)
        except ValueError:
            self.input_error_message = 'Manufacture date fields must have a valid date'
            Factory.NewInputError().open()
            return False
        return True

    def set_up_lots_spinner(self):
        if self.root.current is 'new_vaccination':
            spinner_path = self.root.ids.lot_dropdown
        else:
            spinner_path = self.root.ids.lot_dropdown_flag
        list_of_lots = []
        for lot in get_sql_data('lots', 'lot_id'):
            list_of_lots.append(str(lot))
        list_of_lots.sort()
        spinner_path.values = list_of_lots
        spinner_path.text = 'Select Lot'

    def update_person(self):
        update_person_static(self)

    def check_for_patient_id(self):
        if self.root.ids.patient_id_review_vaccinations.text == '':
            self.input_error_message = 'Please enter a patient id.'
            Factory.NewInputError().open()
            return False
        return True

    def get_vaccination_record(self, patient_id):
        if self.check_for_patient_id():
            people_lots = session.query(PeopleLots).filter(PeopleLots.patient_id == patient_id).all()
            path_to_scrollview = self.root.ids.scrollview_review_vaccinations
            for people_lot in people_lots:
                lot_id = people_lot.lot_id
                lot = session.query(Lots).filter(Lots.lot_id == lot_id).one()
                vaccination_date = people_lot.vaccination_date
                vaccine_type = get_specific_sql_data('vaccines', 'relevant_disease', 'vaccine_id', lot.vaccine_id)[0]
                path_to_scrollview.add_widget(
                    MDLabel(
                        text=f'Vaccine Type: {vaccine_type}; Lot: {lot_id}; Vaccination Date: {vaccination_date}',
                        halign='center', height=50
                    ))
            self.root.current = 'review_vaccinations_continued'
            self.root.transition.direction = 'left'

    def clear_vaccination_records(self):
        self.root.ids.scrollview_review_vaccinations.clear_widgets()
        self.root.ids.patient_id_review_vaccinations.text = ''

    def new_vaccination_from_review(self):
        name = get_specific_sql_data('people', 'name', 'patient_id', self.root.ids.patient_id_review_vaccinations.text)[0]
        self.root.ids.name_input_new_vaccination.text = name

    def flag_vaccine_lot(self, selected_lot):
        self.root.ids.scrollview_flag_vaccine_lot.clear_widgets()
        people = session.query(PeopleLots).filter(PeopleLots.lot_id == selected_lot).all()
        for person in people:
            patient_id = person.patient_id
            name = get_specific_sql_data('people', 'name', 'patient_id', patient_id)[0]
            self.root.ids.scrollview_flag_vaccine_lot.add_widget(
                MDLabel(
                    text=name, font_size=35, halign='center', height=50
                )
            )
        

# These methods below where made static so that tests could but run on them
# with a different sql database
# They all attempt to input some type of data into the database
def update_person_static(self):
    name = self.new_person_name
    birthdate_month = self.new_person_birthdate_month
    birthdate_day = self.new_person_birthdate_day
    birthdate_year = self.new_person_birthdate_year
    birthdate = datetime(year=birthdate_year, month=birthdate_month, day=birthdate_day)
    person, mysql_session = get_person_data(self.new_person_patient_id, session)
    person.name = name
    person.birthdate = birthdate
    self.confirm_screen('person_updated')
    session.commit()


def new_vaccination_record(self, lot_id, name, temperature, vaccine_month, vaccine_day, vaccine_year):
    vaccination_date = datetime(year=int(vaccine_year), day=int(vaccine_day), month=int(vaccine_month))
    patient_id = get_specific_sql_data('people', 'patient_id', 'name', name)[0]
    record = PeopleLots(vaccination_date=vaccination_date, lot_id=lot_id, patient_id=patient_id, patient_temperature=temperature)
    if record.lot_id not in get_specific_sql_data('people_lots', 'lot_id', 'patient_id', record.patient_id):
        sql_input(record, session)
        self.confirm_screen('new_vaccination_confirmed')
    else:
        self.input_error_message = 'This person already has this vaccine!'
        Factory.NewInputError().open()


def new_lot(self, vaccine_id, lot_id, manufacture_month, manufacture_day, manufacture_year):
    manufacture_date = datetime(year=manufacture_year, day=manufacture_day, month=manufacture_month)
    lot = Lots(vaccine_id=vaccine_id, lot_id=lot_id, manufacture_date=manufacture_date)
    if int(lot.lot_id) not in get_sql_data('lots', 'lot_id'):
        sql_input(lot, session)
        self.root.current = 'new_vaccination'
        self.root.transition.direction = 'right'
        self.set_up_lots_spinner()
    else:
        self.input_error_message = 'Lot with this lot id already exists!'
        Factory.NewInputError().open()


def new_person(self, name, patient_id, birthdate_month, birthdate_day, birthdate_year):
    birthdate = datetime(year=birthdate_year, month=birthdate_month, day=birthdate_day)
    person = People(name=name, patient_id=patient_id, birthdate=birthdate)
    list_of_ids = []
    for patient in get_sql_data('people', 'patient_id'):
        list_of_ids.append(str(patient))
    if person.patient_id not in list_of_ids:
        sql_input(person, session)
        self.confirm_screen('new_person_confirmed')
    else:
        Factory.MatchingIDError().open()


# Some background information on the two below methods: I started figuring out how to query sql before I saw the post on piazza.
# So I did it the way I found to do it online where you simply run an actual sql command
# to the database using mysqlconnector. Same thing for the other non-sqlalchemy query method below.

# These methods below query data from the database and return the specified data


# if column name is None then it returns the whole table
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


# This returns a People object associated with the parameter patient_id as well as the session to commit the data
def get_person_data(patient_id, session):
    person_data = session.query(People).filter(People.patient_id == patient_id).one()
    return person_data, session


# This is a simple method for adding data to the sql database
def sql_input(data, session):
    session.add(data)
    session.commit()


if __name__ == '__main__':
    app = VaccineRecordApp()
    app.run()
