import enum
from json import dumps
from kivy import Config
from kivy.uix.popup import Popup

Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '1000')
Config.set('graphics', 'minimum_width', '1200')
Config.set('graphics', 'minimum_height', '1000')

from kivy.factory import Factory
from kivy.clock import Clock
from kivymd.uix.label import MDLabel
from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivy.core.window import Window  # For inspection.
from kivy.modules import inspector  # For inspection.
from kivy.uix.screenmanager import ScreenManager, Screen
from sqlalchemy.exc import DatabaseError
from database import *
from openmrs import RESTConnection


class HomeScreen(Screen):
    pass


class LoadingLogin(Screen):
    pass


class DataPreview(Screen):
    pass


class ImportingLoading(Screen):
    pass


class SymptomaticPatients(Screen):
    pass


class VaccinationRate(Screen):
    pass


class VaccineOrderSummary(Screen):
    pass


class RecordType(enum.Enum):
    OTHER_RECORD = 'OTHER_RECORD'
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

    input_error_message = StringProperty()

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
        sm.add_widget(SymptomaticPatients(name='SymptomaticPatients'))
        sm.add_widget(VaccinationRate(name='VaccinationRate'))
        sm.add_widget(VaccineOrderSummary(name='VaccineOrderSummary'))

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
        if self.load_login_credentials():
            if connect_to_databases(self):
                test_openmrs_connection()

    def load_login_credentials(self):
        try:
            path = self.root.get_screen('home').ids
            self.host = path.database_host.text
            self.database_name = path.database_database.text
            self.user = path.database_username.text
            self.password = path.database_password.text

            self.port = path.database_port.text

            self.openmrs_port = path.openmrs_port.text

            self.openmrs_user = path.openmrs_username.text
            self.openmrs_host = path.openmrs_host.text
            self.openmrs_password = path.openmrs_password.text
            return True
        except FileNotFoundError:
            self.input_error_message = 'SQL database not connected.  Credentials may be incorrect'
            Factory.NewInputError().open()
            return False

    def load_vaccines_for_selected_disease(self):
        disease_spinner = self.root.get_screen('VaccinationRate').ids.select_disease_vaccination_rate
        vaccine_spinner = self.root.get_screen('VaccinationRate').ids.select_vaccine_vaccination_rate
        self.root.get_screen("VaccinationRate").ids.people_vaccinated_label.text = '0'
        self.root.get_screen("VaccinationRate").ids.people_not_vaccinated_label.text = '0'
        global loading_vaccines_active
        loading_vaccines_active = True
        try:
            vaccine_query = session.query(Vaccines).filter(Vaccines.relevant_disease == disease_spinner.text)
            values = list()
            if disease_spinner.text is not 'Select a Disease':
                if len(vaccine_query.all()) > 0:
                    for vaccine in vaccine_query.all():
                        values.append(vaccine.vaccine_name)
                    vaccine_spinner.values = values
                    vaccine_spinner.text = 'Select a Vaccine'
                    loading_vaccines_active = False
                else:
                    vaccine_spinner.text = 'No Vaccines for\nSelected Disease'
                    loading_vaccines_active = False
            else:
                self.input_error_message = 'You must select a disease to see\nassociated diseases.'
                Factory.NewInputError().open()
        except Exception:
            app_reference.input_error_message = 'SQL database disconnection error loading vaccines. \nThe database may no longer be connected. \nPlease restart the app to try again'
            Factory.NewInputError().open()

    def load_vaccines_for_the_disease(self):
        try:
            if loading_vaccines_active is False:
                vaccine_spinner = self.root.get_screen('VaccinationRate').ids.select_vaccine_vaccination_rate
                if vaccine_spinner.text is not "Select a Vaccine" and vaccine_spinner.text is not "Not available":
                    all_people = session.query(People).all()
                    all_people_set = set(all_people)
                    all_people_with_vaccine_for_disease = set()
                    people_lots = session.query(PeopleLots).all()
                    people_with_this_vaccine_for_disease = set()
                    for person_lot in people_lots:
                        if person_lot.lot.vaccine.vaccine_name == vaccine_spinner.text:
                            people_with_this_vaccine_for_disease.add(person_lot.person)
                    all_people_with_vaccine_for_disease = all_people_with_vaccine_for_disease.union(
                        people_with_this_vaccine_for_disease)
                    self.root.get_screen("VaccinationRate").ids.people_vaccinated_label.text = str(
                        len(all_people_with_vaccine_for_disease))
                    self.root.get_screen("VaccinationRate").ids.people_not_vaccinated_label.text = str(
                        len(all_people_set - all_people_with_vaccine_for_disease))
        except Exception:
            app_reference.input_error_message = 'SQL database disconnection error loading number of vaccinated patients. \nThe database may no longer be connected. \nPlease restart the app to try again'
            Factory.NewInputError().open()

    def load_symptomatic_patients_screen(self):
        try:
            appointments = session.query(PeopleLots).all()
            print('OKAY OKAY OKAT')
            list_of_ids = []
            # Creates a list of patients (their ids) in the database
            for appointment in appointments:
                if appointment.patient_id not in list_of_ids:
                    list_of_ids.append(appointment.patient_id)
            # Goes through each patient and removes their not current records from the list of appointments
            for id in list_of_ids:
                latest_record = None
                records_to_remove = []
                for appointment in appointments:
                    print(appointment.patient_id)
                    print(id)
                    print(appointment.patient_id == id)
                    if appointment.patient_id == id:
                        if latest_record is not None:
                            if latest_record.vaccination_date > appointment.vaccination_date:
                                records_to_remove.append(appointment)
                            else:
                                records_to_remove.append(latest_record)
                                latest_record = appointment
                        else:
                            latest_record = appointment
                for appointment in records_to_remove:
                    if appointment in appointments:
                        print('Patient VISIT')
                        print(appointment.patient_id)
                        appointments.remove(appointment)
            # Goes through the list of appointments (Newest one per person) and checks if they have a fever
            # If they do have a fever, a label for them is added
            for record in appointments:
                if record.patient_temperature is not None:
                    if record.patient_temperature >= 38:
                        date_as_string = f'{record.vaccination_date}'
                        split_date = date_as_string.split(' ')[0]
                        date = f'\nVaccination Date: {split_date}'
                        self.root.get_screen("SymptomaticPatients").ids.scrollview_symptomatic_patients.add_widget(
                            MDLabel(
                                text=f'\nSymptomatic Patient\nPatient ID: {record.patient_id} \nTemperature taken during vaccination: {record.patient_temperature}{date}\n-----------------\n',
                                halign="center", ))
        except Exception:
            app_reference.input_error_message = 'SQL database disconnection error loading symptomatic patients. \nThe database may no longer be connected. \nPlease restart the app to try again'
            Factory.NewInputError().open()

    def load_order_screen(self):
        try:
            vaccines = session.query(Vaccines).all()
            diseases = set()
            for vaccine in vaccines:
                diseases.add(vaccine.relevant_disease)
            self.root.get_screen("VaccineOrderSummary").ids.select_vaccine_vaccine_order_summary.values = diseases
        except Exception:
            app_reference.input_error_message = 'SQL database disconnection error loading orders into app. \nThe database may no longer be connected. \nPlease restart the app to try again'
            Factory.NewInputError().open()

    def load_orders_placed(self):
        print('called HERE')
        self.root.get_screen("VaccineOrderSummary").ids.scrollview_vaccine_order_summary.clear_widgets()
        if self.root.get_screen(
                "VaccineOrderSummary").ids.select_vaccine_vaccine_order_summary.text is not 'Select a Disease':
            disease = self.root.get_screen("VaccineOrderSummary").ids.select_vaccine_vaccine_order_summary.text
            total_orders_with_disease = []
            vaccines = set()
            try:
                total_orders = session.query(Orders).all()
                for order in total_orders:
                    if order.vaccine.relevant_disease == disease:
                        total_orders_with_disease.append(order)

                for order in total_orders_with_disease:
                    vaccines.add(order.vaccine)

                if len(vaccines) is not 0:
                    for vaccine in vaccines:
                        orders_for_this_vaccine_filled = []
                        total_orders_for_this_vaccine = []
                        for order in total_orders_with_disease:
                            if order.vaccine == vaccine:
                                total_orders_for_this_vaccine.append(order)
                                if order.order_fulfilled == "True":
                                    orders_for_this_vaccine_filled.append(order)
                        self.root.get_screen("VaccineOrderSummary").ids.scrollview_vaccine_order_summary.add_widget(
                            MDLabel(
                                text=f'\nVaccine: {vaccine.vaccine_name}\nOrders fulfilled: {len(orders_for_this_vaccine_filled)}/{len(total_orders_for_this_vaccine)}\n-----------------\n',
                                halign="center", )
                        )
                else:
                    self.root.get_screen("VaccineOrderSummary").ids.scrollview_vaccine_order_summary.add_widget(MDLabel(
                        text=f'\nNo Orders Exist For Vaccines Associated With This Disease\n-----------------\n',
                        halign="center", )
                    )
            except Exception:
                app_reference.input_error_message = 'SQL database disconnection error loading orders placed. \nThe database may no longer be connected. \nPlease restart the app to try again'
                Factory.NewInputError().open()

    def clear_data_preview_screen(self):
        global number_of_records_to_load
        global number_of_records_loaded
        global patient_uuids
        global unmatched_records
        global other_records
        global location_to_import_records
        global import_records
        global existing_observations
        global openmrs_disconnected
        global concepts
        number_of_records_to_load = 0
        number_of_records_loaded = 0
        patient_uuids = {}
        unmatched_records = []
        import_records = []
        existing_observations = []
        location_to_import_records = []
        openmrs_disconnected = False
        concepts = []
        self.root.get_screen('DataPreview').ids.scrollview_left.clear_widgets()
        self.root.get_screen('DataPreview').ids.scrollview_right.clear_widgets()

    def import_button(self):
        Clock.schedule_once(lambda dt: import_data_into_openmrs(), .5)
        app_reference.root.get_screen('ImportingLoading').ids.importing_spinner.active = True

    # Clears a given screen that you are changing from
    def change_screen(self, from_screen):
        if from_screen == 'SymptomaticPatients':
            self.root.get_screen(from_screen).ids.scrollview_symptomatic_patients.clear_widgets()
        elif from_screen == 'ImportingLoading':
            self.clear_data_preview_screen()
            self.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value = 0
        elif from_screen == 'VaccineOrderSummary':
            print(' VACCINE ORDER SUM')
            self.root.get_screen(from_screen).ids.select_vaccine_vaccine_order_summary.text = 'Select a Disease'
            self.root.get_screen(from_screen).ids.scrollview_vaccine_order_summary.clear_widgets()
        elif from_screen == 'DataPreview':
            self.clear_data_preview_screen()
        elif from_screen == 'VaccinationRate':
            self.root.get_screen("VaccinationRate").ids.people_vaccinated_label.text = '0'
            self.root.get_screen("VaccinationRate").ids.people_not_vaccinated_label.text = '0'
            self.root.get_screen('VaccinationRate').ids.select_vaccine_vaccination_rate.values = []
            global loading_vaccines_active
            loading_vaccines_active = True
            self.root.get_screen('VaccinationRate').ids.select_vaccine_vaccination_rate.text = 'Not available'
            loading_vaccines_active = False
            self.root.get_screen('VaccinationRate').ids.select_disease_vaccination_rate.text = 'Select a Disease'

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


