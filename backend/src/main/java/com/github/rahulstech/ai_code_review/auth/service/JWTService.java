package com.github.rahulstech.ai_code_review.auth.service;

import com.github.rahulstech.ai_code_review.auth.security.TokenBody;

public interface JWTService {

    String generateToken(TokenBody body);

    TokenBody verifyToken(String token);
}
