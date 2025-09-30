import json
import boto3
import os
import time
import tempfile
from botocore.exceptions import ClientError

ami_id=os.environ['AMI']
instance_type = os.environ['INSTANCE_TYPE']
bucket_name = os.environ['S3_BUCKET']
region = os.environ['REGION']

ec2_client = boto3.client('ec2', region_name=region)
ec2 = boto3.resource('ec2', region_name=region)
s3 = boto3.client('s3', region_name=region)

def lambda_handler(event, context):
    '''This function is used to create, start, stop, terminate EC2 instances'''

    #access the query string parameters
    event_payload = event.get('queryStringParameters',{})

    try:
        action = event_payload.get('action', 'None').lower()
        if action not in ['create', 'start', 'stop', 'terminate']:
            return {
                'statusCode': 400,
                'body': json.dumps({"message": f"Invalid action: {action}"})
            }
        if action == 'create':
            return create_instance()
        else:
            instance_id = event.get('queryStringParameters', {}).get('instance_id')
            if not instance_id: 
                return {
                    'statusCode': 400,
                    'body': json.dumps({"message": f"Missing instance_id for {action} action"})
                }
            try:
                if action == 'start':
                    return start_instance(instance_id)
                elif action == 'stop':
                    return stop_instance(instance_id)
                elif action == 'terminate':
                    return terminate_instance(instance_id)
                else:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({"message": f"Invalid {action}"})
                    }
            except Exception as e:
                return {
                'statusCode': 400,
                'body': json.dumps(str(e))
                }
    except AttributeError:
        return {
            'statusCode': 400,
            'body': json.dumps({"message": "Missing action parameter"})
        }         
    except Exception as e:
        return {
                'statusCode': 400,
                'body': json.dumps(str(e))
        }                                                              
def create_ec2_key_pair():
    '''This function is used to create a key pair and generate a presigned url to access the pem file'''
    try:
        key_name = f"ec2-private-key-{int(time.time())}"
        response = ec2_client.create_key_pair(KeyName=key_name)
        private_key = response['KeyMaterial']

        # Save PEM file to /tmp
        pem_file_path = os.path.join(tempfile.gettempdir(), f"{key_name}.pem")
        with open(pem_file_path, 'w') as pem_file:
            pem_file.write(private_key)

        # Upload PEM to S3
        s3.upload_file(pem_file_path, bucket_name, f"{key_name}.pem")

        # Generate presigned URL (valid for 1 hour)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': f"{key_name}.pem"},
            ExpiresIn=3600
        )
        return key_name, presigned_url
    except ClientError as err:
        error_code = err.response['Error']['Code']
        error_message = err.response['Error']['Message']
        return error_message
    except Exception as e:
        return e
def create_instance():
    '''This function is used to create EC2 instances'''
    try:
        key_name, presigned_url = create_ec2_key_pair()
        response = ec2_client.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_name,
            MaxCount=1,
            MinCount=1,
            SecurityGroups = ['default']
        )
        instance_id = response['Instances'][0]['InstanceId']
        instance = ec2.Instance(instance_id)
        instance.wait_until_running()

        # Wait for instance status checks to pass
        while True:
            instance.reload()
            status = instance.state['Name']
            if status == 'running':
                break
            else:
                time.sleep(5)
            
        instance_public_ip = instance.public_ip_address

        ssh_command = f"ssh -i {key_name}.pem ec2-user@" + instance_public_ip

        instance_details = {
        'instance_id': instance_id,
        'public_ip': instance_public_ip,
        'username': 'ec2-user',
        'ssh_command': ssh_command,
        'pem_filename': f"{key_name}.pem",
        'pem_download_url': presigned_url
        }

        body_content = json.dumps(instance_details)
        return {
            'statusCode': 200,
            'body': body_content
        }
    except ClientError as err:
        error_code = err.response['Error']['Code']
        error_message = err.response['Error']['Message']
        return {
            "statusCode": 400,
            "body": json.dumps({"message": error_message})
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps(str(e))
        }

def check_status(instance_id):
    '''This function is used to check the status'''
    try:
        response = ec2_client.describe_instance_status(InstanceIds=[instance_id], IncludeAllInstances=True)
        state = response['InstanceStatuses'][0]['InstanceState']['Name']
        return state
    except ClientError as err:
        error_code = err.response['Error']['Code']
        error_message = err.response['Error']['Message']
        return error_message
    except Exception as e:
        return e

def start_instance(instance_id):
    '''This is used to start an EC2 instance'''
    try:
        state = check_status(instance_id)
        if state == 'stopped':
            response = ec2_client.start_instances(InstanceIds=[instance_id])
            return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Instance {instance_id} started successfully"})
            }
        elif state == 'running':
            return {
                "statusCode": 400,
                "body": json.dumps({"message": f"Instance {instance_id} is already running"})
            }
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": f"Instance {instance_id} is in state: {state} and start operation is not allowed."})
            }
    except ClientError as err:
        error_code = err.response['Error']['Code']
        error_message = err.response['Error']['Message']
        return {
            "statusCode": 400,
            "body": json.dumps({"message": error_message})
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps(str(e))
        }

def stop_instance(instance_id):
    '''This is used to stop EC2 instance'''
    try:
        response = ec2_client.stop_instances(InstanceIds=[instance_id])
        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Instance {instance_id} stopped successfully"})
        }
    except ClientError as err:
        error_code = err.response['Error']['Code']
        error_message = err.response['Error']['Message']
        return {
            "statusCode": 400,
            "body": json.dumps({"message": error_message})
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps(str(e))
        }

def terminate_instance(instance_id):
    '''This is used to terminate an EC2 instance'''
    try:
        state = check_status(instance_id)
        if state in ['shutting-down','terminated']:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": f"Instance {instance_id} is already terminated"})
            }
        else:
            response = ec2_client.terminate_instances(InstanceIds=[instance_id])
            return {
                "statusCode": 200,
                "body": json.dumps({"message": f"Instance {instance_id} terminated successfully"})
            }
    except ClientError as err:
        error_code = err.response['Error']['Code']
        error_message = err.response['Error']['Message']
        return {
            "statusCode": 400,
            "body": json.dumps({"message": error_message})
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps(str(e))
        }