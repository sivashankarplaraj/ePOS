"""Import CSV data into SQLite tables.

This script can be executed as a program or imported for its `csv_to_table` mapping.
When imported, it will NOT perform any side-effects (DB writes) due to the
`if __name__ == '__main__'` guard below.
"""

import sqlite3
import csv
import dotenv
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Explicitly load .env from project root to work in hosted environments
dotenv.load_dotenv(BASE_DIR / '.env')

# Resolve paths and environment once on import (safe; no DB I/O here)
shop_number = os.getenv('SHOP_NUMBER') or '1'  # fallback to '1' if unset

sql_db_path = BASE_DIR / 'db.sqlite3'
# Directory where downloaded CSV files are stored
script_dir = Path(__file__).resolve().parent
downloaded_files_dir = script_dir / 'downloaded_files'

# Mappings for CSV -> table. Some use shop suffix <n>.
# Included: EPOS_PROD<n>, EPOS_GROUP<n>, EPOS_FREE_PROD.CSV, EPOS_COMB_FREE_PROD.CSV (Extras removed)
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
    "SHOPS_TB.CSV": "update_till_SHOPSTB",
    # New tables (with shop number where applicable)
    f"EPOS_PROD{shop_number}.CSV": "update_till_EPOSPROD",
    f"EPOS_GROUP{shop_number}.CSV": "update_till_EPOSGROUP",
    "EPOS_FREE_PROD.CSV": "update_till_EPOSFREEPROD",
    "EPOS_COMB_FREE_PROD.CSV": "update_till_EPOSCOMBFREEPROD",
    f"EPOS_COMB{shop_number}.CSV": "update_till_EPOSCOMB",
}


def _run_import():
    """Execute the CSV import against SQLite, printing progress to stdout."""
    # Basic validation / logging
    if not downloaded_files_dir.exists():
        raise SystemExit(f"Downloaded files directory not found: {downloaded_files_dir}")

    print(f"Using DB: {sql_db_path}")
    print(f"Using shop number: {shop_number}")
    print(f"Scanning CSV directory: {downloaded_files_dir}")

    conn = sqlite3.connect(sql_db_path)
    cursor = conn.cursor()

    # Determine existing tables for warning about missing targets
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    # Normalize to lowercase for robust comparison across backends
    existing_tables = { (r[0] or '').lower() for r in cursor.fetchall() }

    # Clear existing data (truncate style) for mapped tables that exist
    for table_name in set(csv_to_table.values()):
        if table_name.lower() in existing_tables:
            cursor.execute(f"DELETE FROM {table_name}")
            print(f"Cleared table {table_name}")
        else:
            print(f"[WARN] Table {table_name} does not exist; skipping clear phase")

    # Helper: insert rows from one CSV
    def load_csv(file_name: str, table_name: str):
        file_path = downloaded_files_dir / file_name
        if not file_path.exists():
            print(f"[MISS] {file_name} not found; skipping")
            return
        # Try encodings fallback
        for encoding in ('utf-8', 'latin-1'):
            try:
                with open(file_path, newline='', encoding=encoding) as csvfile:
                    reader = csv.reader(csvfile)
                    try:
                        headers = next(reader)
                    except StopIteration:
                        print(f"[EMPTY] {file_name}")
                        return
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    table_columns = [col[1] for col in cursor.fetchall()]
                    if not table_columns:
                        print(f"[WARN] Table {table_name} has no schema info; skipped")
                        return
                    # Header mapping removed: model fields now align with CSV headers.
                    # Inject id if necessary
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
                        # Combined field rules
                        if file_name == 'PROD_EXT.CSV' and len(row) > 5:
                            row = row[:4] + [','.join(row[4:])]
                        if file_name == 'COMB_EXT.CSV' and len(row) > 4:
                            row = row[:3] + [','.join(row[3:])]
                        if 'id' in table_columns:
                            row = [id_counter] + row
                            id_counter += 1
                        if add_last_updated:
                            row.append(datetime.now().isoformat(sep=' ', timespec='seconds'))
                        if len(row) != len(headers):
                            print(f"[ERR] {file_name}: row len {len(row)} != header len {len(headers)}")
                            print(f"       Header: {headers}")
                            print(f"       Row: {row}")
                            mismatch_count += 1
                        cursor.execute(insert_sql, row)
                        row_count += 1
                    print(f"[OK] {file_name} -> {table_name} ({encoding}) rows={row_count} mismatches={mismatch_count}")
                    return  # success; break outer encoding loop
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"[FAIL] {file_name} ({encoding}): {e}")
                return
        print(f"[FAIL] {file_name}: encodings failed")

    # Process all mapped CSVs
    for file_name, table_name in csv_to_table.items():
        load_csv(file_name, table_name)

    # Debug dump for key large tables
    debug_tables = [t for t in ('update_till_PDITEM','update_till_PRODEXT') if t in existing_tables]

    with open(script_dir / 'debug_output.txt', 'a', encoding='utf-8') as dbg:
        for t in debug_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            count = cursor.fetchone()[0]
            dbg.write(f"[INFO] {t} count={count}\n")
            cursor.execute(f"PRAGMA table_info({t})")
            for col in cursor.fetchall():
                dbg.write(str(col) + '\n')
            cursor.execute(f"SELECT * FROM {t} LIMIT 50")
            for row in cursor.fetchall():
                dbg.write(str(row) + '\n')

    conn.commit()
    conn.close()
    print("Import complete.")


def main():
    _run_import()


if __name__ == '__main__':
    main()