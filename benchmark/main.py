#!/usr/bin/env python3
import argparse
from operator import contains

import boto3
import json
import time
import os
import uuid
from botocore.exceptions import ClientError

def parse_args():
    parser = argparse.ArgumentParser(description='Deploy a function as AWS Lambda multiple times and benchmark')
    parser.add_argument('--path', required=True, help='Path to the function.zip file')
    parser.add_argument('--count', type=int, default=10, help='Number of functions to deploy (default: 10)')
    parser.add_argument('--function-name', default='test-function', help='Base name for the Lambda functions')
    parser.add_argument('--role-arn', required=True, help='ARN of the IAM role for Lambda execution')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--handler', default='SimpleLambda.lambda_handler', help='Lambda function handler')
    parser.add_argument('--runtime', default='python3.13', help='Lambda runtime (default: python3.13)')
    parser.add_argument('--memory', type=int, default=128, help='Memory in MB')
    parser.add_argument('--environment', help='Environment')
    parser.add_argument('--layer', help="ARN of layer to include")
    parser.add_argument('--output', required=True, help="Output file")
    return parser.parse_args()

def delete_lambda_function(lambda_client, function_name):
    try:
        lambda_client.delete_function(FunctionName=function_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Lambda function not found: {function_name}")
        else:
            raise

def create_lambda_function(lambda_client, function_name, environment, zip_path, role_arn, handler, runtime, memory, layer):
    try:
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()

        response = lambda_client.create_function(
            FunctionName=function_name,
            Environment={
                'Variables': environment,
            },
            Runtime=runtime,
            Role=role_arn,
            Handler=handler,
            Code={'ZipFile': zip_content},
            Timeout=10,
            MemorySize=memory,
            Layers=[layer] if layer else [],
        )
        return response['FunctionArn']
    except ClientError as e:
        print(f"Error creating Lambda function {function_name}: {e}")
        return None

def invoke_lambda_function(lambda_client, base_name, function_name, memory, payload):
    try:
        start_time = time.time()
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload)
        )
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Get the Lambda execution duration from the response headers
        response_payload = json.loads(response['Payload'].read().decode('utf-8'))
        status_code = response['StatusCode']
        execution_log = None
        if 'LogResult' in response:
            import base64
            execution_log = base64.b64decode(response['LogResult']).decode('utf-8')

        # Try to extract the actual Lambda execution duration from logs
        lambda_init_duration = None
        if execution_log:
            for line in execution_log.split('\n'):
                if 'Init Duration:' in line:
                    if 'Extension.Crash' in line:
                        print(f"Exception crashed, full execution log: {execution_log}")
                        raise Exception("Lambda extension has crashed")
                    try:
                        duration_part = line.split('Init Duration:')[1].split('ms')[0].strip()
                        lambda_init_duration = float(duration_part)
                        break
                    except (IndexError, ValueError):
                        pass
        if not lambda_init_duration:
            raise Exception("Could not extract the actual Lambda init duration from logs")

        print(f"Invoked {function_name}: Status: {status_code}, Duration: {duration:.2f} ms, Init Duration: {lambda_init_duration:.2f} ms")

        return {
            'base_name': base_name,
            'function_name': function_name,
            'memory': memory,
            'status_code': status_code,
            'client_duration_ms': duration,
            'init_duration_ms': lambda_init_duration,
            'response': response_payload
        }
    except ClientError as e:
        print(f"Error invoking Lambda function {function_name}: {e}")
        return None

def main():
    args = parse_args()

    environment = {}
    if args.environment:
        for val in args.environment.split(','):
            key, value = val.split('=')
            environment[key] = value

    # Validate the ZIP file exists
    if not os.path.isfile(args.path):
        print(f"Error: ZIP file not found at {args.path}")
        return

    # Create AWS clients
    lambda_client = boto3.client('lambda', region_name=args.region)

    # Deploy multiple Lambda functions
    functions = []
    results = []

    print(f"Deploying {args.count} Lambda functions...")
    for i in range(1, args.count + 1):
        function_name = f"{args.function_name}-{args.memory}-{i}"
        # Try to delete it first
        delete_lambda_function(lambda_client, function_name)
        function_arn = create_lambda_function(
            lambda_client,
            function_name,
            environment,
            args.path,
            args.role_arn,
            args.handler,
            args.runtime,
            args.memory,
            args.layer,
        )
        if function_arn:
            functions.append(function_name)

    # Wait for all functions to be fully initialized
    time.sleep(5)
    print(f"Successfully deployed {len(functions)} Lambda functions")

    # Invoke each function with a simple payload
    test_payload = {
        'operation': "list_buckets",
        'payload': {
            'dog': "boxer",
            'cat': "siamese",
            'timestamp': int(time.time()),
        }
    }

    for function_name in functions:
        result = invoke_lambda_function(lambda_client, args.function_name, function_name, args.memory, test_payload)
        if result:
            results.append(result)

    # Print summary
    print(f"\nSummary of lambda init durations (cold start) for {args.function_name}:")

    sorted_results = sorted(results, key=lambda x: x['init_duration_ms'])
    sorted_durations = list(map(lambda x: str(x['init_duration_ms']), sorted_results))
    print(f"Init Durations: {", ".join(sorted_durations)}")

    with open(args.output, 'a') as f:
        f.write("base_name, memory, client_duration_ms, init_duration_ms\n")
        for result in sorted_results:
            f.write(f"{result['base_name']}, {result['memory']}, {result['client_duration_ms']}, {result['init_duration_ms']}\n")

    for function_name in functions:
        delete_lambda_function(lambda_client, function_name)

if __name__ == "__main__":
    main()
