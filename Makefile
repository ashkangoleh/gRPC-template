# Makefile for Python gRPC example project

# Protobuf Definition
PROTOC = python -m grpc_tools.protoc

# Paths to protos and generated files
PROTOS = myservice.proto
# PROTOC_FLAGS = --python_out=. --grpc_python_out=. myservice.proto
OUT_PATH = .

# Rules for generating protobuf files
.PHONY: generate-protos
generate-protos:
	$(PROTOC) -I=. --python_out=$(OUT_PATH) --grpc_python_out=$(OUT_PATH) $(PROTOC_FLAGS) $(PROTOS)

# Rules for running tests
.PHONY: test
test:
	pytest --asyncio-mode=auto


# .PHONY: format
# format:
# 	black .
# 	isort .
# 	mypy .
