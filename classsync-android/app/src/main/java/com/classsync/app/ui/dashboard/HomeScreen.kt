package com.classsync.app.ui.dashboard

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Assignment
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.classsync.app.data.remote.dto.AttendanceSessionDto
import com.classsync.app.ui.components.AttendanceArc
import com.classsync.app.ui.components.ErrorState
import com.classsync.app.ui.components.GreetingHeader
import com.classsync.app.ui.components.LoadingSkeleton
import com.classsync.app.ui.components.ModuleCard
import com.classsync.app.ui.theme.*
import com.google.accompanist.swiperefresh.SwipeRefresh
import com.google.accompanist.swiperefresh.rememberSwipeRefreshState

// ── Module definition ────────────────────────────────────────────────────────

private data class ModuleDef(
    val label: String,
    val icon: ImageVector,
    val tint: androidx.compose.ui.graphics.Color,
)

private fun modulesFor(role: String): List<ModuleDef> = buildList {
    when (role) {
        "student" -> {
            add(ModuleDef("Attendance",    Icons.Default.BarChart,                   SemanticGreen))
            add(ModuleDef("Assignments",   Icons.AutoMirrored.Filled.Assignment,     ClassSyncBlue))
        }
        "faculty" -> {
            add(ModuleDef("Attendance",    Icons.Default.BarChart,                   SemanticGreen))
            add(ModuleDef("Assignments",   Icons.AutoMirrored.Filled.Assignment,     ClassSyncBlue))
            add(ModuleDef("Absences",      Icons.Default.EventBusy,                  SemanticAmber))
        }
    }
    add(ModuleDef("Notifications", Icons.Default.Notifications,  ClassSyncGold))
    add(ModuleDef("Timetable",     Icons.Default.CalendarMonth,  Navy500))
    add(ModuleDef("Profile",       Icons.Default.Person,         OnSurface60))
    if (role != "student") add(ModuleDef("Risk Flags", Icons.Default.Flag, SemanticRed))
    if (role == "admin")   add(ModuleDef("Admin panel", Icons.Default.AdminPanelSettings, ClassSyncBlue))
}

// ── HomeScreen ───────────────────────────────────────────────────────────────

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

    val modules = remember(role) { modulesFor(role) }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        SwipeRefresh(
            state = rememberSwipeRefreshState(state.loading),
            onRefresh = onRefresh,
            modifier = Modifier.padding(padding),
        ) {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(horizontal = 20.dp, vertical = 24.dp),
                verticalArrangement = Arrangement.spacedBy(20.dp),
            ) {
                // ── Loading / Error ──────────────────────────────────────
                if (state.loading) {
                    item { LoadingSkeleton() }
                    return@LazyColumn
                }
                state.error?.let { item { ErrorState(it, onRefresh) } }

                // ── Greeting header ──────────────────────────────────────
                item {
                    GreetingHeader(
                        name = state.title
                            .replace("Student dashboard", "")
                            .replace("Faculty dashboard", "")
                            .replace("Admin dashboard", "")
                            .ifBlank { role.replaceFirstChar { it.uppercase() } },
                    )
                }

                // ── OTP Card (faculty) ───────────────────────────────────
                state.generatedOtp?.let { item { OtpCard(it) } }

                // ── Attendance hero (student) ────────────────────────────
                if (role == "student" && state.lines.isNotEmpty()) {
                    item {
                        AttendanceHeroCard(state.lines)
                    }
                }

                // ── Faculty: Today's slots ───────────────────────────────
                if (role == "faculty" && state.facultySlots.isNotEmpty()) {
                    item {
                        Text(
                            "Today's classes",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                    items(state.facultySlots) { item ->
                        FacultySlotCard(
                            label = "${item.slot.section.course.code} · ${item.slot.dayDisplay} P${item.slot.periodNumber}",
                            onGenerateOtp = { onGenerateOtp(item.slot.id) },
                            onReportAbsence = { onReportAbsence(item.slot.id) },
                        )
                    }
                }

                // ── Faculty: My sections ─────────────────────────────────
                if (role == "faculty" && state.sections.isNotEmpty()) {
                    item {
                        Spacer(Modifier.height(4.dp))
                        Text(
                            "My sections",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                    items(state.sections) { section ->
                        Card(
                            onClick = { onOpenSection(section.id) },
                            modifier = Modifier.fillMaxWidth(),
                            shape = MaterialTheme.shapes.medium,
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.surface,
                            ),
                            elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(16.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(12.dp),
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(40.dp)
                                        .clip(MaterialTheme.shapes.small)
                                        .background(ClassSyncBlue.copy(alpha = 0.1f)),
                                    contentAlignment = Alignment.Center,
                                ) {
                                    Icon(Icons.Default.Groups, contentDescription = null, tint = ClassSyncBlue, modifier = Modifier.size(22.dp))
                                }
                                Column {
                                    Text(
                                        "${section.course.code} · Section ${section.name}",
                                        style = MaterialTheme.typography.titleSmall,
                                    )
                                    Text(
                                        "View attendance",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    )
                                }
                            }
                        }
                    }
                }

                // ── Modules grid ─────────────────────────────────────────
                item {
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "Quick access",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                    )
                }
                items(modules.chunked(2)) { rowModules ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        for (mod in rowModules) {
                            ModuleCard(
                                label = mod.label,
                                icon = mod.icon,
                                tint = mod.tint,
                                onClick = { onOpen(mod.label) },
                                modifier = Modifier.weight(1f),
                            )
                        }
                        if (rowModules.size == 1) {
                            Spacer(modifier = Modifier.weight(1f))
                        }
                    }
                }
            }
        }
    }
}

