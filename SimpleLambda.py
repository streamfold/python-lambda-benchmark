import boto3
import json
import os

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource, DEPLOYMENT_ENVIRONMENT
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Set up the OpenTelemetry tracer provider with a resource name.
resource = Resource(attributes={
    SERVICE_NAME: "python-lambda-example",
    DEPLOYMENT_ENVIRONMENT: "dev",
})
provider = TracerProvider(resource=resource)

span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces"))
provider.add_span_processor(span_processor)

trace.set_tracer_provider(provider)

tracer = trace.get_tracer("python-lambda.tracer")

def echo(payload):
    return payload

def list_buckets(payload):
    client = boto3.client("s3")
    buckets = client.list_buckets()
    bucket_names = list(map(lambda b: b['Name'], buckets['Buckets']))

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "Buckets": bucket_names,
            "Region ": os.environ['AWS_REGION']
        })
    }

operations = {
    'echo': echo,
    'list_buckets': list_buckets,
}

def lambda_handler(event, context):
    '''Provide an event that contains the following keys:
      - operation: one of the operations in the operations dict below
      - payload: a JSON object containing parameters to pass to the
        operation being performed
    '''

    with tracer.start_as_current_span(f"op-{event['operation']}") as span:
        operation = event['operation']
        payload = event['payload']

        if operation in operations:
            return operations[operation](payload)
        else:
            raise ValueError(f'Unrecognized operation "{operation}"')

