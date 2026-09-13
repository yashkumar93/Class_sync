package com.classsync.app.data.repository

import com.classsync.app.data.remote.ApiService
import javax.inject.Inject
import javax.inject.Singleton

/** API source for future native timetable widgets; the current grid uses WebView. */
@Singleton
class TimetableRepository @Inject constructor(private val api: ApiService) {
    suspend fun weeklyGrid() = api.timetable()
}
