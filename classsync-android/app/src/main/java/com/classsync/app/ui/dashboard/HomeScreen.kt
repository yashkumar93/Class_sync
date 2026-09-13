package com.classsync.app.ui.dashboard

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.classsync.app.data.remote.dto.AttendanceSessionDto
import com.classsync.app.ui.components.ErrorState
import com.classsync.app.ui.components.LoadingSkeleton
import com.google.accompanist.swiperefresh.SwipeRefresh
import com.google.accompanist.swiperefresh.rememberSwipeRefreshState

@Composable
fun HomeScreen(
    role: String,
    state: HomeState,
    onRefresh: () -> Unit,
    onOpen: (String) -> Unit,
    onOpenSection: (Int) -> Unit,
    onReportAbsence: (Int) -> Unit,
    onGenerateOtp: (Int) -> Unit,
) {
    LaunchedEffect(role) { onRefresh() }
    val moduleLabels =
        (if (role == "student") listOf("Attendance", "Assignments") else if (role == "faculty") listOf("Assignments", "Absences") else emptyList()) +
            listOf("Notifications", "Timetable") +
            (if (role != "student") listOf("Risk Flags") else emptyList()) +
            (if (role == "admin") listOf("Admin panel") else emptyList())
    Scaffold(topBar = { TopAppBar(title = { Text(state.title.ifBlank { "ClassSync" }) }) }) { padding ->
        SwipeRefresh(
            state = rememberSwipeRefreshState(state.loading),
            onRefresh = onRefresh,
            modifier = Modifier.padding(padding),
        ) {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                if (state.loading) item { LoadingSkeleton() }
                state.error?.let { item { ErrorState(it, onRefresh) } }
                state.generatedOtp?.let { item { OtpCard(it) } }
                items(state.lines) { line -> Card { Text(line, Modifier.padding(16.dp)) } }
                if (role == "faculty") items(state.facultySlots) { item ->
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                        OutlinedButton(onClick = { onGenerateOtp(item.slot.id) }, modifier = Modifier.weight(1f)) { Text("Generate OTP") }
                        TextButton(onClick = { onReportAbsence(item.slot.id) }, modifier = Modifier.weight(1f)) { Text("Report absence") }
                    }
                }
                if (role == "faculty") {
                    item { Text("My sections", style = MaterialTheme.typography.titleMedium) }
                    items(state.sections) { section ->
                        OutlinedButton(onClick = { onOpenSection(section.id) }, modifier = Modifier.fillMaxWidth()) {
                            Text("Attendance · ${section.course.code} Section ${section.name}")
                        }
                    }
                }
                item { Spacer(Modifier.height(8.dp)); Text("Modules", style = MaterialTheme.typography.titleMedium) }
                items(moduleLabels) { label ->
                    Card(modifier = Modifier.fillMaxWidth().clickable { onOpen(label) }) { Text(label, Modifier.padding(18.dp)) }
                }
            }
        }
    }
}

@Composable
private fun OtpCard(session: AttendanceSessionDto) = Card(
    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
) {
    Column(Modifier.padding(20.dp)) {
        Text("Attendance code", style = MaterialTheme.typography.titleMedium)
        Text(session.otpCode ?: "", style = MaterialTheme.typography.displayLarge)
        Text("Valid for ${session.remainingSeconds} seconds")
    }
}
