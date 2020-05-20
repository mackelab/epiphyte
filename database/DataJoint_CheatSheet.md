# Data Joint in Python Cheat Sheet

### Connecting to Data Base server
First define host name, user name and password and connect to the data base (change parameters to match your data base):
```
host_name = '127.0.0.1'
user_name = 'root'
password = 'pw'
```

```
dj.config['database.host'] = host_name
dj.config['database.user'] = user_name
dj.config['database.password'] = password

dj.conn()
```

### Setting up schema(s)
You need to set up a schema to which you then add all the tables, a database (SQL: show databases). Give the schema a name to access from Python (here: schema_dhv) and a name to access from mysql (here: DeepHumanVison). You can set up several schemas if you need to / want to.

```
schema_dhv = dj.schema('DeepHumanVison', locals())
```

### Defining tables

To define a table, you need to add a class to the previously defined schema. Each defined and added class will be represented as a table.
```
@schema_dhv
class Table(dj.Manual):
    definition = """
    name: varchar(128)    # primary key
    ---
    # more variables always in the same format 'name' : 'type'
    """
```

### Instantiate the tables

```
table = Table()
```

### Inserting data to a table
Adding one row to a table; Either in form of a tuple, without column names or in form of a dictionary with column names. (here a tuple for an entry in a table with three columns)
```
table.insert1( (10, '2015-03-01', 'M'))
```

Inserting data (usually several rows)
```
table.insert(data, skip_duplicates=True)
```


### Delete / Altering a table
If you have to make changes to a previously defined class/table, you need to delete the table first.
```
table.drop()
```

### Deleting one entry from a table
```
(table & "name = 'test'").delete()
```


### Populating table
You can define a function called _make_tuples(self, key) in a class to enable populating a table from multiple files. Call the function with
```
table.populate()
```
