package com.classsync.app.ui.attendance

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.classsync.app.ui.components.EmptyState
import com.classsync.app.ui.components.ErrorState
import com.classsync.app.ui.components.LoadingSkeleton

@Composable
fun AttendanceScreen(state: AttendanceState, onLoad: () -> Unit, onSubmit: (Int, String) -> Unit, onBack: () -> Unit) {
    var code by remember { mutableStateOf("") }
    val haptics = LocalHapticFeedback.current
    LaunchedEffect(Unit) { onLoad() }
    Scaffold(topBar = { TopAppBar(title = { Text("Attendance") }, navigationIcon = { TextButton(onClick = onBack) { Text("Back") } }) }) { padding ->
        LazyColumn(
            Modifier.padding(padding).fillMaxSize(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            if (state.loading) item { LoadingSkeleton() }
            state.message?.let { item { Text(it, color = MaterialTheme.colorScheme.primary) } }
            state.error?.let { item { ErrorState(it, onLoad) } }
            item { Text("My attendance", style = MaterialTheme.typography.titleMedium) }
            if (!state.loading && state.summary.isEmpty()) item { EmptyState("Attendance will appear after your first class.") }
            items(state.summary) { summary ->
                val color = when {
                    summary.percentage >= 75 -> MaterialTheme.colorScheme.primary
                    summary.percentage >= 60 -> MaterialTheme.colorScheme.tertiary
                    else -> MaterialTheme.colorScheme.error
                }
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("${summary.courseCode} · ${summary.percentage}%", color = color, style = MaterialTheme.typography.titleMedium)
                        LinearProgressIndicator(progress = { (summary.percentage / 100).toFloat() }, modifier = Modifier.fillMaxWidth(), color = color)
                        Text("${summary.attended} of ${summary.totalSessions} sessions attended")
                    }
                }
            }
            item { Text("Today's classes", style = MaterialTheme.typography.titleMedium) }
            if (!state.loading && state.sessions.isEmpty()) item { EmptyState("No classes are scheduled for today.") }
            items(state.sessions) { session ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("${session.slot.section.course.code} · Period ${session.slot.periodNumber}", style = MaterialTheme.typography.titleMedium)
                        Text(if (session.alreadyMarked) "Attendance marked" else if (session.isActive) "OTP session active" else "No active OTP session")
                        if (session.isActive && !session.alreadyMarked) {
                            OutlinedTextField(
                                value = code,
                                onValueChange = { code = it.filter(Char::isDigit).take(6) },
                                label = { Text("6-digit OTP") },
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                                singleLine = true,
                            )
                            Button(onClick = { haptics.performHapticFeedback(HapticFeedbackType.LongPress); onSubmit(session.slot.id, code) }, enabled = code.length == 6) {
                                Text("Mark attendance")
                            }
                        }
                    }
                }
            }
        }
    }
}