# This method gets called once all records are done importing in order to allow access to the rest of the app
def importing_done():
    app_reference.root.get_screen('ImportingLoading').ids.loading_importing_progress_bar.value = 100
    app_reference.root.get_screen('ImportingLoading').ids.importing_spinner.active = False
    app_reference.root.get_screen('ImportingLoading').ids.back_to_login_button.disabled = False
    app_reference.root.get_screen('ImportingLoading').ids.view_symptomatic_patients_button.disabled = False
    app_reference.root.get_screen('ImportingLoading').ids.view_vaccination_rate_button.disabled = False
    app_reference.root.get_screen('ImportingLoading').ids.view_vaccine_order_summary_button.disabled = False


# Sends a test query to openmrs to check that the connection worked
def test_openmrs_connection():
    get_parameters = {'limit': '100', 'startIndex': '0', 'q': 'TestConnection'}
    rest_connection.send_request('patient', get_parameters, None, connection_verified, connection_failed,
                                 connection_failed)


# This loads the observations of a given patient
def load_observations(patient_uuid):
    get_parameters = {'v': 'full', 'patient': patient_uuid, 'concept': '5088AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'}
    rest_connection.send_request('obs', get_parameters, None, on_observations_loaded, on_observations_not_loaded,
                                 on_observations_not_loaded)


