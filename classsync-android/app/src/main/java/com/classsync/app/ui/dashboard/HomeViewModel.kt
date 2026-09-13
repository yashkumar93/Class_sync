package com.classsync.app.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.classsync.app.data.remote.ApiService
import com.classsync.app.data.remote.dto.*
import com.classsync.app.service.FcmTokenRegistrar
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import java.time.LocalDate
import javax.inject.Inject

data class HomeState(
    val loading: Boolean = true,
    val title: String = "",
    val lines: List<String> = emptyList(),
    val facultySlots: List<TodaySlotWithSession> = emptyList(),
    val sections: List<SectionDto> = emptyList(),
    val generatedOtp: AttendanceSessionDto? = null,
    val error: String? = null,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val api: ApiService,
    private val fcmTokenRegistrar: FcmTokenRegistrar,
) : ViewModel() {
    private val _state = MutableStateFlow(HomeState())
    val state: StateFlow<HomeState> = _state

    fun load(role: String) = viewModelScope.launch {
        fcmTokenRegistrar.registerCurrentToken()
        _state.value = HomeState(loading = true)
        runCatching {
            when (role) {
                "faculty" -> api.facultyDashboard().let { d -> HomeState(false, "Faculty dashboard", d.todaySlots.map { "${it.slot.section.course.code} · ${it.slot.dayDisplay} P${it.slot.periodNumber}" }, d.todaySlots, d.sections) }
                "student" -> api.studentDashboard().let { d -> HomeState(false, "Student dashboard", d.attendanceSummary.map { "${it.courseCode}: ${it.percentage}% attendance" } + d.upcomingAssignments.map { "Due: ${it.title}" }) }
                else -> api.adminDashboard().let { d -> HomeState(false, "Admin dashboard", listOf("${d.totalStudents} students", "${d.totalFaculty} faculty", "${d.activeRiskFlags} active risk flags")) }
            }
        }.onSuccess { _state.value = it }.onFailure { _state.value = HomeState(loading = false, error = it.message ?: "Could not load dashboard.") }
    }

    fun generateOtp(slotId: Int) = viewModelScope.launch {
        runCatching { api.generateOtp(GenerateOtpRequest(slotId, LocalDate.now().toString())) }
            .onSuccess { _state.value = _state.value.copy(generatedOtp = it) }
            .onFailure { _state.value = _state.value.copy(error = it.message ?: "Could not generate OTP.") }
    }
}
