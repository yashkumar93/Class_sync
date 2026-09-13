package com.classsync.app.ui.features

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.classsync.app.data.remote.ApiService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class FeatureState(val loading: Boolean = true, val rows: List<String> = emptyList(), val error: String? = null)

@HiltViewModel
class FeatureViewModel @Inject constructor(private val api: ApiService) : ViewModel() {
    private val _state = MutableStateFlow(FeatureState())
    val state: StateFlow<FeatureState> = _state

    fun load(feature: String, role: String) = viewModelScope.launch {
        _state.value = FeatureState()
        runCatching {
            when (feature) {
                "Assignments" -> if (role == "student") api.studentAssignments().map { "${it.assignment.title} · ${if (it.submission == null) "Not submitted" else "Submitted"}" } else api.facultyAssignments().map { "${it.title} · ${it.submissionCount}/${it.totalStudents} submitted" }
                "Absences" -> if (role == "faculty") api.myAbsences().map { "${it.date} · ${it.timetableSlot?.section?.course?.code ?: "Class"} · ${it.statusDisplay}" } else emptyList()
                "Notifications" -> api.notifications().map { "${it.typeDisplay}: ${it.message}" }
                else -> emptyList()
            }
        }.onSuccess { _state.value = FeatureState(false, it) }
            .onFailure { _state.value = FeatureState(false, error = it.message ?: "Could not load $feature.") }
    }
}
