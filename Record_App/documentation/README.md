# Vaccination Record App

Vaccination record application is an application that records a vaccination of a given person.  The application has the capability of creating and storing different people, different vaccine lots, and different vaccine records, within an SQL database.

# Information
This application keeps track of each vaccine that a person gets, with that there are a few of assumptions.  
1. Each person will only get a single vaccine from each vaccine lot. 
2. Each person that uses this application will have a unique name.   
3. The vaccination will take place between years 1000 and 3000.

The application enforces all of these assumptions.
## Dependencies

You must have a MariaDB MySQL server version 10.1 or later installed and running on your machine with the ability to access it via a terminal.  

You must have PyCharm installed on your machine.
You must have python 3.6 installed on your machine.

## Installation

1. Open terminal and log into your database and then input the following command
```create database records```
2. Open up PyCharm
3. Open the milestone_1 folder in PyCharm
4. Right click installer.py and click run, this will create the tables for the database as well as populate them with some default values

## Usage

1. Open up PyCharm
2. Open the milestone_1 folder in PyCharm
3. Right click main.py and click run

From here you can create a new person to register to the database or create a new vaccination record to register to the database.  You can also add new vaccine lots into the database from the new vaccination screen.  Everything else should be rather intuitive so further instruction should not be required.

The only unintuitive thing to note is that in the 'create new lot' screen the vaccine dropdown includes the id of the vaccine in front of its associated disease in order to make the dropdown more readable.

## Status

This application is currently finished with full functionality.
#### Known Issues
There are a few warnings in the console when the application through an IDE but they do not seem to affect the functionality of the application.
#### Known bugs
There are currently no known bugs.
# Author
Max Bielstein
