# Adding Annotations to the Database

To add new layers of annotations to the database, you need to follow the following steps.


### (1) Design new Table

Most of the time, it is recommended to store new annotations in a seperate table. To do so, define table name and columns.

### (2) Define Type of Table

DataJoint has four different data tiers (manual, imported, lookup and computed). Choose one of them for the new table.

### (3) Initialize Table

To initialize the table, implement as a new class in the _db_setup.py_ file.

### (4) Define how Table will be Populated

In case the table is a computed or imported table, you need a _make_ function to populate it. It's recommended to design and test this function independently from the database and add it to the _db_setup.py_ file when finished.

### (5) Populate Table

