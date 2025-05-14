# python-lambda-benchmark

Small repo to benchmark Lambda runtime execution across different layers and memory sizes.

Tests:
* [AWS OpenTelemetry Collector layer](https://github.com/open-telemetry/opentelemetry-lambda)
* [Rotel collector layer](https://github.com/streamfold/rotel-lambda-extension)
* [Datadog Go Layer](https://docs.datadoghq.com/serverless/aws_lambda/opentelemetry/?tab=python): While there is a new [Rust DD layer](https://www.datadoghq.com/blog/datadog-next-gen-lambda-extension/), the Go version is still required for OpenTelemetry support.

## Usage

Use Github to invoke a workflow to run the tests.
