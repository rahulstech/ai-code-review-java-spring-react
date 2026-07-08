package com.github.rahulstech.ai_code_review.auth.dto;

import lombok.Builder;

@Builder
public record AuthResponse(
   String authToken,
   String userDisplayName,
   String userEmail
) {}
