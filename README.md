# garage_storage
Garage storage




## Data migration
1 .Backup and Remove the Existing Migrations Directory: If you have any important migration scripts in the migrations directory, back them up first. Then, remove the existing migrations directory:
```bash 

mv migrations migrations_backup

export FLASK_APP=run.py

```
2. Reinitialize the Migrations Directory: Reinitialize the migrations directory to create a new env.py file:
```bash
flask db init
```
3. Create a Migration Script: Generate a new migration script to add the new columns to your database:
```bash

flask db migrate -m "Add new columns to LLMUsasge"
```
4. Apply the Migration: Apply the migration to update the database schema:
```bash
flask db upgrade
```
5. Verify the Migration: Verify that the new columns have been added to the database:
```bash
sqlite3 garage_storage.db
```
```sql
.schema
```
6. Restore the Original Migrations Directory: If you backed up the original migrations directory, you can restore it now:
```bash
mv migrations_backup migrations
```
7. Commit the Changes: Commit the changes to your version control system:
```bash
git add .
git commit -m "Add new columns to LLMUsage"
git push
```


These steps should resolve the issue and allow you to proceed with the migration. If you encounter any issues, please let me know.

db
edit
