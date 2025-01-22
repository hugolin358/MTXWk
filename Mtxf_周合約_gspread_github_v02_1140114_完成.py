# -*- coding: utf-8 -*-
"""txf_nearby周合約k圖 gspread GitHub 修改中v02_1140114

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1mkEW8XJz8kb1mYxld7PCs52WhZbvFS6u
"""

#!pip install finmind

from FinMind.data import DataLoader

dl = DataLoader()

future_data = dl.taiwan_futures_daily(futures_id='MTX', start_date='2024-1-1')

"""# 1. Download row data"""

#future_data= future_data[(future_data.contract_date=="202411")]
future_data = future_data[(future_data.trading_session == "position")]
future_data = future_data[future_data['contract_date'].str.len() <= 6]
#future_data = future_data[(future_data.settlement_price > 0)]
future_data = future_data[future_data['contract_date'] == future_data.groupby('date')['contract_date'].transform('min')] #近月

df = future_data.drop_duplicates(subset=['date'])
df

"""2. Extract data for every Wednsday"""

import calendar
import pandas as pd
import logging

# ... (logging setup from previous response) ...

# Convert the 'date' column to datetime objects
future_data['date'] = pd.to_datetime(future_data['date'])
df['date'] = pd.to_datetime(df['date'])  # Ensure df['date'] is datetime

# Filter for all Wednesdays and handle exceptions
wednesdays_data = []
matched_dates = set()  # Keep track of already matched dates

# Get the year range from df
min_year = df['date'].min().year
max_year = df['date'].max().year

for year in range(min_year, max_year + 1):
    for month in range(1, 13):
        cal = calendar.monthcalendar(year, month)
        for week in cal:
            if week[calendar.WEDNESDAY]:
                try:
                    target_date = pd.to_datetime(f"{year}-{month:02d}-{week[calendar.WEDNESDAY]:02d}")

                    # Find the closest matching date in df
                    while target_date not in df['date'].values and target_date <= df['date'].max():
                        target_date += pd.Timedelta(days=1)

                    # Check if a match was found and the date hasn't been used before
                    if target_date in df['date'].values and target_date not in matched_dates:
                        matching_row = df[df['date'] == target_date].iloc[0]
                        wednesdays_data.append(matching_row)
                        matched_dates.add(target_date)  # Add to matched dates

                except OutOfBoundsDatetime as e:
                    logging.exception(f"OutOfBoundsDatetime error for target_date: {target_date}")
                    break

wednesdays_data = pd.DataFrame(wednesdays_data)
wednesdays_data['contract_status'] = "contract close"

# Print or use wednesdays_data as needed
wednesdays_data



"""3.Extract data for the next day of each Wednsday"""

# Second extraction based on dates from wednesdays_data + 1 day
extracted_data = []
matched_dates_extracted = set()  # Keep track of matched dates for this extraction

for index, row in wednesdays_data.iterrows():
    target_date = row['date'] + pd.Timedelta(days=1)  # Target date for second extraction

    # Find the closest matching date in df, similar to wednesdays_data logic
    while target_date not in df['date'].values and target_date <= df['date'].max():
        target_date += pd.Timedelta(days=1)

    # Check if a match was found and the date hasn't been used before
    if target_date in df['date'].values and target_date not in matched_dates_extracted:
        matching_row = df[df['date'] == target_date].iloc[0]  # Extract from df
        extracted_data.append(matching_row)
        matched_dates_extracted.add(target_date)

extracted_data = pd.DataFrame(extracted_data)
extracted_data['contract_status'] = "contract open"

extracted_data

"""4. Combination of these two extracted data to be Open and Close Date of each week contract"""

# Combine and sort the DataFrames
combined_data = pd.concat([wednesdays_data, extracted_data], ignore_index=True)
combined_data = combined_data.sort_values(by=['date'])  # Sort by 'date'

combined_data

"""5. Refit the combined data to new build dataframe gethering serial order"""

# Create a list of dictionaries, each representing a row
data_list = [row.to_dict() for index, row in combined_data.iterrows()]

# Create the new DataFrame from the list of dictionaries
new_combined_data = pd.DataFrame(data_list)

# Remove the first row
new_combined_data = new_combined_data.iloc[1:].copy()

new_combined_data

"""6. Build a new dataframe with  title of each weekly contracts and fill primarily open dates from new_bimbined_data"""

# Create the new DataFrame
new_df = pd.DataFrame(columns=["開倉日期", "商品名稱", "合約名稱", "開盤", "最高", "最低", "收盤"])

# Extract data for "開倉日期" and "合約名稱"
open_contract_data = combined_data[combined_data['contract_status'] == "contract open"]
new_df["開倉日期"] = open_contract_data["date"]

new_df["商品名稱"] = open_contract_data["futures_id"]
new_df["合約名稱"] = open_contract_data["contract_date"]


new_df

""" 7. Fill extracted data from df raw dataframe ( loop with range between open and close date) in.
   
   The current week contract which is not yet closed would go through extracting data from the lastest date of df raw dataframe.
"""

import pandas as pd

# Assuming you have 'new_combined_data', 'df', and 'new_df' DataFrames


# 1. Get close date for each open date in new_df
new_df['收盤日期'] = pd.NaT  # Initialize a new column for close dates

