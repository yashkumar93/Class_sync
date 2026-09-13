package com.classsync.app.ui.navigation

/** Centralized route definitions prevent stringly typed navigation at call-sites. */
sealed class Screen(val route: String) {
    data object Login : Screen("login")
    data object Home : Screen("home/{role}") {
        fun forRole(role: String) = "home/$role"
    }
    data object Attendance : Screen("attendance")
    data object Feature : Screen("feature/{feature}/{role}") {
        fun forRole(feature: String, role: String) = "feature/$feature/$role"
    }
    data object Web : Screen("web/{page}") {
        fun page(page: String) = "web/$page"
    }
}
