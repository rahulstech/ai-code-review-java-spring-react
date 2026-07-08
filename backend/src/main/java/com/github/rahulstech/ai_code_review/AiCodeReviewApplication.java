package com.github.rahulstech.ai_code_review;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.security.autoconfigure.UserDetailsServiceAutoConfiguration;

@SpringBootApplication(
        exclude = {
                UserDetailsServiceAutoConfiguration.class
        }
)
public class AiCodeReviewApplication {

	public static void main(String[] args) {
		SpringApplication.run(AiCodeReviewApplication.class, args);
	}

}
