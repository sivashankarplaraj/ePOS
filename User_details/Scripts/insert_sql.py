# --- Insert CSV data into SQLite tables ---
import sqlite3
import csv
import dotenv
import os
from datetime import datetime

# Load environment variables from .env file
dotenv.load_dotenv()
shop_number = os.getenv('SHOP_NUMBER')
# Path to the SQLite database
sql_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'db.sqlite3')
# Directory where downloaded CSV files are stored
downloaded_files_dir = os.path.join(os.path.dirname(__file__), 'downloaded_files')

# Map CSV filenames to SQLite table names
csv_to_table = {
    f"PDITEM{shop_number}.CSV": "update_till_PDITEM",
    f"COMBTB{shop_number}.CSV": "update_till_COMBTB",
    "PDVAT_TB.CSV": "update_till_PDVATTB",
    "ACODES.CSV": "update_till_ACODES",
    "BCODES.CSV": "update_till_BCODES",
    "COMP_PRO.CSV": "update_till_COMPPRO",
    "OPT_PRO.CSV": "update_till_OPTPRO",
    "P_CHOICE.CSV": "update_till_PCHOICE",
    "ST_ITEMS.CSV": "update_till_STITEMS",
    "APP_COMB.CSV": "update_till_APPCOMB",
    "APP_PROD.CSV": "update_till_APPPROD",
    "GROUP_TB.CSV": "update_till_GROUPTB",
    "MISC_SEC.CSV": "update_till_MISCSEC",
    "COMB_EXT.CSV": "update_till_COMBEXT",
    "PROD_EXT.CSV": "update_till_PRODEXT",
    "SHOPS_TB.CSV": "update_till_SHOPSTB"
}

conn = sqlite3.connect(sql_db_path)
cursor = conn.cursor()

# Before inserting data, ensure all records in the tables are removed
# This is to prevent duplicates and ensure fresh data is inserted
# Note: This will delete all existing records in the tables
# Use with caution, especially in production environments
for table_name in csv_to_table.values():
    cursor.execute(f"DELETE FROM {table_name}") # Clear existing records

for file_name in os.listdir(downloaded_files_dir):
    table_name = csv_to_table.get(file_name)
    if not table_name:
        print(f"No table mapping for {file_name}, skipping.")
        continue
    file_path = os.path.join(downloaded_files_dir, file_name)
    for encoding in ['utf-8', 'latin-1']:
        try:
            with open(file_path, newline='', encoding=encoding) as csvfile:
                reader = csv.reader(csvfile)
                headers = next(reader)  # first row is header
                cursor.execute(f"PRAGMA table_info({table_name})")
                table_columns = [col[1] for col in cursor.fetchall()]
                # Always generate an 'id' column for every record
                if 'id' in table_columns and 'id' not in headers:
                    headers = ['id'] + headers
                add_last_updated = 'last_updated' in table_columns and 'last_updated' not in headers
                if add_last_updated:
                    headers.append('last_updated')
                placeholders = ','.join(['?'] * len(headers))
                insert_sql = f"INSERT OR REPLACE INTO {table_name} ({','.join(headers)}) VALUES ({placeholders})"
                row_count = 0
                mismatch_count = 0
                id_counter = 1
                for row in reader:
                    # Special handling for PROD_EXT.CSV: merge all columns after the 4th into the description
                    if file_name == 'PROD_EXT.CSV' and len(row) > 5:
                        row = row[:4] + [','.join(row[4:])]
                    # Special handling for COMB_EXT.CSV: merge all columns after the 3rd into the description
                    if file_name == 'COMB_EXT.CSV' and len(row) > 4:
                        row = row[:3] + [','.join(row[3:])]
                    # Always generate id for every record
                    if 'id' in table_columns:
                        row = [id_counter] + row
                        id_counter += 1
                    if add_last_updated:
                        row.append(datetime.now().isoformat(sep=' ', timespec='seconds'))
                    if len(row) != len(headers):
                        print(f"[ERROR] File: {file_name}, Table: {table_name}, Row columns: {len(row)}, Header columns: {len(headers)}")
                        print(f"Header: {headers}")
                        print(f"Row: {row}")
                        mismatch_count += 1
                    cursor.execute(insert_sql, row)
                    row_count += 1
                print(f"Inserted data from {file_name} into {table_name}{' ('+encoding+')' if encoding=='latin-1' else ''}. Total rows: {row_count}. Mismatches: {mismatch_count}")
                # Extra check for PDITEM and PRODEXT
                if file_name.startswith('PDITEM') or file_name == 'PROD_EXT.CSV':
                    debug_path = os.path.join(os.path.dirname(__file__), 'debug_output.txt')
                    with open(debug_path, 'a', encoding='utf-8') as dbg:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        db_count = cursor.fetchone()[0]
                        dbg.write(f"[INFO] Table {table_name} now has {db_count} records after insert.\n")
                        # Write table schema
                        dbg.write(f"[SCHEMA] {table_name}:\n")
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        schema = cursor.fetchall()
                        for col in schema:
                            dbg.write(str(col) + '\n')
                        # Write triggers for the table
                        dbg.write(f"[TRIGGERS] {table_name}:\n")
                        cursor.execute(f"SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger' AND tbl_name='{table_name}'")
                        triggers = cursor.fetchall()
                        if not triggers:
                            dbg.write("No triggers found.\n")
                        else:
                            for trig in triggers:
                                dbg.write(str(trig) + '\n')
                        # Write first 100 rows
                        dbg.write(f"[SAMPLE ROWS] {table_name} (first 100):\n")
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                        for row in cursor.fetchall():
                            dbg.write(str(row) + '\n')
                        # Write all distinct values of the first column (likely PK)
                        if schema:
                            pk_col = schema[0][1]
                            dbg.write(f"[DISTINCT VALUES] {table_name}.{pk_col}:\n")
                            cursor.execute(f"SELECT DISTINCT {pk_col} FROM {table_name}")
                            for val in cursor.fetchall():
                                dbg.write(str(val) + '\n')
                break
        except UnicodeDecodeError:
            continue

conn.commit()
conn.close()