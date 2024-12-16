### Notes on This Structure

- **protos/**: Holds `.proto` definitions for your service interface.
- **server/**: Contains all server-side logic—entry point, service implementations, database setup, configuration, utilities, and any interceptors or instrumentation.
- **tests/**: Houses both unit and integration tests.


## Dependencies & Tooling

### Python Dependencies

`requirements.txt` (pinned versions for reproducibility):

```text
annotated-types==0.7.0
certifi==2024.12.14
charset-normalizer==3.4.0
clickhouse-connect==0.8.10
colorama==0.4.6
Deprecated==1.2.15
dnspython==2.7.0
email_validator==2.2.0
googleapis-common-protos==1.66.0
grpcio==1.68.1
grpcio-health-checking==1.68.1
grpcio-reflection==1.68.1
grpcio-tools==1.68.1
idna==3.10
importlib_metadata==8.5.0
iniconfig==2.0.0
lz4==4.3.3
opentelemetry-api==1.29.0
opentelemetry-exporter-otlp==1.29.0
opentelemetry-exporter-otlp-proto-common==1.29.0
opentelemetry-exporter-otlp-proto-grpc==1.29.0
opentelemetry-exporter-otlp-proto-http==1.29.0
opentelemetry-instrumentation==0.50b0
opentelemetry-instrumentation-grpc==0.50b0
opentelemetry-proto==1.29.0
opentelemetry-sdk==1.29.0
opentelemetry-semantic-conventions==0.50b0
packaging==24.2
pluggy==1.5.0
protobuf==5.29.1
pydantic==2.10.3
pydantic_core==2.27.1
pytest==8.3.4
python-dotenv==1.0.1
pytz==2024.2
requests==2.32.3
typing_extensions==4.12.2
urllib3==2.2.3
wrapt==1.17.0
zipp==3.21.0
zstandard==0.23.0
```

### Makefile

A Makefile can simplify common tasks like generating protos, running tests, formatting code:

```makefile
PROTOC = python -m grpc_tools.protoc
PROTOS_PATH = protos
OUT_PATH = .

.PHONY: generate-protos
generate-protos:
	$(PROTOC) -I=$(PROTOS_PATH) --python_out=$(OUT_PATH) --grpc_python_out=$(OUT_PATH) $(PROTOS_PATH)/myservice.proto

.PHONY: test
test:
	pytest --asyncio-mode=auto

.PHONY: format
format:
	black .
	isort .
	mypy .
```

## Protobuf Definition

`protos/myservice.proto` defines your service contract. Let’s assume a `UserService`:
