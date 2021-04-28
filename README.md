# soft161-Group-Capstone

This is for the SOFT161 capstone project at the University of Nebraska-Lincoln for Taylor Runge, Nick Colleran, Max Bielstein, and Ethan Rasgorshek.

## Important Note

This project uses additional widgets from KivyMD and as such requires that anyone working on or viewing the project run the following command in a directory above the project's scope
    
    pip install kivymd

If you would like to learn more about KivyMD you can refer to the documentation here https://kivymd.readthedocs.io/en/latest/

One important thing to note when reviewing the Kivy for the project is that MDSpinner is different from the kivy spinner. The MDSpinner is a status indicator that we use in the Health Department app as opposed to the normal kivy spinner which is a dropdown menu. Another thing to note is that some kivy widgets have different names due to the project using the KivyMD counterpart.

## Distribution App
The distribution app is a mobile app that handles the creation and interactions of clinics, vaccines, and orders.
It is also used for fulfilling orders.
#### Functionality
###### Adding and editing clinics
By pressing "Add/Edit Vaccination Clinics" a user can either choose an existing clinic from the database or add a new clinic to the database. From there, a user can view all of the associated manufacturers, and all of the non-associated manufacturers. The user may then select to add or remove manufacturers from the selected clinic, then go back to the home screen.
###### Adding vaccines
By pressing "New Vaccine" a user can enter a new vaccine into the database. They first select a manufacturer, then enter a name, ID, and number of required doses. Finally, they select a disease from the hard-coded list of diseases, then they can add the vaccine to the database. 
###### Placing orders
By selecting "New Order", the user is presented with three spinners that have logic to make sure they are selected in the proper order. These spinners prompt for a clinic, manufacturer, and disease. They dynamically update based on the selections made on the other spinners. After these are filled, the code will automatically assign a vaccine. The user then enters the number of required doses and assigns an order ID. From there, the user can place the order. 
###### Reviewing orders
By selecting "Review Orders", the user can view the details of an order, and choose to mark it as fulfilled. The user can filter orders by clinics or manufacturers, then select an order. After selecting an order, the user is presented with all the needed information about the order, and given the option to fulfill it and return to the home screen, go back to select another order, or just return to the home screen. 
## Record App
The vaccination record app is a mobile app that can register patients, vaccination records, and vaccine lots into the database.
#### Functionality
Ability to create patients to put into the database.  Takes inputs: Name, Patient ID, Birthdate.
Ability to update patients already in the database. 
Ability to create vaccination lots to put into the database. Takes inputes: Vaccine, Lot ID, Manufacture Date.
Ability to create vaccination records (Instances of a vaccination for a given patient).  Takes inputes: Lot ID, Name, Patient Temperature, Vaccination Date.
Ability to review all vaccinations of a given patient.  Takes inputes: Patient ID.
Ability to review which patients have gotten a vaccine from a certain lot.  Takes inputs: Lot ID.
## Health Department App
The health department app is a desktop app used to import data from the database that the mobile apps use into OpenMRS.
It is also used for viewing certain data that is within the database such as symptomatic patients.
#### Terminology
###### Record:
A record of a patient's vaccination including their temperature and the date of vaccination pulled from the SQL database.
###### Observation: 
An observation containing some form of data from OpenMRS. (You can put records into these)
###### Record to import: 
The newest record for a certain patient, which is newer than any observation within OpenMRS containing the same data as the record for the same certain patient. See Notes 1.
###### Unmatched Record: 
Any record that has no matching patient ID in OpenMRS.
#### Login Screen
In this screen, you will need to put in the credentials to both an OpenMRS database, which is running locally on your device, and for a MySQL server that you have currently running.  After you enter your credentials you can simply log in by clicking the login button.  The program will then attempt to connect to both OpenMRS and the MySQL database.  If the app is successful you will be moved to the Data Preview screen.
#### Data Preview Screen
This screen shows you the unmatched records as well as the records to import.  To reload this screen you will need to log in again.  Once you are ready to import, simply click the import button and the application will import the records to import into the local OpenMRS server.
#### Importing Screen
This screen will show you the status of the records that it is currently importing if any are importing.  Once the records are done importing there will be a label saying that the importing has finished and you will be able to access the rest of the app. See Notes 2.

#### 
#### Notes
1. In the case that you want to import all records newer than the last observation for that patient, you can simply delete the remove_past_records_from_import_list() method call from inside of the sort_records() method.  We have that method because that is how we interpreted the specification for this app. However, as noted, this is an easy fix if you would like all of the records newer than the last observation. This process for determining records to import keeps records that are already in OpenMRS from being imported again.
2. In the original specification it was required for the app to " display a success message and allow the user to close the application.", in which the message is the label showing the status of the import (should be finished) and the option to close is simply the X on the top right of the application window.
