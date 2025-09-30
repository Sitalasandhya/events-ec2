import pytest 
import boto3 
import requests
import logging
from requests_aws4auth import AWS4Auth

logging.basicConfig(level=logging.INFO) 

'''The ACCESS_KEY and SECRET_KEY should be replaced with the iam user access key and secret key'''
ACCESS_KEY = "xxxxxxxxxxxx"
SECRET_KEY = "xxxxxxxxxxxx"
REGION = "us-east-1"
SERVICE = "execute-api"

auth = AWS4Auth(ACCESS_KEY,SECRET_KEY,REGION,SERVICE)

@pytest.fixture
def api_action(request):

    api_url = "https://nx0gn3q6e2.execute-api.us-east-1.amazonaws.com/test/actions"  
    params = request.param
    
    try:
        response = requests.post(api_url, params=params, auth=auth)
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

@pytest.mark.parametrize("api_action", [{"action": "start", "instance_id":"i-011e2bcbbb1130be1"}], indirect=True)
def test_api_start_action(api_action):
    '''This validates the start action of the api endpoint''' 

    response = api_action.get("response")  
    assert response.status_code == 200

@pytest.mark.parametrize("api_action", [{"action": "stop", "instance_id":"i-011e2bcbbb1130be1"}], indirect=True)
def test_api_stop_action(api_action):
    '''This validates the stop action of the api endpoint'''

    response = api_action.get("response")
    assert response.status_code == 200

@pytest.mark.parametrize("api_action", [{"action": "terminate","instance_id":"i-0dda3b5701ce03495"}], indirect=True)
def test_api_terminate_action(api_action):
    '''This validates the terminate action of the api endpoint'''

    response = api_action.get("response")
    assert response.status_code == 200

