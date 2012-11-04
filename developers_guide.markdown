How to add a new setting
------------------------

1. Add a field to `models.EWUser`.
2. Add the field to the database, e.g.:

    $ sqlite3 sqlite.db
    sqlite> alter table ew_ewuser add column <new field> string;
    sqlite> update ew_ewuser set <new_field>='';
    sqlite> ^D

3. Add the database upgrade information to `UPGRADE.txt`.
4. Modify `views.ew_settings` where needed to include the new field.
5. Update the translation file.
