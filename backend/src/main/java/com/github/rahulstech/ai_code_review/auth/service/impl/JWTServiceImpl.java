package com.github.rahulstech.ai_code_review.auth.service.impl;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.github.rahulstech.ai_code_review.auth.security.TokenBody;
import com.github.rahulstech.ai_code_review.auth.service.JWTService;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.Date;

@Service
public class JWTServiceImpl implements JWTService {

    private static final long AUTH_TOKEN_EXPIRE_AFTER_MILLIS = 24 * 3600 * 1000; // one day

    private final Algorithm algorithm;

    public JWTServiceImpl(@Value("${ai_code_review.auth.jwt.secret}") String jwtSecret) {
        this.algorithm = Algorithm.HMAC256(jwtSecret);
    }

    @Override
    public String generateToken(TokenBody body) {
        long expirationMs = System.currentTimeMillis() + AUTH_TOKEN_EXPIRE_AFTER_MILLIS;
        Date expiresAt = new Date(expirationMs);

        // Symmetric signing using HMAC256
        return JWT.create()
                .withSubject(body.subject())
                .withClaim("email", body.email())
                .withExpiresAt(expiresAt)
                .sign(algorithm);
    }

    @Override
    public TokenBody verifyToken(String token) {
        JWTVerifier verifier = JWT.require(algorithm).build();
        DecodedJWT decodedJWT = verifier.verify(token);
        String subject = decodedJWT.getSubject();
        String email = decodedJWT.getClaim("email").asString();
        return TokenBody.builder()
                .subject(subject)
                .email(email)
                .build();
    }
}