// ── Sub-composables ──────────────────────────────────────────────────────────

@Composable
private fun AttendanceHeroCard(lines: List<String>) {
    // Parse the first attendance line to extract a percentage
    val overallPct = lines.firstOrNull()
        ?.let { Regex("""(\d+)%""").find(it)?.groupValues?.get(1)?.toFloatOrNull() }
        ?: 0f

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            AttendanceArc(
                percentage = overallPct,
                size = 140.dp,
                strokeWidth = 10.dp,
                label = "Overall",
            )
            Spacer(Modifier.height(16.dp))
            // Course-wise breakdown
            lines.forEach { line ->
                val parts = line.split(":")
                if (parts.size == 2) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Text(
                            text = parts[0].trim(),
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Text(
                            text = parts[1].trim(),
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                } else if (line.startsWith("Due:")) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            Icons.AutoMirrored.Filled.Assignment,
                            contentDescription = null,
                            tint = SemanticAmber,
                            modifier = Modifier.size(16.dp),
                        )
                        Text(
                            text = line,
                            style = MaterialTheme.typography.bodyMedium,
                            color = SemanticAmber,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun FacultySlotCard(
    label: String,
    onGenerateOtp: () -> Unit,
    onReportAbsence: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.medium,
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(label, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = onGenerateOtp,
                    modifier = Modifier.weight(1f),
                    shape = MaterialTheme.shapes.small,
                    colors = ButtonDefaults.buttonColors(containerColor = ClassSyncBlue),
                ) {
                    Icon(Icons.Default.QrCode, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(6.dp))
                    Text("Generate OTP", style = MaterialTheme.typography.labelMedium)
                }
                OutlinedButton(
                    onClick = onReportAbsence,
                    modifier = Modifier.weight(1f),
                    shape = MaterialTheme.shapes.small,
                ) {
                    Icon(Icons.Default.EventBusy, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(6.dp))
                    Text("Absent", style = MaterialTheme.typography.labelMedium)
                }
            }
        }
    }
}

@Composable
private fun OtpCard(session: AttendanceSessionDto) = Card(
    modifier = Modifier.fillMaxWidth(),
    shape = MaterialTheme.shapes.large,
    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
    elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
) {
    Column(
        Modifier
            .fillMaxWidth()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("Attendance Code", style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.onPrimaryContainer)
        Spacer(Modifier.height(8.dp))
        Text(
            session.otpCode ?: "",
            style = MaterialTheme.typography.displayLarge,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary,
        )
        Spacer(Modifier.height(4.dp))
        Text(
            "Valid for ${session.remainingSeconds}s",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f),
        )
    }
}
