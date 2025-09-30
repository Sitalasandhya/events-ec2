import pytest 
import boto3 
import requests
import logging

logging.basicConfig(level=logging.INFO) 

#token for testing the api, the token should be replaced with valid token
token = "********" 

@pytest.fixture
def api_action(request):

    api_url = "https://nx0gn3q6e2.execute-api.us-east-1.amazonaws.com/test/events"  
    params = request.param
    header_details = {
        "auth-token": token,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, params=params, headers=header_details)
        #checking if response is in corrrect format or not
        try:
            response_json = response.json()
            message = response_json.get("message")
            logging.info(f"Response body: {message}")
        except ValueError:
            assert False, "Invalid JSON response"
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        assert False, f"API returned error: {response.status_code}"

    return {"response":response, "response_json":response_json}

@pytest.mark.parametrize("api_action", [{"action": "create"}], indirect=True)
def test_api_create_action(api_action):
    '''This validates the create action of the api endpoint'''
    assert "response" in api_action
    assert "response_json" in api_action

    response = api_action.get("response")
    response_json = api_action.get("response_json")

    assert response.status_code == 200

    #checking if body exists in response
    assert response_json is not None, "No details found in response for ec2 connection"
    
    #checking if the body_content contains all the details to connect to the ec2 instance 
    ec2_details = ["instance_id", "public_ip", "username", "ssh_command", "pem_filename", "pem_download_url"]
    if isinstance(response_json, dict):
        for item in ec2_details:
            if item not in response_json:
                raise KeyError(f"Missing {item} in response data to connect to ec2 instance")
    else:
        assert False, f"Invalid Format"
    
    logging.info(f"ec2_connection details: {response_json}")

@pytest.mark.parametrize("api_action", [{"action": "start", "instance_id":"i-00e26c640084aba8a"}], indirect=True)
def test_api_start_action(api_action):
    '''This validates the start action of the api endpoint''' 

    response = api_action.get("response")  
    assert response.status_code == 200

@pytest.mark.parametrize("api_action", [{"action": "stop", "instance_id":"i-00e26c640084aba8a"}], indirect=True)
def test_api_stop_action(api_action):
    '''This validates the stop action of the api endpoint'''

    response = api_action.get("response")
    assert response.status_code == 200

@pytest.mark.parametrize("api_action", [{"action": "terminate","instance_id":"i-009d6119cd79af30a"}], indirect=True)
def test_api_terminate_action(api_action):
    '''This validates the terminate action of the api endpoint'''

    response = api_action.get("response")
    assert response.status_code == 200

