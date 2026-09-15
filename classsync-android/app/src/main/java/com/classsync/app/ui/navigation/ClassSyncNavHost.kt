package com.classsync.app.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.classsync.app.BuildConfig
import com.classsync.app.data.TokenStore
import com.classsync.app.ui.attendance.AttendanceScreen
import com.classsync.app.ui.attendance.AttendanceViewModel
import com.classsync.app.ui.attendance.SectionDashboardRoute
import com.classsync.app.ui.absence.AbsenceScreen
import com.classsync.app.ui.absence.AbsenceViewModel
import com.classsync.app.ui.absence.ReportAbsenceScreen
import com.classsync.app.ui.assignments.AssignmentScreen
import com.classsync.app.ui.assignments.AssignmentViewModel
import com.classsync.app.ui.auth.LoginScreen
import com.classsync.app.ui.auth.LoginViewModel
import com.classsync.app.ui.dashboard.HomeScreen
import com.classsync.app.ui.dashboard.HomeViewModel
import com.classsync.app.ui.features.FeatureScreen
import com.classsync.app.ui.features.FeatureViewModel
import com.classsync.app.ui.web.WebViewScreen
import com.classsync.app.ui.notifications.NotificationScreen
import com.classsync.app.ui.notifications.NotificationViewModel
import com.classsync.app.ui.profile.ProfileScreen
import com.classsync.app.ui.profile.ProfileViewModel
import javax.inject.Inject

@Composable
fun ClassSyncNavHost(notificationType: String? = null, notificationEvent: Int = 0) {
    val sessionViewModel: TokenStoreViewModel = hiltViewModel()
    val tokenStore = sessionViewModel.tokenStore
    val nav = rememberNavController()
    val accessToken by tokenStore.accessToken.collectAsState(initial = null)
    val role by tokenStore.role.collectAsState(initial = null)
    var handledNotificationEvent by androidx.compose.runtime.remember { mutableStateOf(-1) }
    androidx.compose.runtime.LaunchedEffect(notificationEvent, role) {
        if (notificationType != null && role != null && handledNotificationEvent != notificationEvent) {
            nav.navigate("notifications/$role?risks=${notificationType == "risk_flag"}") {
                launchSingleTop = true
            }
            handledNotificationEvent = notificationEvent
        }
    }
    NavHost(navController = nav, startDestination = "login") {
        composable("login") {
            val vm: LoginViewModel = hiltViewModel()
            val state by vm.state.collectAsState()
            state.role?.let { role ->
                androidx.compose.runtime.LaunchedEffect(role, notificationEvent) {
                    if (notificationType != null) return@LaunchedEffect
                    nav.navigate("home/$role") { popUpTo("login") { inclusive = true } }
                }
            }
            LoginScreen(state, vm::login)
        }
        composable("home/{role}", arguments = listOf(navArgument("role") { type = NavType.StringType })) { entry ->
            val role = entry.arguments?.getString("role") ?: "student"
            val vm: HomeViewModel = hiltViewModel()
            val state by vm.state.collectAsState()
            HomeScreen(role, state, { vm.load(role) }, { target ->
                when (target) {
                    "Attendance" -> nav.navigate("attendance")
                    "Assignments" -> nav.navigate("assignments/$role")
                    "Absences" -> nav.navigate("absence")
                    "Notifications" -> nav.navigate("notifications/$role")
                    "Risk Flags" -> nav.navigate("notifications/$role?risks=true")
                    "Timetable" -> nav.navigate("web/timetable")
                    "Profile" -> nav.navigate("profile")
                    "Admin panel" -> nav.navigate("web/admin")
                    else -> nav.navigate("feature/$target/$role")
                }
            }, { sectionId -> nav.navigate("section/$sectionId") }, { slotId -> nav.navigate("report-absence/$slotId") }, vm::generateOtp)
        }
        composable("attendance") {
            val vm: AttendanceViewModel = hiltViewModel()
            val state by vm.state.collectAsState()
            AttendanceScreen(state, vm::load, vm::submit) { nav.popBackStack() }
        }
        composable("assignments/{role}", arguments = listOf(navArgument("role") { type = NavType.StringType })) { entry ->
            val role = entry.arguments?.getString("role") ?: "student"
            val vm: AssignmentViewModel = hiltViewModel()
            val state by vm.state.collectAsState()
            AssignmentScreen(role, state, { vm.load(role) }, vm::loadSubmissions, vm::submit) { nav.popBackStack() }
        }
        composable("absence") {
            val vm: AbsenceViewModel = hiltViewModel()
            val state by vm.state.collectAsState()
            AbsenceScreen(state, vm::load, vm::accept, vm::decline) { nav.popBackStack() }
        }
        composable("report-absence/{slotId}", arguments = listOf(navArgument("slotId") { type = NavType.IntType })) { entry ->
            val slotId = entry.arguments?.getInt("slotId") ?: 0
            val vm: AbsenceViewModel = hiltViewModel()
            val state by vm.state.collectAsState()
            ReportAbsenceScreen(slotId, state, { date, reason -> vm.report(slotId, date, reason) { nav.popBackStack() } }) { nav.popBackStack() }
        }
        composable(
            "notifications/{role}?risks={risks}",
            arguments = listOf(
                navArgument("role") { type = NavType.StringType },
                navArgument("risks") { type = NavType.BoolType; defaultValue = false },
            ),
        ) { entry ->
            val role = entry.arguments?.getString("role") ?: "student"
            val risks = entry.arguments?.getBoolean("risks") ?: false
            val vm: NotificationViewModel = hiltViewModel()
            val state by vm.state.collectAsState()
            NotificationScreen(role, state, { vm.load(risks) }, vm::markAllRead, vm::resolveRisk) { nav.popBackStack() }
        }
        composable("section/{id}", arguments = listOf(navArgument("id") { type = NavType.IntType })) { entry ->
            SectionDashboardRoute(entry.arguments?.getInt("id") ?: 0, onBack = { nav.popBackStack() })
        }
        composable(
            "feature/{feature}/{role}",
            arguments = listOf(navArgument("feature") { type = NavType.StringType }, navArgument("role") { type = NavType.StringType }),
        ) { entry ->
            val feature = entry.arguments?.getString("feature") ?: ""
            val role = entry.arguments?.getString("role") ?: ""
            val vm: FeatureViewModel = hiltViewModel()
            val state by vm.state.collectAsState()
            FeatureScreen(feature, role, state, { vm.load(feature, role) }) { nav.popBackStack() }
        }
        composable("web/{page}", arguments = listOf(navArgument("page") { type = NavType.StringType })) { entry ->
            val page = entry.arguments?.getString("page") ?: "timetable"
            val path = if (page == "admin") "admin-panel/" else "timetable/"
            WebViewScreen(if (page == "admin") "Admin panel" else "Timetable", BuildConfig.BASE_URL + path, accessToken) { nav.popBackStack() }
        }
        composable("profile") {
            val vm: ProfileViewModel = hiltViewModel()
            val state by vm.state.collectAsState()
            ProfileScreen(
                state = state,
                onBack = { nav.popBackStack() },
                onLogout = {
                    vm.logout {
                        nav.navigate("login") { popUpTo(0) { inclusive = true } }
                    }
                },
                onRefresh = vm::loadProfile
            )
        }
    }
}

/** Hilt bridge keeps the composable API testable while retaining a singleton session store. */
@dagger.hilt.android.lifecycle.HiltViewModel
class TokenStoreViewModel @Inject constructor(val tokenStore: TokenStore) : androidx.lifecycle.ViewModel()
