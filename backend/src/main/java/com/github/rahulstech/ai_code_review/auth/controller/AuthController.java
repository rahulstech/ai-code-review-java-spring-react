package com.github.rahulstech.ai_code_review.auth.controller;

import com.github.rahulstech.ai_code_review.auth.dto.AuthResponse;
import com.github.rahulstech.ai_code_review.auth.dto.LogInRequest;
import com.github.rahulstech.ai_code_review.auth.dto.RegisterRequest;
import com.github.rahulstech.ai_code_review.auth.dto.ResetPasswordRequest;
import com.github.rahulstech.ai_code_review.auth.security.UserPrincipal;
import com.github.rahulstech.ai_code_review.auth.service.AuthService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.jspecify.annotations.NonNull;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    public ResponseEntity<@NonNull AuthResponse> register(@Valid @RequestBody RegisterRequest body) {
        var res = authService.register(body);
        return ResponseEntity.status(HttpStatus.CREATED).body(res);
    }

    @PostMapping("/login")
    public AuthResponse login(@Valid @RequestBody LogInRequest body) {
        return authService.login(body);
    }

    @PostMapping("/reset-password")
    public void resetPassword(Authentication auth, @Valid @RequestBody ResetPasswordRequest body) {
        UserPrincipal principal = (UserPrincipal) auth.getPrincipal();
        authService.resetPassword(principal, body);
    }
}
