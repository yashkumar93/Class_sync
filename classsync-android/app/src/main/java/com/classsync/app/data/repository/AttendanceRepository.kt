package com.classsync.app.data.repository

import com.classsync.app.data.remote.ApiService
import com.classsync.app.data.remote.dto.GenerateOtpRequest
import com.classsync.app.data.remote.dto.SubmitOtpRequest
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AttendanceRepository @Inject constructor(private val api: ApiService) {
    suspend fun myAttendance() = api.myAttendance()
    suspend fun todaySessions() = api.todaySessions()
    suspend fun generateOtp(request: GenerateOtpRequest) = api.generateOtp(request)
    suspend fun submitOtp(request: SubmitOtpRequest) = api.submitOtp(request)
    suspend fun sectionDashboard(sectionId: Int) = api.sectionAttendance(sectionId)
}
