LAMBDA_FUNCTION_NAME := lambda_quotes
ZIP_PKG := deployment_package.zip
ZIP_LAYER_PKG := layer_package.zip
TMP_PKG_DIR := /tmp/lima/python

.PHONY: update-function
update-function: $(ZIP_PKG)
	aws lambda update-function-code \
		--function-name $(LAMBDA_FUNCTION_NAME) \
		--zip-file fileb://$<

$(ZIP_PKG): aws_lambda
	cd aws_lambda && zip -9 $@ lambda_function.py
	mv aws_lambda/$@ .

$(ZIP_LAYER_PKG):
	if [ -d $(TMP_PKG_DIR) ]; then rm -r $(TMP_PKG_DIR); fi
	lima pip3 install yfinance --upgrade --no-cache-dir --target $(TMP_PKG_DIR)
	find $(TMP_PKG_DIR) -type d -name "__pycache__"  | xargs -I _ rm -r _
	cd $(TMP_PKG_DIR)/.. && zip -9 -r /tmp/$@ python
	mv /tmp/$@ .

.PHONY: update-layer
update-layer: $(ZIP_LAYER_PKG)
	aws lambda publish-layer-version \
		--layer-name yfinance \
		--zip-file fileb://$<
	@echo "Delete the old layer version with 'delete-layer-version --version-number'" \
	      " or via the console."
	@echo "Update the function to use the updated version with" \
	      " 'update-function-configuration --layers LayerVersionArn' or via the console."

clean:
	rm -f $(ZIP_PKG) $(ZIP_LAYER_PKG)

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