# Queries for a single patient given a patient ID
def load_patient(patient_id):
    get_parameters = {'limit': '100', 'startIndex': '0', 'q': patient_id}
    rest_connection.send_request('patient', get_parameters, None, add_patient_uuid, patient_not_loaded,
                                 patient_not_loaded)


# This method adds the temperature observation to a patient in openMRS given their record (appointment)
def post_observation_to_patient(record):
    print(record)
    print(f'{record.vaccination_date}')

    post_parameters = {'person': patient_uuids[record.patient_id]['UUID'], 'obsDatetime': f'{record.vaccination_date}',
                       'concept': '5088AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
                       'value': record.patient_temperature}
    rest_connection.send_request('obs', None, post_parameters, temperature_posted, temperature_not_posted,
                                 temperature_not_posted)


# Connection to openmrs verified method.  This completes the credentials check and moves the app to the next screen
def connection_verified(_, response):
    global openmrs_disconnected
    openmrs_disconnected = False
    Clock.schedule_once(lambda dt: load_records_into_app(), .5)
    app_reference.root.transition.direction = 'left'
    app_reference.root.current = 'LoadingLogin'


# Temperature did not post correctly callback
def temperature_not_posted(_, error):
    print(dumps(error, indent=2, sort_keys=True))
    print('it didnt work')
    global openmrs_disconnected
    openmrs_disconnected = True
    on_openmrs_disconnect()


