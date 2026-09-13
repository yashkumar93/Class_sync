package com.classsync.app.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.classsync.app.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

data class LoginState(val loading: Boolean = false, val role: String? = null, val error: String? = null)

@HiltViewModel
class LoginViewModel @Inject constructor(private val auth: AuthRepository) : ViewModel() {
    private val _state = MutableStateFlow(LoginState())
    val state: StateFlow<LoginState> = _state

    init {
        viewModelScope.launch { auth.role.first()?.let { _state.value = LoginState(role = it) } }
    }

    fun login(username: String, password: String) = viewModelScope.launch {
        if (username.isBlank() || password.isBlank()) {
            _state.value = LoginState(error = "Enter both your username and password.")
            return@launch
        }
        _state.value = LoginState(loading = true)
        runCatching { auth.login(username.trim(), password) }
            .onSuccess { _state.value = LoginState(role = it) }
            .onFailure { _state.value = LoginState(error = it.message ?: "Unable to sign in.") }
    }
}
