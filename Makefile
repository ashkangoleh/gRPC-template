PROTOC = python -m grpc_tools.protoc
# PROTOS_PATH = protos
PROTOS = myservice.proto
OUT_PATH = .

.PHONY: generate-protos
generate-protos:
	$(PROTOC) -I=. --python_out=$(OUT_PATH) --grpc_python_out=$(OUT_PATH) $(PROTOC_FLAGS) $(PROTOS)

.PHONY: test
test:
	pytest --asyncio-mode=auto


# .PHONY: format
# format:
# 	black .
# 	isort .
# 	mypy .
