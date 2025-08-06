# update_till_db.py
# https://raw.githubusercontent.com/sivashankarplaraj/ePOS/refs/heads/main/docx/BROADWATER_CSV_240725/
import os
from dotenv import load_dotenv
import requests

raw_git_path = "https://raw.githubusercontent.com/sivashankarplaraj/ePOS/refs/heads/main/docx/"

# Load environment variables from the global .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))
shop_number = os.getenv('SHOP_NUMBER')

csv_files = [
    "PDVAT_TB.CSV",
    "PDITEM<n>.CSV",    # <n> is the shop number, 1-15
    "COMBTB<n>.CSV",    # <n> is the shop number, 1-15
    "ACODES.CSV",
    "BCODES.CSV",
    "COMP_PRO.CSV",
    "OPT_PRO.CSV",
    "P_CHOICE.CSV",
    "ST_ITEMS.CSV",
    "APP_COMB.CSV",
    "APP_PROD.CSV",
    "GROUP_TB.CSV",
    "MISC_SEC.CSV",
    "COMB_EXT.CSV",
    "PROD_EXT.CSV",
    "SHOPS_TB.CSV"
]

# Creat raw urls for each CSV file
csv_urls = []
raw_git_path = raw_git_path + str(shop_number) + "/"
for file in csv_files:
    if "<n>" in file:
        csv_urls.append(f"{raw_git_path}{file.replace('<n>', str(shop_number))}")
    else:
        csv_urls.append(f"{raw_git_path}{file}")

# Download each CSV file and save it to the downloaded files directory
downloaded_files_dir = os.path.join(os.path.dirname(__file__), 'downloaded_files')
if not os.path.exists(downloaded_files_dir):
    os.makedirs(downloaded_files_dir)
for url in csv_urls:
    file_name = os.path.basename(url)
    file_path = os.path.join(downloaded_files_dir, file_name)
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded {file_name} to {file_path}")
    else:
        print(f"Failed to download {file_name} from {url}")



# Table 5: PDVAT_TB
# CSV file: PDVAT_TB.CSV

# Table 6: PDITEM
# CSV file: PDITEM<n>.CSV (<n> is the shop number, 1-15)

# Table 7: COMBTB
# CSV file: COMBTB<n>.CSV (<n> is the shop number, 1-15)

# Table 8: ACODES
# CSV file: ACODES.CSV

# Table 9: BCODES
# CSV file: BCODES.CSV

# Table 10: COMP_PRO
# CSV file: COMP_PRO.CSV

# Table 11: OPT_PRO
# CSV file: OPT_PRO.CSV

# Table 12: P_CHOICE
# CSV file: P_CHOICE.CSV

# Table 13: ST_ITEMS
# CSV file: ST_ITEMS.CSV

# Table 14: APP_COMB
# CSV file: APP_COMB.CSV

# Table 15: APP_PROD
# CSV file: APP_PROD.CSV

# Table 16: GROUP_TB
# CSV file: GROUP_TB.CSV

# Table 17: MISC_SEC
# CSV file: MISC_SEC.CSV

# Table 18: COMB_EXT
# CSV file: COMB_EXT.CSV

# Table 19: PROD_EXT
# CSV file: PROD_EXT.CSV

# Table 20: SHOPS_TB
# CSV file: SHOPS_TB.CSV
