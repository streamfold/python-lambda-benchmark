#!/bin/bash

COUNT=${COUNT:-5}

MEMORY_SIZES="128 256 512 1024 2048 3072 4096"

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

if [ -z "$DATADOG_LAYER" ]; then
  echo "Must set DATADOG_LAYER"
  exit 1
fi

if [ -z "$DD_API_KEY" ]; then
  echo "Must set DD_API_KEY"
  exit 1
fi

cat <<EOF
Running benchmark with the following:
 - Memory size: $MEMORY_SIZES
 - AWS Region: $AWS_REGION
 - OTEL Layer: $OTEL_LAYER
 - Rotel Layer: $ROTEL_LAYER
 - Datadog Layer: $DATADOG_LAYER
EOF

set -e

make bundle

cd benchmark

for MEMORY_SIZE in ${MEMORY_SIZES}; do
  echo "Testing base case at $MEMORY_SIZE MB"

  uv run main.py --path ../function.zip --count $COUNT --function-name benchmark-coldstart \
    --role-arn "$AWS_ROLE_ARN" --region "$AWS_REGION" --output "$OUTPUT" \
    --memory "$MEMORY_SIZE"
done


for MEMORY_SIZE in ${MEMORY_SIZES}; do
  echo "Testing OpenTelemetry collector layer at $MEMORY_SIZE MB"

  uv run main.py --path ../function.zip --count $COUNT --function-name benchmark-coldstart-otel \
    --environment OPENTELEMETRY_COLLECTOR_CONFIG_URI=/var/task/collector.yaml \
    --role-arn "$AWS_ROLE_ARN" --region "$AWS_REGION" --layer "$OTEL_LAYER" --output "$OUTPUT" \
    --memory "$MEMORY_SIZE"
done

for MEMORY_SIZE in ${MEMORY_SIZES}; do
  echo "Testing Rotel layer at $MEMORY_SIZE MB"

  uv run main.py --path ../function.zip --count $COUNT --function-name benchmark-coldstart-rotel \
    --environment ROTEL_ENV_FILE=/var/task/rotel.env \
    --role-arn "$AWS_ROLE_ARN" --region "$AWS_REGION" --layer "$ROTEL_LAYER" --output "$OUTPUT" \
    --memory "$MEMORY_SIZE"
done

for MEMORY_SIZE in ${MEMORY_SIZES}; do
  echo "Testing Datadog layer at $MEMORY_SIZE MB"

  uv run main.py --path ../function.zip --count $COUNT --function-name benchmark-coldstart-datadog \
    --environment DD_API_KEY=${DD_API_KEY},DD_OTLP_CONFIG_RECEIVER_PROTOCOLS_HTTP_ENDPOINT=localhost:4318 \
    --role-arn "$AWS_ROLE_ARN" --region "$AWS_REGION" --layer "$DATADOG_LAYER" --output "$OUTPUT" \
    --memory "$MEMORY_SIZE"
done
