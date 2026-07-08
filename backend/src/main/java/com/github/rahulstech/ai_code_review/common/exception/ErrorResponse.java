package com.github.rahulstech.ai_code_review.common.exception;

import java.util.Map;

public sealed interface ErrorResponse {

    record SimpleError(
            String message
    ) implements ErrorResponse {}

    record FieldError(
            Map<String,String> reasons
    ) implements ErrorResponse {}
}
