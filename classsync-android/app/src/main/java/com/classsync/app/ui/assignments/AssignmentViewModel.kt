package com.classsync.app.ui.assignments

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.classsync.app.data.repository.AssignmentRepository
import com.classsync.app.data.remote.dto.AssignmentDto
import com.classsync.app.data.remote.dto.StudentAssignmentDto
import com.classsync.app.data.remote.dto.SubmissionDashboardResponse
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import okhttp3.MultipartBody
import javax.inject.Inject

data class AssignmentState(
    val loading: Boolean = true,
    val studentItems: List<StudentAssignmentDto> = emptyList(),
    val facultyItems: List<AssignmentDto> = emptyList(),
    val submissions: SubmissionDashboardResponse? = null,
    val message: String? = null,
    val error: String? = null,
)

@HiltViewModel
class AssignmentViewModel @Inject constructor(private val repository: AssignmentRepository) : ViewModel() {
    private val _state = MutableStateFlow(AssignmentState())
    val state: StateFlow<AssignmentState> = _state

    fun load(role: String) = viewModelScope.launch {
        _state.value = AssignmentState()
        if (role == "student") {
            runCatching { repository.forStudent() }
                .onSuccess { _state.value = AssignmentState(loading = false, studentItems = it) }
                .onFailure { _state.value = AssignmentState(loading = false, error = it.message ?: "Could not load assignments.") }
        } else {
            runCatching { repository.forFaculty() }
                .onSuccess { _state.value = AssignmentState(loading = false, facultyItems = it) }
                .onFailure { _state.value = AssignmentState(loading = false, error = it.message ?: "Could not load assignments.") }
        }
    }

    fun loadSubmissions(assignmentId: Int) = viewModelScope.launch {
        runCatching { repository.submissions(assignmentId) }
            .onSuccess { _state.value = _state.value.copy(submissions = it) }
            .onFailure { _state.value = _state.value.copy(error = it.message ?: "Could not load submissions.") }
    }

    fun submit(assignmentId: Int, file: MultipartBody.Part) = viewModelScope.launch {
        runCatching { repository.submit(assignmentId, file) }
            .onSuccess { _state.value = _state.value.copy(message = it.message); load("student") }
            .onFailure { _state.value = _state.value.copy(error = it.message ?: "Could not upload submission.") }
    }
}
