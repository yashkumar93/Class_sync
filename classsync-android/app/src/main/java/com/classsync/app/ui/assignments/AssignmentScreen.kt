package com.classsync.app.ui.assignments

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

@Composable
fun AssignmentScreen(
    role: String,
    state: AssignmentState,
    onLoad: () -> Unit,
    onOpenSubmissions: (Int) -> Unit,
    onSubmit: (Int, MultipartBody.Part) -> Unit,
    onBack: () -> Unit,
) {
    val context = LocalContext.current
    var selectedAssignmentId by remember { mutableStateOf<Int?>(null) }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        val assignmentId = selectedAssignmentId
        if (uri != null && assignmentId != null) uri.toMultipartPart(context)?.let { onSubmit(assignmentId, it) }
    }
    LaunchedEffect(role) { onLoad() }
    Scaffold(topBar = { TopAppBar(title = { Text("Assignments") }, navigationIcon = { TextButton(onClick = onBack) { Text("Back") } }) }) { padding ->
        LazyColumn(Modifier.padding(padding).fillMaxSize(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            if (state.loading) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
            state.message?.let { item { Text(it, color = MaterialTheme.colorScheme.primary) } }
            state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
            if (role == "student") items(state.studentItems) { item ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(item.assignment.title, style = MaterialTheme.typography.titleMedium)
                        Text(item.assignment.section?.course?.code ?: "")
                        Text(if (item.submission == null) "Not submitted" else if (item.submission.isLate) "Submitted late" else "Submitted")
                        if (!item.isPastDue || item.submission == null) Button(onClick = { selectedAssignmentId = item.assignment.id; picker.launch("*/*") }) { Text(if (item.submission == null) "Choose file & submit" else "Replace submission") }
                    }
                }
            } else items(state.facultyItems) { assignment ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(assignment.title, style = MaterialTheme.typography.titleMedium)
                        Text("${assignment.submissionCount}/${assignment.totalStudents} submitted")
                        OutlinedButton(onClick = { onOpenSubmissions(assignment.id) }) { Text("View submissions") }
                    }
                }
            }
            state.submissions?.let { dashboard ->
                item { Text("Submission dashboard · ${dashboard.assignment.title}", style = MaterialTheme.typography.titleMedium) }
                item { Text("On time: ${dashboard.onTime.size} · Late: ${dashboard.late.size} · Missing: ${dashboard.missingStudents.size}") }
                items(dashboard.missingStudents) { Text("Missing: ${it.fullName}") }
            }
        }
    }
}

private fun Uri.toMultipartPart(context: android.content.Context): MultipartBody.Part? {
    val bytes = context.contentResolver.openInputStream(this)?.use { it.readBytes() } ?: return null
    val contentType = context.contentResolver.getType(this)?.toMediaTypeOrNull()
    val body = bytes.toRequestBody(contentType)
    return MultipartBody.Part.createFormData("file", "submission", body)
}
