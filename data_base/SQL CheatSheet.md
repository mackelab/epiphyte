# MySQL Queries

## Delete

```
DELETE FROM <table_name> WHERE <condition>;
```
```
DROP TABLE <table_name>;
```

## Get column names of table
```
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '<table_name>'
```
```
SELECT Column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='<schema_name>' AND TABLE_NAME = '<table_name>';
```
## Insert
```
INSERT INTO <table_name> (<column1>, <column2>, <column3>, ...)
VALUES (<value1>, <value2>, <value3>, ...);
```

## Create User
```
create user 'tamara'@'%' identified by 'PASSWORD';
```

## Grand Privileges
```
grant select, insert on DeepHumanVision.* to 'tamara'@'%';
```

## Trouble Shooting
### Foreign key constraint fails
If you get the following error message when you try to delete a table:
```
ERROR 1217 (23000): Cannot delete or update a parent row: a foreign key constraint fails
```
This usually happens when another table is referencing the primary key of this table. By deleting this table, references will get lost.
You can force the deletion by following the following commands. **But make sure, you really want to drop the table!**
```
SET FOREIGN_KEY_CHECKS=0;
DROP TABLE <table_name>;
SET FOREIGN_KEY_CHECKS=1;
```

## Who has access to what
```
SHOW GRANTS FOR <user_name>;
```

## Show all users
```
select User from mysql.user;
```