# Patient was not loaded correctly callback
def patient_not_loaded(_, response):
    print('not loaded')
    global openmrs_disconnected
    openmrs_disconnected = True
    on_openmrs_disconnect()


# Observations were not loaded correctly callback
def on_observations_not_loaded(_, error):
    global openmrs_disconnected
    openmrs_disconnected = True
    print(error)
    print('observations not loaded')


# Initial openmrs connection test failed, could be because of login credentials.
# This is a callback to a test query on openmrs
def connection_failed(_, error):
    print('Connection failed')
    app_reference.input_error_message = 'Open MRS connection failed, credentials may be incorrect'
    Factory.NewInputError().open()


# This method should be called after openmrs disconnects during an operation.
def on_openmrs_disconnect():
    print('openmrs disconnected error')
    app_reference.input_error_message = 'Open MRS seems to have disconnected, please lot in again'
    Factory.NewInputError().open()
    app_reference.root.transition.direction = 'right'
    app_reference.root.current = 'home'
    app_reference.clear_data_preview_screen()


# Temperature posted correctly callback
def temperature_posted(_, results):
    loading_bar_import_increment()
    global number_of_records_imported
    number_of_records_imported += 1
    if number_of_records_imported >= number_of_records_to_import:
        app_reference.root.get_screen('ImportingLoading').ids.loading_importing_progress_bar.value = 100
        app_reference.root.get_screen('ImportingLoading').ids.importing_spinner.active = False
        importing_done()
        app_reference.root.get_screen(
            'ImportingLoading').ids.current_action_loading_importing.text = f'{number_of_records_imported}/{number_of_records_to_import} records imported into OpenMRS.  Importing Finished'
    print('it worked, it posted')
    print('results')


# Patient was loaded correctly callback
# Adds a patient UUID to a dictionary of patient ids and their information.
# Also queries to load their observations to determine if they have already existing observations.
def add_patient_uuid(_, response):
    global number_of_records_to_load
    if len(response['results']) is not 0 and 'voided' not in response['results'][0]:
        number_of_records_to_load += 1
        print('in')
        print(response)
        id_and_name = response['results'][0]['display'].split(' - ')
        id = id_and_name[0]
        name = id_and_name[1]
        uuid = response['results'][0]['uuid']
        global patient_uuids
        patient_uuids[id] = {'Name': name, 'UUID': uuid}
        print(name + ";;")
        load_observations(uuid)
    else:
        global number_of_patients_loaded
        number_of_patients_loaded += 1
        print('unmatched')
        print(f'{number_of_patients_loaded} | {number_of_patients_to_load}')
        print(f'{number_of_records_loaded} | {number_of_records_to_load}')
        if number_of_patients_loaded >= number_of_patients_to_load and number_of_records_loaded >= number_of_records_to_load:
            sort_records()
            populate_data_preview_screen(app_reference.root)


# Observations for a patient loaded callback
# Adds their observations to the existing observations list and confirms that the query came back
def on_observations_loaded(_, response):
    print(dumps(response, indent=4, sort_keys=True))
    print('got to on observations loaded')
    global number_of_records_loaded
    number_of_records_loaded += 1
    if len(response) is not 0:
        for result in response['results']:
            existing_observations.append(result)
    loading_bar_login_increment()
    print(number_of_records_loaded)
    print(number_of_records_to_load)
    if number_of_records_loaded >= number_of_records_to_load:
        sort_records()
        populate_data_preview_screen(app_reference.root)


