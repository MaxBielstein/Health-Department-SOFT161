# soft161-Group-Capstone

This is for the SOFT161 capstone project at the University of Nebraska-Lincoln for Taylor Runge, Nick Colleran, Max Bielstein, and Ethan Rasgorshek.

## Important Note

This project uses aditional widgets from KivyMD and as such requires that anyone working on or viewing the project run the following command in a directory above the project's scope
	
	pip install kivymd

If you would like to learn more about KivyMD you can refer to the documentation here https://kivymd.readthedocs.io/en/latest/

One important thing to note when reviewing the Kivy for the project is that MDSpinner is different from the kivy spinner. The MDSpinner is a status indicator that we use in the Health Department app as opposed to the normal kivy spinner which is a dropdown menu. Other things to note is that some kivy widgets have different names due to the project using the KivyMD counterpart.

## Health Department App
The health department app is used to import data from the database that the mobile apps use into OpenMRS.
It is also used for viewing certain data that is within the database such as symptomatic patients.
#### Termonology
###### Record:
A record of a patient's vaccination including their temperature and the date of vaccination pulled from the SQL database.
###### Observation: 
An observation containing some form of data from OpenMRS. (You can put records into these)
###### Record to import: 
The newest record for a certain patient, which is newer than any observation within OpenMRS containing the same data as the record for the same certain patient. See Notes 1.
###### Unmatched Record: 
Any record that has no matching patient ID in OpenMRS.
#### Login Screen
In this screen you will need to put in the credentials to both an OpenMRS database, which is running locally on your device, and for a MySQL server which you have currently running.  After you enter your credentials you can simply login by clicking the login button.  The program will then attempt to connect to both OpenMRS and the MySQL database.  If the app is successful you will be moved to the Data Preview screen.
#### Data Preview Screen
This screen shows you the unmatched records as well as the records to import.  To reload this screen you will need to login again.  Once you are ready to import, simply click the import button and the application will import the records to import into the local OpenMRS server.
#### Importing Screen
This screen will show you the status of the records that it is currently importing, if any are importing.  Once the records are done importing there will be a label saying that the importing has finished and you will be able to access the rest of the app. See Notes 2.

#### 
#### Notes
1. In the case that you want to import all records newer than the last observation for that patient, you can simply delete the remove_past_records_from_import_list() method call from inside of the sort_records() method.  We have that method because that is how we interpreted the specification for this app. However as noted, this is an easy fix if you would like all of the records newer than the last observation. This process for determining records to import keeps records that are already in OpenMRS from being imported again.
2. In the original specification it was required for the app to " display a success message and allow the user to close the application.", in which the message is the label showing the status of the import (should be finished) and the option to close is simply the X on the top right of the application window.
