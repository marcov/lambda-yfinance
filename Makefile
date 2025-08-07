LAMBDA_FUNCTION_NAME := lambda_quotes
# The CPU architecture of the machine running the AWS lambda function.
LAMBDA_ARCH ?= arm64
LAMBDA_FUNCTION_ZIPFILE := deployment_package.zip

# Python packages required to run the lambda
PYTHON_PKGS_ZIPFILE_LAYER := layer_package_$(LAMBDA_ARCH).zip

# Root dir where the Python packages gets populated during build
PIP_INSTALL_TARGET_DIR := /tmp/lima/python-pkg-$(LAMBDA_FUNCTION_NAME)/python

# Support creating the Python layer on macOS
ifeq (Darwin,$(shell uname -s))
  UID := $(shell id -u)
  GID := $(shell id -g)
  PIP3_HAL_CMD := lima podman run --arch $(LAMBDA_ARCH) --rm -it -v $(PIP_INSTALL_TARGET_DIR):$(PIP_INSTALL_TARGET_DIR) -u $(UID):$(GID) python:3.13
endif

# Only update the function code.
.PHONY: update-function
update-function: $(LAMBDA_FUNCTION_ZIPFILE)
	aws lambda update-function-code \
		--function-name $(LAMBDA_FUNCTION_NAME) \
		--zip-file fileb://$<

$(LAMBDA_FUNCTION_ZIPFILE): aws_lambda
	cd aws_lambda && zip -9 $@ lambda_function.py
	mv aws_lambda/$@ .

$(PYTHON_PKGS_ZIPFILE_LAYER): $(PIP_INSTALL_TARGET_DIR)
	rm -f $@
	cd $(PIP_INSTALL_TARGET_DIR)/.. && zip -9 -r /tmp/$@ $(shell basename $(PIP_INSTALL_TARGET_DIR))
	mv /tmp/$@ .

.PHONY: $(PIP_INSTALL_TARGET_DIR)
$(PIP_INSTALL_TARGET_DIR):
	if [ -d $(PIP_INSTALL_TARGET_DIR) ]; then rm -r $(PIP_INSTALL_TARGET_DIR); fi
	mkdir -p $(PIP_INSTALL_TARGET_DIR)
	$(PIP3_HAL_CMD) pip3 install yfinance==0.2.65 --upgrade --no-cache-dir --target $(PIP_INSTALL_TARGET_DIR)
	find $(PIP_INSTALL_TARGET_DIR) -type d -name "__pycache__"  | xargs -I _ rm -r _
# Patches were for 0.2.28, 0.2.65 does not need it
#	patch -p1 -d $(PIP_INSTALL_TARGET_DIR)/yfinance < yfinance-patches.diff

# Update the lambda layer containing all the python modules. This is needed
# when changing any of the modules
.PHONY: update-layer
update-layer: $(PYTHON_PKGS_ZIPFILE_LAYER)
	aws lambda publish-layer-version \
		--layer-name yfinance \
		--zip-file fileb://$<
	@echo "Delete the old layer version with\n" \
		  "> aws lambda delete-layer-version --layer-name yfinance --version-number VERSION" \
		  "Where VERSION is n-1 from the publish command above (or obtained via  aws lambda list-layer-versions --layer-name yfinance)"
	@echo "Update the function to use the updated version with\n" \
  		"> aws update-function-configuration --function-name $(LAMBDA_FUNCTION_NAME) --layers arn:aws:lambda:REGION::layer:yfinance:VERSION # (i.e. LayerVersionArn from above)\n" \
	    "or via the console."

clean:
	rm -f $(LAMBDA_FUNCTION_ZIPFILE) $(PYTHON_PKGS_ZIPFILE_LAYER)
	if [ -d $(PIP_INSTALL_TARGET_DIR) ]; then rm -r $(PIP_INSTALL_TARGET_DIR); fi

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
