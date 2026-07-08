package com.github.rahulstech.ai_code_review.auth.security;

import lombok.Builder;

@Builder
public record TokenBody(
        String subject,
        String email
) {}
