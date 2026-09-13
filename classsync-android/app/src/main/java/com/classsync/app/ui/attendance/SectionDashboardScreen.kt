package com.classsync.app.ui.attendance

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.classsync.app.data.repository.AttendanceRepository
import com.classsync.app.data.remote.dto.SectionDashboardResponse
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SectionDashboardState(val loading: Boolean = true, val dashboard: SectionDashboardResponse? = null, val error: String? = null)

@HiltViewModel
class SectionDashboardViewModel @Inject constructor(private val repository: AttendanceRepository) : ViewModel() {
    private val _state = MutableStateFlow(SectionDashboardState())
    val state: StateFlow<SectionDashboardState> = _state
    fun load(sectionId: Int) = viewModelScope.launch {
        _state.value = SectionDashboardState()
        runCatching { repository.sectionDashboard(sectionId) }
            .onSuccess { _state.value = SectionDashboardState(false, it) }
            .onFailure { _state.value = SectionDashboardState(false, error = it.message ?: "Could not load section attendance.") }
    }
}

@Composable
fun SectionDashboardRoute(sectionId: Int, onBack: () -> Unit, viewModel: SectionDashboardViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsState()
    SectionDashboardScreen(state, { viewModel.load(sectionId) }, onBack)
}

@Composable
fun SectionDashboardScreen(state: SectionDashboardState, onLoad: () -> Unit, onBack: () -> Unit) {
    LaunchedEffect(Unit) { onLoad() }
    Scaffold(topBar = { TopAppBar(title = { Text("Section attendance") }, navigationIcon = { TextButton(onClick = onBack) { Text("Back") } }) }) { padding ->
        LazyColumn(Modifier.padding(padding).fillMaxSize(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (state.loading) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
            state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
            state.dashboard?.let { dashboard ->
                item { Text("${dashboard.section.course.code} · Section ${dashboard.section.name}", style = MaterialTheme.typography.titleMedium) }
                item { Text("Attendance threshold: ${dashboard.threshold}%") }
                items(dashboard.rows) { row ->
                    Card(Modifier.fillMaxWidth()) { Text("${row.studentName} (${row.rollNumber}) · ${row.attended}/${row.totalSessions} · ${row.percentage}%", Modifier.padding(14.dp)) }
                }
            }
        }
    }
}
