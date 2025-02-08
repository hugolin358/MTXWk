#To trigger GAS web app to write data from weekly to 周 sheet of 關卡價

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
          
        else:
            print(f"Request failed with status code {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    trigger_gas_webapp()
