package com.classsync.app.ui.features

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun FeatureScreen(title: String, role: String, state: FeatureState, onLoad: () -> Unit, onBack: () -> Unit) {
    LaunchedEffect(title, role) { onLoad() }
    Scaffold(topBar = { TopAppBar(title = { Text(title) }, navigationIcon = { TextButton(onClick = onBack) { Text("Back") } }) }) { padding ->
        LazyColumn(Modifier.padding(padding).fillMaxSize(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            if (state.loading) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
            state.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
            if (!state.loading && state.rows.isEmpty()) item { Text("Nothing to show yet.") }
            items(state.rows) { Card(Modifier.fillMaxWidth()) { Text(it, Modifier.padding(16.dp)) } }
        }
    }
}
