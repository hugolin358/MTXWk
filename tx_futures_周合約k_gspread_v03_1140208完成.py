# -*- coding: utf-8 -*-
"""TX_futures_周合約k  gspread_v03 1140208完成

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1jsPP-TfM9VhGKhGvKRiw2nqjtH6v3f1v
"""

#!pip install finmind

from FinMind.data import DataLoader

dl = DataLoader()


future_data = dl.taiwan_futures_daily(futures_id='TX', start_date='2023-12-21')

"""# 1. Download row data"""

#future_data= future_data[(future_data.contract_date=="202411")]
future_data = future_data[(future_data.trading_session == "position")]
future_data = future_data[future_data['contract_date'].str.len() <= 6]
#future_data = future_data[(future_data.settlement_price > 0)]
future_data = future_data[future_data['contract_date'] == future_data.groupby('date')['contract_date'].transform('min')] #近月

df = future_data.drop_duplicates(subset=['date'])
df

"""2. remark contract open and contract close by reaching Wed. from top of df row by row  but considering off day condition on someday

 From top-to-buttom of df reaching the Wed., if yes tagged "contract close" and tagged next row "contract open", else check  diff. from last contract open >9, >6 if yes tagged contract close in i-1 and i
"""

import pandas as pd

# Assuming df is your original DataFrame
# Ensure that 'date' is in datetime format
df['date'] = pd.to_datetime(df['date'])

# Initialize an empty DataFrame for the results
wednesdays_data = pd.DataFrame(columns=df.columns.tolist() + ['contract_status'])

# Variable to track the last 'contract open' date
last_contract_open_date = None

# Iterate through the DataFrame
i = 0
while i < len(df):  # Iterate through all rows
    current_date = df.iloc[i]['date']

    # Check if the current date is a Wednesday
    if current_date.weekday() == 2:  # Wednesday is represented by 2
        # Add the Wednesday row as 'contract close'
        wed_row = df.iloc[i].copy()
        wed_row['contract_status'] = 'contract close'
        wednesdays_data = pd.concat([wednesdays_data, wed_row.to_frame().T], ignore_index=True)

        # Add the next row as 'contract open'
        if i + 1 < len(df):  # Ensure there is a next row
            next_row = df.iloc[i + 1].copy()
            next_row['contract_status'] = 'contract open'
            wednesdays_data = pd.concat([wednesdays_data, next_row.to_frame().T], ignore_index=True)

            # Update the last 'contract open' date
            last_contract_open_date = next_row['date']

        # Skip the next row since it's already been processed
        i += 1
    else:
        # Check if the difference between the current date and the last 'contract open' date is more than 9 days
        if last_contract_open_date is not None and (current_date - last_contract_open_date).days > 9:
            # Add the previous row as 'contract close'
            if i - 1 >= 0:  # Ensure there is a previous row
                close_row = df.iloc[i - 1].copy()
                close_row['contract_status'] = 'contract close'
                wednesdays_data = pd.concat([wednesdays_data, close_row.to_frame().T], ignore_index=True)

            # Add the current row as 'contract open'
            open_row = df.iloc[i].copy()
            open_row['contract_status'] = 'contract open'
            wednesdays_data = pd.concat([wednesdays_data, open_row.to_frame().T], ignore_index=True)

            # Update the last 'contract open' date
            last_contract_open_date = open_row['date']

        # Check if the difference is more than 6 days but less than or equal to 9 days
        elif last_contract_open_date is not None and (current_date - last_contract_open_date).days > 6:
            # Add the current row as 'contract close'
            close_row = df.iloc[i].copy()
            close_row['contract_status'] = 'contract close'
            wednesdays_data = pd.concat([wednesdays_data, close_row.to_frame().T], ignore_index=True)

            # Add the next row as 'contract open'
            if i + 1 < len(df):  # Ensure there is a next row
                open_row = df.iloc[i + 1].copy()
                open_row['contract_status'] = 'contract open'
                wednesdays_data = pd.concat([wednesdays_data, open_row.to_frame().T], ignore_index=True)

                # Update the last 'contract open' date
                last_contract_open_date = open_row['date']

            # Skip the next row since it's already been processed
            i += 1
    i += 1

# Display the resulting DataFrame
contractExtract_data=wednesdays_data
contractExtract_data

#from google.colab import files

#wednesdays_data.to_csv('output.csv')
#files.download('output.csv')

"""3.Build a new dataframe with  title of each weekly contracts and fill primarily date, future_id and contract_date from contractExtract_data"""

# Create the new DataFrame
new_df = pd.DataFrame(columns=["開倉日期", "商品名稱", "合約名稱", "開盤", "最高", "最低", "收盤"])

# Extract data for "開倉日期" and "合約名稱"
open_contract_data =contractExtract_data[contractExtract_data['contract_status'] == "contract open"]
new_df["開倉日期"] = open_contract_data["date"]

new_df["商品名稱"] = open_contract_data["futures_id"]
new_df["合約名稱"] = open_contract_data["contract_date"]


new_df

""" 4. Fill extracted data from contractExtract_data raw dataframe ( loop with range between contract open ,targeted-date row, and contract close,targeted-date row+1,) accrodding to the "date" of each row of new_df ."""

import pandas as pd

# Assuming you have 'contractExtract_data', 'df', and 'new_df' DataFrames

# 1. Get close date for each open date in new_df
new_df['收盤日期'] = pd.NaT  # Initialize a new column for close dates

for index, row in new_df.iterrows():
    open_date = row['開倉日期']

    try:
        open_date_index = contractExtract_data[contractExtract_data['date'] == open_date].index[0]  # Use contractExtract_data

        if open_date_index + 1 < len(contractExtract_data):
            close_date = contractExtract_data.loc[open_date_index + 1, 'date']
            new_df.loc[index, '收盤日期'] = close_date
        else:
            # If close date is missing, use the last date in df
            close_date = df['date'].max()  # Get the last date in df
            new_df.loc[index, '收盤日期'] = close_date
            print(f"Warning: No close date found for open date {open_date}. Using last date in df: {close_date}")

    except IndexError:
        print(f"Warning: No close date found for open date {open_date} (not found)")

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

"""5. calculate rolling mean of 20ma and so on."""

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

"""6.Transfer dataframe to google sheet"""

# Install necessary libraries
#!pip install --upgrade gspread pandas gspread_dataframe

"""7. API key.json store in drive and shareed for downloading to Colad VM temperially by url, which doesn't go through drive authentication"""

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

"""8. use key to transfer table to google sheet

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

"""9. To trigger GAS web app to write data from weekly to 周 sheet of 關卡價"""

import requests

def trigger_gas_webapp():
    # The URL of the GAS web app
    url = "https://script.google.com/macros/s/AKfycbxFLi4_yhfdsDGnEAYuqrj1aCbx8izUuWjtM-7pyQOnRUToiHfY6-e6FA3yQjKjCl47Cw/exec"

    try:
        # Send a GET request to the GAS web app
        response = requests.get(url)

        # Check the response status code
        if response.status_code == 200:
            print("Request successful!")
            print("Response from GAS:", response.text)
        else:
            print(f"Request failed with status code {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    trigger_gas_webapp()

