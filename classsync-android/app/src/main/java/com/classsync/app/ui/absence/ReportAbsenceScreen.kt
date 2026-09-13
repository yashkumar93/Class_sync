package com.classsync.app.ui.absence

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import java.time.LocalDate

@Composable
fun ReportAbsenceScreen(slotId: Int, state: AbsenceState, onReport: (String, String) -> Unit, onBack: () -> Unit) {
    var date by remember { mutableStateOf(LocalDate.now().toString()) }
    var reason by remember { mutableStateOf("") }
    Scaffold(topBar = { TopAppBar(title = { Text("Report absence") }, navigationIcon = { TextButton(onClick = onBack) { Text("Back") } }) }) { padding ->
        Column(Modifier.padding(padding).padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Scheduled slot #$slotId", style = MaterialTheme.typography.titleMedium)
            OutlinedTextField(date, { date = it }, label = { Text("Date (YYYY-MM-DD)") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(reason, { reason = it }, label = { Text("Reason (optional)") }, minLines = 3, modifier = Modifier.fillMaxWidth())
            state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Button(onClick = { onReport(date, reason) }, modifier = Modifier.fillMaxWidth(), enabled = date.length == 10) { Text("Notify eligible faculty") }
        }
    }
}
