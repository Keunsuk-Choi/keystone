import requests
import keystone.conf

CONF = keystone.conf.CONF
group_url = CONF.keycloak.group_url
token_url = CONF.keycloak.token_url


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
        'client_id': CONF.keycloak.client_id,
        'client_secret': CONF.keycloak.client_secret,
        'grant_type': 'client_credentials',
        'scope': 'openid',
    }
    token_response = send_post_request(token_url, data=token_data)
    access_token = token_response.get('access_token')
    return access_token

def create_group(url, name):
    access_token = get_access_token()
    group_url = url
    group_data = {'name': f'{name}'}
    group_headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    requests.post(group_url, headers=group_headers, json=group_data)
        
def list_group(url):
    access_token = get_access_token()
    headers= {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    requests.get(url=url, headers=headers)

def delete_group(url, name):
    access_token = get_access_token()
    headers= {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    search_url = url+'?exact=true&search=' + name
    response=requests.get(url=search_url, headers=headers)
    data = response.json()
    id = data[0].get('id')
    delete_url = url+'/'+id
    requests.delete(url=delete_url, headers=headers)

def update_group(url, name, new_name):
    access_token = get_access_token()
    headers= {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    search_url = url+'?exact=true&search=' + name
    response=requests.get(url=search_url, headers=headers)
    data = response.json()
    id = data[0].get('id')
    update_url = url + '/' + id
    group_data = {'name': f'{new_name}'}
    requests.put(update_url, headers=headers, json=group_data)

        
# # PUT /admin/realms/{realm}/groups/{id}
# token_url = 'http://211.175.140.77:31000/realms/master/protocol/openid-connect/token'
# create_group(group_url, "one")
# # list_group(group_url)
# # delete_group(group_url, "one")
# # update_group(group_url, "one", "two")
