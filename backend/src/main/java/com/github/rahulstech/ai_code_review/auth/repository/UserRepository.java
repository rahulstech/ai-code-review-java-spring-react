package com.github.rahulstech.ai_code_review.auth.repository;

import com.github.rahulstech.ai_code_review.auth.model.UserEntity;
import org.jspecify.annotations.NonNull;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<@NonNull UserEntity, @NonNull String> {

    Optional<@NonNull UserEntity> findByEmail(@NonNull String email);

    boolean existsByEmail(@NonNull String email);
}
