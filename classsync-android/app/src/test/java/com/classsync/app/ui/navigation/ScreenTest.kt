package com.classsync.app.ui.navigation

import org.junit.Assert.assertEquals
import org.junit.Test

class ScreenTest {
    @Test
    fun role_and_feature_routes_are_built_consistently() {
        assertEquals("home/student", Screen.Home.forRole("student"))
        assertEquals("feature/Assignments/faculty", Screen.Feature.forRole("Assignments", "faculty"))
        assertEquals("web/timetable", Screen.Web.page("timetable"))
    }
}
