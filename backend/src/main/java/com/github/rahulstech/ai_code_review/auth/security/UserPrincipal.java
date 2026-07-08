package com.github.rahulstech.ai_code_review.auth.security;

public record UserPrincipal(
        String id,
        String email
) {}