# Determines which records are records to import and which records are unmatched records
def sort_records():
    app_reference.root.get_screen(
        'LoadingLogin').ids.current_action_loading_login.text = 'Sorting records'
    to_remove_from_unmatched = []
    to_remove_from_import = []

    # Goes through each patient finding the latest temperature observation that is currently in openmrs
    # If this observation is before one of the possible unmatched records, that record is added to the import records list
    # (As long as that patient exists in openmrs)
    check_for_existing_records_in_openmrs()
    loading_bar_login_increment()

    # For each patient, only their latest record from within import records is kept.  The rest are removed.
    remove_past_records_from_import_list(to_remove_from_import)

    # All records that are matched with a patient in openmrs are removed from unmatched_records
    remove_matched_records_from_unmatched_records(to_remove_from_unmatched)
    loading_bar_login_increment()


# Goes through each patient finding the latest temperature observation that is currently in openmrs
# If this observation is before one of the possible unmatched records, that record is added to the import records list
# (As long as that patient exists in openmrs)
def check_for_existing_records_in_openmrs():
    for patient_id in patient_uuids:
        print(patient_id)
        observations_of_this_patient = []
        for observation in existing_observations:
            if observation['person']['display'].split(' - ')[0] == patient_id:
                observations_of_this_patient.append(observation)
        if len(observations_of_this_patient) is not 0:
            latest_observation = None
            for observation in observations_of_this_patient:
                if latest_observation is not None:
                    if datetime.strptime(observation['obsDatetime'][:len(observation['obsDatetime']) - 5],
                                         '%Y-%m-%dT%H:%M:%S.%f') > latest_observation:
                        latest_observation = datetime.strptime(
                            observation['obsDatetime'][:len(observation['obsDatetime']) - 5], '%Y-%m-%dT%H:%M:%S.%f')
                else:
                    latest_observation = datetime.strptime(
                        observation['obsDatetime'][:len(observation['obsDatetime']) - 5], '%Y-%m-%dT%H:%M:%S.%f')
            for unmatched_record in unmatched_records:
                if unmatched_record.vaccination_date > latest_observation:
                    if unmatched_record.patient_id == patient_id:
                        import_records.append(unmatched_record)


# For each patient, only their latest record from within import records is kept.  The rest are removed.
def remove_past_records_from_import_list(to_remove_from_import):
    for patient in patient_uuids:
        record_with_latest_vaccination_date = None
        for record in import_records:
            if patient == record.patient_id:
                if record_with_latest_vaccination_date is not None:
                    if record.vaccination_date < record_with_latest_vaccination_date.vaccination_date:
                        to_remove_from_import.append(record)
                    else:
                        to_remove_from_import.append(record_with_latest_vaccination_date)
                        record_with_latest_vaccination_date = record
                else:
                    record_with_latest_vaccination_date = record
    for record in to_remove_from_import:
        import_records.remove(record)


# All records that are matched with a patient in openmrs are removed from unmatched_records
def remove_matched_records_from_unmatched_records(to_remove_from_unmatched):
    for record in unmatched_records:
        for patient_id in patient_uuids:
            if patient_id == record.patient_id:
                to_remove_from_unmatched.append(record)
    for record in to_remove_from_unmatched:
        if record in unmatched_records:
            unmatched_records.remove(record)


# Returns false if something goes wrong while trying to connect to OpenMRS server
def connect_to_openmrs(openmrs_host, openmrs_port, openmrs_user, openmrs_password):
    global rest_connection
    try:
        rest_connection = RESTConnection(openmrs_host, openmrs_port, openmrs_user, openmrs_password)
        return True
    except NameError:
        return False


# Returns false if something goes wrong while connecting to the sql databsae
def connect_to_sql(self):
    try:
        url = RecordDatabase.construct_mysql_url(self.host, self.port, self.database_name, self.user, self.password)
        record_database = RecordDatabase(url)
        record_database.ensure_tables_exist()
        global session
        session = record_database.create_session()
        return True
    except DatabaseError:
        print('database error')
        self.input_error_message = 'SQL did not connect, credentials may be incorrect'
        Factory.NewInputError().open()
        return False
    except NameError:
        print('name error')
        self.input_error_message = 'SQL did not connect, credentials may be incorrect'
        Factory.NewInputError().open()
        return False
    except ValueError:
        print('SQL connection value error')
        self.input_error_message = 'SQL did not connect, credentials may be incorrect'
        Factory.NewInputError().open()
        return False


