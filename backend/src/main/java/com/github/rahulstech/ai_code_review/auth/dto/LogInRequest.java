package com.github.rahulstech.ai_code_review.auth.dto;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record LogInRequest(
        @NotBlank(message = "email is required")
        @Email(message = "invalid email")
        String email,

        @NotBlank(message = "password is required")
        @Size(min = 8, max = 12, message = "password length must between between 8 and 12 charters")
        String password
) {
    @AssertTrue(message = "characters allowed for password are a-zA-Z0-9 and $@-_")
    public boolean isPasswordCharactersAccepted() {
        // TODO: check characters of password
        return true;
    }
}
