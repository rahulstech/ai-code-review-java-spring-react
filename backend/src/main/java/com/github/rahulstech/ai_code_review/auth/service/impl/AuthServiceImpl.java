package com.github.rahulstech.ai_code_review.auth.service.impl;

import com.github.rahulstech.ai_code_review.auth.dto.AuthResponse;
import com.github.rahulstech.ai_code_review.auth.dto.LogInRequest;
import com.github.rahulstech.ai_code_review.auth.dto.RegisterRequest;
import com.github.rahulstech.ai_code_review.auth.dto.ResetPasswordRequest;
import com.github.rahulstech.ai_code_review.auth.model.UserEntity;
import com.github.rahulstech.ai_code_review.auth.security.TokenBody;
import com.github.rahulstech.ai_code_review.auth.security.UserPrincipal;
import com.github.rahulstech.ai_code_review.auth.repository.UserRepository;
import com.github.rahulstech.ai_code_review.auth.service.AuthService;
import com.github.rahulstech.ai_code_review.auth.service.JWTService;
import com.github.rahulstech.ai_code_review.common.exception.HttpException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserRepository userRepository;

    private final JWTService jwtService;

    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    @Override
    @Transactional
    public AuthResponse register(RegisterRequest body) {
        // check user with email already exist and throw
        if (userRepository.existsByEmail(body.email())) {
           throw HttpException.conflict("user already exists");
        }

        var passwordHash = passwordEncoder.encode(body.password());
        UserEntity user = UserEntity.builder()
                .id(UUID.randomUUID().toString())
                .email(body.email())
                .passwordHash(passwordHash)
                .displayName(body.displayName())
                .build();
        userRepository.saveAndFlush(user);

        String authToken = buildAuthToken(user);

        return buildAuthResponse(authToken, user);
    }

    @Override
    public AuthResponse login(LogInRequest body) {
        var email =  body.email();
        var password = body.password();

        UserEntity user = userRepository.findByEmail(email)
                .orElseThrow(()-> HttpException.unauthorized("invalid email and/or password"));

        if (!passwordEncoder.matches(password, user.getPasswordHash())) {
            throw HttpException.unauthorized("incorrect email and/or password");
        }

        String authToken = buildAuthToken(user);

        return buildAuthResponse(authToken, user);
    }

    @Override
    @Transactional
    public void resetPassword(UserPrincipal principal, ResetPasswordRequest body) {
        var email = principal.email();
        var currentPassword = body.currentPassword();
        var newPassword = body.newPassword();

        UserEntity user = userRepository.findByEmail(email).orElseThrow();

        if (!passwordEncoder.matches(currentPassword, user.getPasswordHash())) {
            throw HttpException.forbidden("incorrect current password");
        }

        var passwordHash = passwordEncoder.encode(newPassword);
        user.setPasswordHash(passwordHash);

        userRepository.saveAndFlush(user);
    }


    private String buildAuthToken(UserEntity user) {
        var id = user.getId();
        var email = user.getEmail();
        var body = new TokenBody(id,email);
        return jwtService.generateToken(body);
    }

    private AuthResponse buildAuthResponse(String authToken, UserEntity user) {
        return AuthResponse.builder()
                .authToken(authToken)
                .userDisplayName(user.getDisplayName())
                .userEmail(user.getEmail())
                .build();
    }
}
