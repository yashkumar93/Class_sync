package com.classsync.app.data.remote

import com.classsync.app.data.remote.dto.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.http.*

/** Retrofit contract for the Django REST API. */
interface ApiService {
    @POST("api/auth/login/") suspend fun login(@Body request: LoginRequest): LoginResponse
    @POST("api/auth/refresh/") suspend fun refresh(@Body request: TokenRefreshRequest): TokenRefreshResponse
    @GET("api/auth/me/") suspend fun me(): UserDto

    @GET("api/dashboard/faculty/") suspend fun facultyDashboard(): FacultyDashboardResponse
    @GET("api/dashboard/student/") suspend fun studentDashboard(): StudentDashboardResponse
    @GET("api/dashboard/admin/") suspend fun adminDashboard(): AdminDashboardResponse

    @POST("api/attendance/generate-otp/") suspend fun generateOtp(@Body request: GenerateOtpRequest): AttendanceSessionDto
    @GET("api/attendance/my/") suspend fun myAttendance(): List<AttendanceSummaryDto>
    @GET("api/attendance/today-sessions/") suspend fun todaySessions(): List<TodaySessionDto>
    @POST("api/attendance/submit-otp/") suspend fun submitOtp(@Body request: SubmitOtpRequest): MessageResponse
    @GET("api/attendance/section/{id}/") suspend fun sectionAttendance(@Path("id") id: Int): SectionDashboardResponse

    @GET("api/assignments/student/") suspend fun studentAssignments(): List<StudentAssignmentDto>
    @GET("api/assignments/") suspend fun facultyAssignments(): List<AssignmentDto>
    @GET("api/assignments/{id}/submissions/") suspend fun assignmentSubmissions(@Path("id") id: Int): SubmissionDashboardResponse
    @Multipart @POST("api/assignments/{id}/submit/")
    suspend fun submitAssignment(@Path("id") id: Int, @Part file: MultipartBody.Part): SubmitAssignmentResponse

    @GET("api/absence/my/") suspend fun myAbsences(): List<AbsenceReportDto>
    @GET("api/absence/substitute-requests/") suspend fun substituteRequests(): List<SubstituteRequestDto>
    @POST("api/absence/report/") suspend fun reportAbsence(@Body request: ReportAbsenceRequest): ReportAbsenceResponse
    @POST("api/absence/{id}/accept/") suspend fun acceptSubstitute(@Path("id") id: Int): SubRequestActionResponse
    @POST("api/absence/{id}/decline/") suspend fun declineSubstitute(@Path("id") id: Int): SubRequestActionResponse
    @GET("api/absence/history/") suspend fun substitutionHistory(): List<SubstitutionRecordDto>

    @GET("api/notifications/") suspend fun notifications(): List<NotificationDto>
    @POST("api/notifications/{id}/read/") suspend fun markRead(@Path("id") id: Int): MessageResponse
    @POST("api/notifications/read-all/") suspend fun markAllRead(): MessageResponse
    @POST("api/notifications/device-token/") suspend fun registerDevice(@Body request: DeviceTokenRequest): MessageResponse
    @GET("api/notifications/risk-flags/") suspend fun riskFlags(): List<RiskFlagDto>
    @POST("api/notifications/risk-flags/{id}/resolve/") suspend fun resolveRiskFlag(@Path("id") id: Int): MessageResponse

    @GET("api/timetable/") suspend fun timetable(): TimetableResponse
}
