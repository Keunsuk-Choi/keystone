import requests
import keystone.conf
from keystone.keycloak import variables as k_vars

# CONF = keystone.conf.CONF
# group_url = CONF.keycloak.group_url
# token_url = CONF.keycloak.token_url
# client_id = CONF.keycloak.client_id
# client_secret = CONF.keycloak.client_secret
group_url = k_vars.group_url
token_url = k_vars.token_url
client_id = k_vars.client_id
client_secret = k_vars.client_secret

def send_post_request(url, data, headers=None):
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors (non-2xx status codes)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
def get_access_token():
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
        'scope': 'openid',
    }
    token_response = send_post_request(token_url, data=token_data)
    access_token = token_response.get('access_token')
    return access_token

def send_get_request(url):
    access_token = get_access_token()
    headers= {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    try: 
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
def create_group(name):
    access_token = get_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    data = {'name': f'{name}'}
    # requests.post(group_url, headers, json=data)
    response = requests.post(group_url, json=data, headers=headers)
    return response
        
def list_group():
    data = send_get_request(group_url)
    return data

def get_group(name):
    search_url = group_url+'?exact=true&search=' + name
    data = send_get_request(search_url)
    return data

def delete_group(name):
    id = get_group_id(name)
    access_token = get_access_token()
    headers= {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    delete_url = group_url + '/' + id
    return requests.delete(url=delete_url, headers=headers)

def update_group(name, new_name):
    id = get_group_id(name)
    access_token = get_access_token()
    headers= {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    update_url = group_url + '/' + id
    group_data = {'name': f'{new_name}'}
    return requests.put(update_url, headers=headers, json=group_data)

def get_group_id(name):
    data = get_group(name)
    id = data[0].get('id')
    return id

