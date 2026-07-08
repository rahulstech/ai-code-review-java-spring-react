package com.github.rahulstech.ai_code_review.auth.dto;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ResetPasswordRequest(
        @NotBlank(message = "currentPassword is required")
        String currentPassword,

        @NotBlank(message = "newPassword is required")
        @Size(min = 8, max = 12, message = "password length must between between 8 and 12 charters")
        String newPassword
) {

    @AssertTrue(message = "characters allowed for password are a-zA-Z0-9 and $@-_")
    public boolean isPasswordCharactersAccepted() {
        // TODO: check characters of password
        return true;
    }
}
