package com.classsync.app.ui.absence

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun AbsenceScreen(state: AbsenceState, onLoad: () -> Unit, onAccept: (Int) -> Unit, onDecline: (Int) -> Unit, onBack: () -> Unit) {
    LaunchedEffect(Unit) { onLoad() }
    Scaffold(topBar = { TopAppBar(title = { Text("Absences & cover") }, navigationIcon = { TextButton(onClick = onBack) { Text("Back") } }) }) { padding ->
        LazyColumn(Modifier.padding(padding).fillMaxSize(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            if (state.loading) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
            state.message?.let { item { Text(it, color = MaterialTheme.colorScheme.primary) } }
            state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
            item { Text("Incoming substitute requests", style = MaterialTheme.typography.titleMedium) }
            if (!state.loading && state.requests.isEmpty()) item { Text("No pending requests.") }
            items(state.requests) { request ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("${request.courseName} · Section ${request.sectionName}", style = MaterialTheme.typography.titleMedium)
                        Text("${request.date} · ${request.periodInfo}")
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { onAccept(request.id) }) { Text("Accept") }
                            OutlinedButton(onClick = { onDecline(request.id) }) { Text("Decline") }
                        }
                    }
                }
            }
            item { Text("My reported absences", style = MaterialTheme.typography.titleMedium) }
            items(state.absences) { absence -> Card(Modifier.fillMaxWidth()) { Text("${absence.date} · ${absence.timetableSlot?.section?.course?.code ?: "Class"} · ${absence.statusDisplay}", Modifier.padding(16.dp)) } }
            item { Text("Substitution history", style = MaterialTheme.typography.titleMedium) }
            items(state.history) { record -> Text("${record.date} · ${record.courseName} · ${record.originalFaculty} → ${record.substituteFaculty?.fullName ?: ""}") }
        }
    }
}
