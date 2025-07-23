import sqlite3

DB_PATH = 'trackmycalorie.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Print all table names
print('Tables:')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
for table in tables:
    print(f'  - {table}')
print('\n')

# Print schema for each table
print('Schema:')
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
schemas = cursor.fetchall()
for schema in schemas:
    print(schema[0])
print('\n')

# Print first 5 rows of each table
for table in tables:
    print(f'First 5 rows from {table}:')
    try:
        cursor.execute(f'SELECT * FROM {table} LIMIT 5;')
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        if not rows:
            print('  (No data)')
    except Exception as e:
        print(f'  Error reading table {table}: {e}')
    print()

conn.close() 