LAMBDA_FUNCTION_NAME := lambda_quotes
ZIP_PKG := deployment_package.zip

.PHONY: lambda-upload
lambda-upload: $(ZIP_PKG)
	aws lambda update-function-code \
		--function-name $(LAMBDA_FUNCTION_NAME) \
		--zip-file fileb://$<

$(ZIP_PKG): aws_lambda
	cd aws_lambda/package && zip -9 -r ../../$@ .
	cd aws_lambda && zip -9 ../$@ lambda_function.py

clean:
	rm $(ZIP_PKG)
