import json

def lambda_handler(event, context):

    if not 'authorizationToken' in event:
        raise Exception('Unauthorized')

    if event["authorizationToken"]== 'abc1234':
        return generatePolicy('user', 'Allow', event['methodArn'])
    else:
        return generatePolicy('user', 'Deny', event['methodArn'])

def generatePolicy(principal_id, effect, resource):

    auth_response = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
    }

    return auth_response
