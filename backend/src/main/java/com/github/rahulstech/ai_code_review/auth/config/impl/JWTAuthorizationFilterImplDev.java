package com.github.rahulstech.ai_code_review.auth.config.impl;

import com.github.rahulstech.ai_code_review.auth.config.JWTAuthorizationFilter;
import com.github.rahulstech.ai_code_review.auth.security.UserPrincipal;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.context.annotation.Profile;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetails;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
@Profile("dev")
public class JWTAuthorizationFilterImplDev extends JWTAuthorizationFilter {

    private static final String USER_ID = "b19c04be-04cf-42d5-ae57-9f7a877558a5";

    private static final String USER_EMAIL = "demo.user@example.com";

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {

        UserPrincipal principal = new UserPrincipal(USER_ID, USER_EMAIL);
        UsernamePasswordAuthenticationToken token = new UsernamePasswordAuthenticationToken(principal,  null);
        token.setDetails(new WebAuthenticationDetails(request));
        SecurityContextHolder.getContext().setAuthentication(token);

        filterChain.doFilter(request, response);
    }
}
