# google_drive_url: https://drive.google.com/drive/folders/1OyXuFEUFgRw9jwHgtk9p2_rP9vcVOHKV?usp=share_link
import gdown

# Replace with your Google Drive folder URL
folder_url = "https://drive.google.com/drive/folders/1OyXuFEUFgRw9jwHgtk9p2_rP9vcVOHKV?usp=share_link"

# gdown expects the folder id, not the full URL
def extract_folder_id(url):
    if "folders/" in url:
        return url.split("folders/")[1].split("?")[0]
    raise ValueError("Invalid Google Drive folder URL")

folder_id = extract_folder_id(folder_url)
gdown.download_folder(id=folder_id, quiet=False, use_cookies=False)

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
