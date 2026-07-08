package com.github.rahulstech.ai_code_review.common.exception;

import jakarta.servlet.http.HttpServletRequest;
import org.jspecify.annotations.NonNull;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

@ControllerAdvice
public class GlobalErrorHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalErrorHandler.class);


    @ExceptionHandler(HttpException.class)
    public ResponseEntity<@NonNull ErrorResponse> handleHttpException(HttpException ex, HttpServletRequest req) {
        if (ex.status.is5xxServerError()) {
            log.error("http server error", ex);
        }
        else {
            log.info("http error");
        }

        var errorResponse = new ErrorResponse.SimpleError(ex.getMessage());

        return ResponseEntity.status(ex.status).body(errorResponse);
    }

    @ExceptionHandler(Throwable.class)
    public ResponseEntity<@NonNull ErrorResponse> handleUnhandledException(Throwable ex, HttpServletRequest req) {
        log.error("unhandled error occurred", ex);

        var errorResponse = new ErrorResponse.SimpleError("unable to process request due to server side error");

        return ResponseEntity.internalServerError().body(errorResponse);
    }
}
