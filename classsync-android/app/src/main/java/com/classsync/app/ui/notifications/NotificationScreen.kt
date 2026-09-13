package com.classsync.app.ui.notifications

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun NotificationScreen(role: String, state: NotificationState, onLoad: () -> Unit, onMarkAllRead: () -> Unit, onResolveRisk: (Int) -> Unit, onBack: () -> Unit) {
    LaunchedEffect(role) { onLoad() }
    Scaffold(topBar = { TopAppBar(title = { Text("Notifications") }, navigationIcon = { TextButton(onClick = onBack) { Text("Back") } }, actions = { TextButton(onClick = onMarkAllRead) { Text("Read all") } }) }) { padding ->
        LazyColumn(Modifier.padding(padding).fillMaxSize(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            if (state.loading) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
            state.message?.let { item { Text(it, color = MaterialTheme.colorScheme.primary) } }
            state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
            items(state.notifications) { notification -> Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp)) { Text(notification.typeDisplay, style = MaterialTheme.typography.labelLarge); Text(notification.message) } } }
            if (state.risks.isNotEmpty()) item { Text("Active risk flags", style = MaterialTheme.typography.titleMedium) }
            items(state.risks) { risk -> Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp)) { Text(risk.student?.fullName ?: "Student", style = MaterialTheme.typography.titleMedium); Text(risk.reason); OutlinedButton(onClick = { onResolveRisk(risk.id) }) { Text("Resolve") } } } }
        }
    }
}
