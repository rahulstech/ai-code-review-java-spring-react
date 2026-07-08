package com.github.rahulstech.ai_code_review.auth.service;

import com.github.rahulstech.ai_code_review.auth.dto.AuthResponse;
import com.github.rahulstech.ai_code_review.auth.dto.LogInRequest;
import com.github.rahulstech.ai_code_review.auth.dto.RegisterRequest;
import com.github.rahulstech.ai_code_review.auth.dto.ResetPasswordRequest;
import com.github.rahulstech.ai_code_review.auth.security.UserPrincipal;

public interface AuthService {

    AuthResponse register(RegisterRequest body);

    AuthResponse login(LogInRequest body);

    void resetPassword(UserPrincipal principal, ResetPasswordRequest body);
}