# Returns false if one of the databases fails to connect
def connect_to_databases(self):
    if connect_to_sql(self) and connect_to_openmrs(self.openmrs_host, self.openmrs_port, self.openmrs_user,
                                                   self.openmrs_password):
        return True
    else:
        return False


# Increments the loading bar a small amount
def loading_bar_login_increment():
    app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value += \
        (100 - app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value) / 4


def loading_bar_import_increment():
    app_reference.root.get_screen('ImportingLoading').ids.loading_importing_progress_bar.value += \
        (100 - app_reference.root.get_screen('ImportingLoading').ids.loading_importing_progress_bar.value) / 4


# This method imports the 'records to import' into open_mrs
def import_data_into_openmrs():
    print('ok')
    if len(import_records) is not 0:
        app_reference.root.get_screen(
            'ImportingLoading').ids.current_action_loading_importing.text = f'Importing {len(import_records)} records into openmrs'
        for record in import_records:
            if openmrs_disconnected is False:
                print(record)
                global number_of_records_to_import
                number_of_records_to_import += 1
                app_reference.root.get_screen(
                    'ImportingLoading').ids.current_action_loading_importing.text = f'Importing record {number_of_records_to_import}/{len(import_records)} into openmrs'
                post_observation_to_patient(record)
            else:
                on_openmrs_disconnect()
                break
    else:
        app_reference.root.get_screen(
            'ImportingLoading').ids.current_action_loading_importing.text = f'No records to import'
        importing_done()


# This method loads all needed records from openMRS into the app
def load_records_into_app():
    global session
    try:
        people_lots = session.query(PeopleLots).all()
        app_reference.root.get_screen(
            'LoadingLogin').ids.current_action_loading_login.text = 'Loading records from OpenMRS'
        for appointment in people_lots:
            print(appointment.patient_id)
            if openmrs_disconnected is False:
                unmatched_records.append(appointment)
                global number_of_patients_to_load
                number_of_patients_to_load += 1
                load_patient(appointment.patient_id)
            else:
                on_openmrs_disconnect()
                break
    except Exception:
        app_reference.input_error_message = 'SQL database disconnection error loading records into app. \nThe database may no longer be connected. \nPlease restart the app to try again'
        Factory.NewInputError().open()


# Populates the data preview screen with the import and unmatched records
def populate_data_preview_screen(root):
    app_reference.root.get_screen(
        'LoadingLogin').ids.current_action_loading_login.text = 'Populating unmatched records into data preview screen'
    path_to_scrollview_left = root.get_screen('DataPreview').ids.scrollview_left
    path_to_scrollview_right = root.get_screen('DataPreview').ids.scrollview_right
    global unmatched_records
    print('unmatched records below')
    print(len(unmatched_records))
    loading_bar_login_increment()

    # Displaying unmatched records
    for record in unmatched_records:
        date_as_string = f'{record.vaccination_date}'
        split_date = date_as_string.split(' ')[0]
        date = f'\nVaccination Date: {split_date}'
        path_to_scrollview_left.add_widget(
            MDLabel(
                text=f'\nVaccination Record\nPatient ID: {record.patient_id} \nTemperature Taken During Vaccination: {record.patient_temperature}{date}\n-----------------\n',
                halign="center", )
        )

    # Displaying records to import
    app_reference.root.get_screen(
        'LoadingLogin').ids.current_action_loading_login.text = 'Populating records to import into data preview screen'
    for record in import_records:
        date_as_string = f'{record.vaccination_date}'
        split_date = date_as_string.split(' ')[0]
        date = f'\nVaccination Date: {split_date}'
        path_to_scrollview_right.add_widget(
            MDLabel(
                text=f'\nVaccination Record\nPatient ID: {record.patient_id} \nTemperature taken during vaccination: {record.patient_temperature}{date}\n-----------------\n',
                halign="center", )
        )
    app_reference.root.get_screen('LoadingLogin').ids.loading_login_progress_bar.value = 100
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
number_of_patients_to_load = 0
number_of_patients_loaded = 0
number_of_records_imported = 0
number_of_records_to_import = 0
patient_uuids = {}
unmatched_records = []
import_records = []
existing_observations = []
openmrs_disconnected = False
loading_vaccines_active = False

if __name__ == '__main__':
    app = Health_departmentApp()
    app.run()
