package com.classsync.app.ui.absence

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.classsync.app.data.repository.AbsenceRepository
import com.classsync.app.data.remote.dto.AbsenceReportDto
import com.classsync.app.data.remote.dto.SubstituteRequestDto
import com.classsync.app.data.remote.dto.SubstitutionRecordDto
import com.classsync.app.data.remote.dto.ReportAbsenceRequest
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AbsenceState(
    val loading: Boolean = true,
    val absences: List<AbsenceReportDto> = emptyList(),
    val requests: List<SubstituteRequestDto> = emptyList(),
    val history: List<SubstitutionRecordDto> = emptyList(),
    val message: String? = null,
    val error: String? = null,
)

@HiltViewModel
class AbsenceViewModel @Inject constructor(private val repository: AbsenceRepository) : ViewModel() {
    private val _state = MutableStateFlow(AbsenceState())
    val state: StateFlow<AbsenceState> = _state

    fun load() = viewModelScope.launch {
        _state.value = AbsenceState()
        runCatching { Triple(repository.myAbsences(), repository.pendingRequests(), repository.history()) }
            .onSuccess { _state.value = AbsenceState(false, it.first, it.second, it.third) }
            .onFailure { _state.value = AbsenceState(false, error = it.message ?: "Could not load absence data.") }
    }

    fun accept(id: Int) = respond(id, true)
    fun decline(id: Int) = respond(id, false)
    fun report(slotId: Int, date: String, reason: String, onComplete: () -> Unit) = viewModelScope.launch {
        runCatching { repository.report(ReportAbsenceRequest(slotId, date, reason)) }
            .onSuccess { _state.value = _state.value.copy(message = it.message); onComplete() }
            .onFailure { _state.value = _state.value.copy(error = it.message ?: "Could not report absence.") }
    }
    private fun respond(id: Int, accepted: Boolean) = viewModelScope.launch {
        runCatching { if (accepted) repository.accept(id) else repository.decline(id) }
            .onSuccess { _state.value = _state.value.copy(message = it.message); load() }
            .onFailure { _state.value = _state.value.copy(error = it.message ?: "Could not update request.") }
    }
}
