package com.classsync.app.ui.notifications

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.classsync.app.data.repository.NotificationRepository
import com.classsync.app.data.remote.dto.NotificationDto
import com.classsync.app.data.remote.dto.RiskFlagDto
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class NotificationState(
    val loading: Boolean = true,
    val notifications: List<NotificationDto> = emptyList(),
    val risks: List<RiskFlagDto> = emptyList(),
    val message: String? = null,
    val error: String? = null,
)

@HiltViewModel
class NotificationViewModel @Inject constructor(private val repository: NotificationRepository) : ViewModel() {
    private val _state = MutableStateFlow(NotificationState())
    val state: StateFlow<NotificationState> = _state
    fun load(withRisks: Boolean) = viewModelScope.launch {
        _state.value = NotificationState()
        runCatching { repository.all() to if (withRisks) repository.riskFlags() else emptyList() }
            .onSuccess { _state.value = NotificationState(false, it.first, it.second) }
            .onFailure { _state.value = NotificationState(false, error = it.message ?: "Could not load notifications.") }
    }
    fun markAllRead() = viewModelScope.launch {
        runCatching { repository.markAllRead() }.onSuccess { _state.value = _state.value.copy(message = it.message); load(_state.value.risks.isNotEmpty()) }
    }
    fun resolveRisk(id: Int) = viewModelScope.launch {
        runCatching { repository.resolveRiskFlag(id) }.onSuccess { _state.value = _state.value.copy(message = it.message); load(true) }
    }
}