for index, row in new_df.iterrows():
    open_date = row['開倉日期']

    try:
        open_date_index = new_combined_data[new_combined_data['date'] == open_date].index[0]  # Use new_combined_data

        if open_date_index + 1 < len(new_combined_data):
            close_date = new_combined_data.loc[open_date_index + 1, 'date']
            new_df.loc[index, '收盤日期'] = close_date
        else:
            # If close date is missing, use the last date in df
            close_date = df['date'].max()  # Get the last date in df
            new_df.loc[index, '收盤日期'] = close_date
            print(f"Warning: No close date found for open date {open_date}. Using last date in df: {close_date}")

    except IndexError:
        print(f"Warning: No close date found for open date {open_date} (not found)")

# 2-6. Extract values from df based on open and close dates
# ... (Rest of your code remains the same) ...


# 2-6. Extract values from df based on open and close dates
for index, row in new_df.iterrows():
    open_date = row['開倉日期']
    close_date = row['收盤日期']

    # Filter df based on open and close dates
    filtered_df = df[(df['date'] >= open_date) & (df['date'] <= close_date)]

    # Extract values and assign to new_df
    try:
        new_df.loc[index, '最高'] = filtered_df['max'].max()
        new_df.loc[index, '最低'] = filtered_df['min'].min()
        new_df.loc[index, '開盤'] = filtered_df['open'].iloc[0]
        new_df.loc[index, '收盤'] = filtered_df['close'].iloc[-1]
    except IndexError:
        # Add a placeholder or handling logic for IndexError
        print(f"Warning: IndexError encountered for open_date: {open_date}, close_date: {close_date}")
        # You can assign default values, skip the row, or raise a custom exception
        # For example, to assign NaN values:
        # new_df.loc[index, ['最高', '最低', '開盤', '收盤']] = float('nan')
#display(new_df)

# Add new columns to new_df
new_df['span'] = 0  # Initialize with 0
new_df['cost'] = 0   # Initialize with 0
new_df['20周均震幅'] = 0  # Initialize with 0
new_df['最小震幅'] = 0  # Initialize with 0
new_df['小震幅'] = 0   # Initialize with 0
new_df['平均震幅'] = 0  # Initialize with 0
new_df['大震幅'] = 0   # Initialize with 0
new_df['最大震幅'] = 0  # Initialize with 0

# ... (Rest of your code, including the loop to extract values) ...

# Calculate values for the new columns after extracting data from df
for index, row in new_df.iterrows():
    new_df.loc[index, 'span'] = row['收盤'] - row['開盤']  # Calculate span

new_df.head()

# Calculate values for the new columns after extracting data from df
for index, row in new_df.iterrows():
    new_df.loc[index, 'span'] = row['最高'] - row['最低']  # Calculate span
    new_df.loc[index, 'cost'] = (row['最高'] + row['最低']) / 2  # Calculate cost

# Calculate 20DailySpanMa (rolling mean of 'span' over 20 rows)
new_df['20周均震幅'] = new_df['span'].rolling(window=20, min_periods=0).mean().astype(int)

# Calculate other columns based on rolling calculations
new_df['最小震幅'] = new_df['span'].rolling(window=20, min_periods=0).min()
new_df['最大震幅'] = new_df['span'].rolling(window=20, min_periods=0).max()
new_df['平均震幅'] = new_df['20周均震幅']
new_df['小震幅'] = (new_df['最小震幅'] + new_df['平均震幅']) / 2
new_df['大震幅'] = (new_df['最大震幅'] + new_df['平均震幅']) / 2
new_df2=new_df
new_df2

"""Transfer dataframe to google sheet"""

# Install necessary libraries
#!pip install --upgrade gspread pandas gspread_dataframe

"""API key.json store in drive and shareed for downloading to Colad VM temperially by url, which doesn't go through drive authentication"""

import requests

# Direct download link
url = "https://drive.google.com/uc?id=1PUo8axrWc0zOjTHE0f4zsRweVNGCcq6z&export=download"

# Download the file
response = requests.get(url)
if response.status_code == 200:
    with open("mtx-spreads-analysis-179ea8a41891.json", "wb") as file:
        file.write(response.content)
    print("File downloaded successfully.")
else:
    print(f"Failed to download file. HTTP status code: {response.status_code}")

# Path to the downloaded service account file
SERVICE_ACCOUNT_FILE = 'mtx-spreads-analysis-179ea8a41891.json'

"""Munt to drive let Service_Files storage in drive connected to colab

1. the gsheet api KEY is permently store in google drive,/My drive/key
2. the dataset is transferred to the  worksheet,Weekly, of spreadsheet,關卡價
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe

# Authenticate using th
SERVICE_ACCOUNT_FILE = 'mtx-spreads-analysis-179ea8a41891.json' # stored in my drive w/o eliminated as session end
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Initialize the gspread client
client = gspread.authorize(creds)

# Access the Google Sheet
sheet_name = "關卡價"
spreadsheet = client.open(sheet_name)
worksheet = spreadsheet.worksheet("Weekly")

# Clear existing data in the sheet (optional)
worksheet.clear()

# Write the DataFrame to the sheet
set_with_dataframe(worksheet, new_df2)

"""To trigger GAS web app to write data to 周 sheet of 關卡價"""

from IPython.display import IFrame

url = "https://script.google.com/macros/s/AKfycbxFLi4_yhfdsDGnEAYuqrj1aCbx8izUuWjtM-7pyQOnRUToiHfY6-e6FA3yQjKjCl47Cw/exec"
IFrame(url, width=80, height=60)

