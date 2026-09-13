package com.classsync.app.ui.attendance

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.classsync.app.data.remote.ApiService
import com.classsync.app.data.remote.dto.AttendanceSummaryDto
import com.classsync.app.data.remote.dto.SubmitOtpRequest
import com.classsync.app.data.remote.dto.TodaySessionDto
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AttendanceState(val loading: Boolean = true, val summary: List<AttendanceSummaryDto> = emptyList(), val sessions: List<TodaySessionDto> = emptyList(), val message: String? = null, val error: String? = null)

@HiltViewModel
class AttendanceViewModel @Inject constructor(private val api: ApiService) : ViewModel() {
    private val _state = MutableStateFlow(AttendanceState())
    val state: StateFlow<AttendanceState> = _state
    fun load() = viewModelScope.launch {
        _state.value = AttendanceState()
        runCatching { api.myAttendance() to api.todaySessions() }
            .onSuccess { _state.value = AttendanceState(false, it.first, it.second) }
            .onFailure { _state.value = AttendanceState(false, error = it.message ?: "Could not load attendance.") }
    }
    fun submit(slotId: Int, code: String) = viewModelScope.launch {
        runCatching { api.submitOtp(SubmitOtpRequest(slotId, code)) }
            .onSuccess { _state.value = _state.value.copy(message = it.message); load() }
            .onFailure { _state.value = _state.value.copy(error = it.message ?: "OTP submission failed.") }
    }
}
