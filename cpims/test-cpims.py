import requests

USERNAME='testhealthit'
PASSWORD='T3st@987654321'
TOKEN_URL='https://ovc.childprotection.uonbi.ac.ke/api/token/'  # Replace with your token endpoint

data = {
    'username': USERNAME,
    'password': PASSWORD
}

response = requests.post(TOKEN_URL, data=data)

if response.status_code == 200:
    token = response.json().get('access')
else:
   print(f'Response: {response.text}')


def get_data_by_id_card(url, id):
    """Make a GET request to the specified URL with Bearer token authentication."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, json=id)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)

        # Print the response data
        print("GET Response Status Code:", response.status_code)
        print("Response JSON:", response.json())

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

# def verify_by_passport(url, data):
#     """Make a POST request to the specified URL with the given data and Bearer token authentication."""
#     headers = {
#         'Authorization': f'Bearer {token}',
#         'Content-Type': 'application/json'  # Specify the content type
#     }
    
#     try:
#         response = requests.post(url, json=data, headers=headers)
#         response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)

#         # Print the response data
#         print("POST Response Status Code:", response.status_code)
#         print("Response JSON:", response.json())

#     except requests.exceptions.HTTPError as http_err:
#         print(f"HTTP error occurred: {http_err}")
#     except Exception as err:
#         print(f"An error occurred: {err}")

if __name__ == "__main__":

    id = {
        "id_number": "39922822",
    }
    # Example URL for GET request
    get_url = "https://ovc.childprotection.uonbi.ac.ke/api/iprs/2/"  # Replace with your API endpoint
    get_data_by_id_card(get_url, id)

    # # Example URL for POST request
    # post_url = "https://ovc.childprotection.uonbi.ac.ke/api/iprs/4/"  # Replace with your API endpoint
    # post_data_payload = {
    #     "id_number": "40031448",
    # }
    # verify_by_passport(post_url, post_data_payload)