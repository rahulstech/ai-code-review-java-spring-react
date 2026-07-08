package com.github.rahulstech.ai_code_review.common.exception;

import org.springframework.http.HttpStatus;

public class HttpException extends RuntimeException {

    public final HttpStatus status;

    public HttpException(int status) {
        this(status,null,null);
    }

    public HttpException(int status, String message) {
        this(status,message,null);
    }

    public HttpException(int status, String message, Throwable cause) {
        super(message, cause);
        this.status = HttpStatus.valueOf(status);
    }

    public static HttpException badRequest(String message) {
        return new HttpException(400, message);
    }

    public static HttpException unauthorized(String message) {
        return new HttpException(401, message);
    }

    public static HttpException forbidden(String message) {
        return new HttpException(403, message);
    }

    public static HttpException notFound(String message) {
        return new HttpException(404, message);
    }

    public static HttpException conflict(String message) {
        return new HttpException(409, message);
    }

    public static HttpException serverError(String message) {
        return new HttpException(500, message);
    }

    public static HttpException serverError(String message, Throwable cause) {
        return new HttpException(500, message, cause);
    }
}
