#!/bin/bash

COUNT=${COUNT:-10}

if [ $# -ne 1 ]; then
  echo "Usage: $0 <output-file>"
  exit 1
fi

OUTPUT="$1"
shift

if [ -z "$AWS_ROLE_ARN" ]; then
  echo "Must set AWS_ROLE_ARN"
  exit 1
fi

if [ -z "$AWS_REGION" ]; then
  echo "Must set AWS_REGION"
  exit 1
fi

if [ -z "$OTEL_LAYER" ]; then
  echo "Must set OTEL_LAYER"
  exit 1
fi

if [ -z "$ROTEL_LAYER" ]; then
  echo "Must set ROTEL_LAYER"
  exit 1
fi

cat <<EOF
Running benchmark with the following:
 - AWS Region: $AWS_REGION
 - OTEL Layer: $OTEL_LAYER
 - Rotel Layer: $ROTEL_LAYER
EOF

set -e

make bundle

cd benchmark

echo "Testing base case"

uv run main.py --path ../function.zip --count $COUNT --function-name benchmark-coldstart \
  --role-arn "$AWS_ROLE_ARN" --region "$AWS_REGION" --output "$OUTPUT"

echo "Testing OpenTelemetry collector layer"

uv run main.py --path ../function.zip --count $COUNT --function-name benchmark-coldstart-otel \
  --environment OPENTELEMETRY_COLLECTOR_CONFIG_URI=/var/task/collector.yaml \
  --role-arn "$AWS_ROLE_ARN" --region "$AWS_REGION" --layer "$OTEL_LAYER" --output "$OUTPUT"

echo "Testing Rotel layer"

uv run main.py --path ../function.zip --count $COUNT --function-name benchmark-coldstart-rotel \
  --environment ROTEL_ENV_FILE=/var/task/rotel.env \
  --role-arn "$AWS_ROLE_ARN" --region "$AWS_REGION" --layer "$ROTEL_LAYER" --output "$OUTPUT"
