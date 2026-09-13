package com.classsync.app.domain.model

/** Shared state contract for API-backed Compose screens. */
sealed interface UiState<out T> {
    data object Loading : UiState<Nothing>
    data class Content<T>(val value: T) : UiState<T>
    data class Error(val message: String) : UiState<Nothing>
}
