LAMBDA_ARCH ?= arm64
LAMBDA_FUNCTION_NAME := lambda_quotes
ZIP_PKG := deployment_package.zip
ZIP_LAYER_PKG := layer_package_$(LAMBDA_ARCH).zip
# Root dir of the layer needs to be called python
TMP_PKG_DIR := /tmp/lima/python-pkg-$(LAMBDA_FUNCTION_NAME)/python
UID := $(shell id -u)
GID := $(shell id -g)
PIP3_HAL_CMD := lima podman run --arch $(LAMBDA_ARCH) --rm -it -v $(TMP_PKG_DIR):$(TMP_PKG_DIR) -u $(UID):$(GID) python:3.11

.PHONY: update-function
update-function: $(ZIP_PKG)
	aws lambda update-function-code \
		--function-name $(LAMBDA_FUNCTION_NAME) \
		--zip-file fileb://$<

$(ZIP_PKG): aws_lambda
	cd aws_lambda && zip -9 $@ lambda_function.py
	mv aws_lambda/$@ .

.PHONY: $(ZIP_LAYER_PKG)
$(ZIP_LAYER_PKG): $(TMP_PKG_DIR)
	rm -f $@
	cd $(TMP_PKG_DIR)/.. && zip -9 -r /tmp/$@ $(shell basename $(TMP_PKG_DIR))
	mv /tmp/$@ .

$(TMP_PKG_DIR):
	if [ -d $(TMP_PKG_DIR) ]; then rm -r $(TMP_PKG_DIR); fi
	mkdir -p $(TMP_PKG_DIR)
	$(PIP3_HAL_CMD) pip3 install yfinance==0.2.28 --upgrade --no-cache-dir --target $(TMP_PKG_DIR)
	find $(TMP_PKG_DIR) -type d -name "__pycache__"  | xargs -I _ rm -r _

.PHONY: update-layer
update-layer: $(ZIP_LAYER_PKG)
	aws lambda publish-layer-version \
		--layer-name yfinance \
		--zip-file fileb://$<
	@echo "Delete the old layer version with\n" \
		  "> aws delete-layer-version --version-number VERSION"
	@echo "Update the function to use the updated version with\n" \
  		"> aws update-function-configuration --function-name $(LAMBDA_FUNCTION_NAME) --layers arn:aws:lambda:REGION::layer:yfinance:VERSION # (i.e. LayerVersionArn from above)\n" \
	    "or via the console."

clean:
	rm -f $(ZIP_PKG) $(ZIP_LAYER_PKG)
	if [ -d $(TMP_PKG_DIR) ]; then rm -r $(TMP_PKG_DIR); fi

.PHONY: lambda-logs
lambda-logs:
	get_log_stream() { \
		local -r log_stream_name="$$(aws logs describe-log-streams \
				--log-group-name '/aws/lambda/$(LAMBDA_FUNCTION_NAME)' \
				--query 'logStreams[*].logStreamName' | \
			jq -r '.[-1]'\
		)"; \
		aws logs get-log-events \
			--log-group-name '/aws/lambda/$(LAMBDA_FUNCTION_NAME)' \
			--log-stream-name "$${log_stream_name}" | \
			jq -r '.events | .[].message' | \
			sed '/^$$/d'; \
	}; get_log_stream
