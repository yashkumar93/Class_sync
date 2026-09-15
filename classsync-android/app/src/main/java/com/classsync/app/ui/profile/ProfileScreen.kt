package com.classsync.app.ui.profile

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.classsync.app.ui.components.ErrorState
import com.classsync.app.ui.components.LoadingSkeleton

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProfileScreen(
    state: ProfileState,
    onBack: () -> Unit,
    onLogout: () -> Unit,
    onRefresh: () -> Unit
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Profile") },
                navigationIcon = {
                    IconButton(onClick = onBack) { Icon(Icons.Filled.ArrowBack, contentDescription = "Back") }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            if (state.loading && state.user == null) {
                LoadingSkeleton()
            } else if (state.error != null && state.user == null) {
                ErrorState(state.error, onRefresh)
            } else if (state.user != null) {
                val user = state.user
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            text = user.fullName.ifBlank { user.username },
                            style = MaterialTheme.typography.titleLarge
                        )
                        Text("Username: ${user.username}")
                        if (user.email.isNotBlank()) Text("Email: ${user.email}")
                        if (user.phone.isNotBlank()) Text("Phone: ${user.phone}")
                        Text("Role: ${user.role.replaceFirstChar { it.uppercase() }}")
                        
                        user.department?.let {
                            Text("Department: ${it.name} (${it.code})")
                        }
                        
                        if (user.rollNumber.isNotBlank()) {
                            Text("Roll Number: ${user.rollNumber}")
                        }
                        if (user.yearOfStudy != null) {
                            Text("Year of Study: ${user.yearOfStudy}")
                        }
                    }
                }
                
                Spacer(modifier = Modifier.weight(1f))
                
                Button(
                    onClick = onLogout,
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Log Out")
                }
            }
        }
    }
}
