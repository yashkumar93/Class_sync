package com.classsync.app.ui.navigation

import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable

@Composable
fun BottomNavBar(selected: String, onSelect: (String) -> Unit) {
    NavigationBar {
        listOf("Home", "Notifications", "Timetable").forEach { label ->
            NavigationBarItem(
                selected = selected == label,
                onClick = { onSelect(label) },
                icon = {},
                label = { Text(label) },
            )
        }
    }
}
