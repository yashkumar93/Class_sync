package com.classsync.app.data.remote.dto

import com.google.gson.annotations.SerializedName

// ═══════════════════════════════════════════════════════════════════════════
// Auth
// ═══════════════════════════════════════════════════════════════════════════

data class LoginRequest(
    val username: String,
    val password: String
)

data class LoginResponse(
    val access: String,
    val refresh: String,
    val user: UserDto
)

data class TokenRefreshRequest(
    val refresh: String
)

data class TokenRefreshResponse(
    val access: String,
    val refresh: String? = null
)

// ═══════════════════════════════════════════════════════════════════════════
// Core Models
// ═══════════════════════════════════════════════════════════════════════════

data class UserDto(
    val id: Int,
    val username: String,
    @SerializedName("first_name") val firstName: String = "",
    @SerializedName("last_name") val lastName: String = "",
    @SerializedName("full_name") val fullName: String = "",
    val email: String = "",
    val role: String,
    val phone: String = "",
    val department: DepartmentDto? = null,
    @SerializedName("roll_number") val rollNumber: String = "",
    @SerializedName("year_of_study") val yearOfStudy: Int? = null,
    @SerializedName("is_active") val isActive: Boolean = true
)

data class UserMinimalDto(
    val id: Int,
    val username: String,
    @SerializedName("full_name") val fullName: String = "",
    val role: String = ""
)

data class DepartmentDto(
    val id: Int,
    val name: String,
    val code: String
)

data class CourseDto(
    val id: Int,
    val code: String,
    val name: String,
    val credits: Int = 3,
    val department: DepartmentDto? = null
)

data class SectionDto(
    val id: Int,
    val name: String,
    val course: CourseDto,
    val faculty: UserMinimalDto? = null,
    val room: String = "",
    @SerializedName("student_count") val studentCount: Int = 0
)

data class TimetableSlotDto(
    val id: Int,
    val section: SectionDto,
    val day: Int,
    @SerializedName("day_display") val dayDisplay: String = "",
    @SerializedName("period_number") val periodNumber: Int,
    @SerializedName("start_time") val startTime: String,
    @SerializedName("end_time") val endTime: String
)

// ═══════════════════════════════════════════════════════════════════════════
// Attendance
// ═══════════════════════════════════════════════════════════════════════════

data class AttendanceSessionDto(
    val id: Int,
    val slot: TimetableSlotDto,
    val date: String,
    @SerializedName("otp_code") val otpCode: String? = null,
    @SerializedName("is_active") val isActive: Boolean = false,
    @SerializedName("expires_at") val expiresAt: String? = null,
    @SerializedName("remaining_seconds") val remainingSeconds: Int = 0,
    @SerializedName("created_at") val createdAt: String = ""
)

data class GenerateOtpRequest(
    @SerializedName("slot_id") val slotId: Int,
    val date: String
)

data class SubmitOtpRequest(
    @SerializedName("slot_id") val slotId: Int,
    @SerializedName("otp_code") val otpCode: String
)

data class AttendanceSummaryDto(
    @SerializedName("course_id") val courseId: Int,
    @SerializedName("course_code") val courseCode: String,
    @SerializedName("course_name") val courseName: String,
    @SerializedName("total_sessions") val totalSessions: Int,
    val attended: Int,
    val percentage: Double,
    @SerializedName("below_threshold") val belowThreshold: Boolean
)

data class SectionAttendanceRowDto(
    @SerializedName("student_id") val studentId: Int,
    @SerializedName("student_name") val studentName: String,
    @SerializedName("roll_number") val rollNumber: String,
    @SerializedName("total_sessions") val totalSessions: Int,
    val attended: Int,
    val percentage: Double,
    @SerializedName("below_threshold") val belowThreshold: Boolean
)

data class TodaySessionDto(
    val slot: TimetableSlotDto,
    val session: AttendanceSessionDto? = null,
    @SerializedName("is_active") val isActive: Boolean = false,
    @SerializedName("already_marked") val alreadyMarked: Boolean = false
)

data class TodaySlotWithSession(
    val slot: TimetableSlotDto,
    val session: AttendanceSessionDto? = null
)

data class SessionCloseResponse(
    @SerializedName("absent_count") val absentCount: Int,
    @SerializedName("notified_count") val notifiedCount: Int,
    val message: String
)

data class SectionDashboardResponse(
    val section: SectionDto,
    val rows: List<SectionAttendanceRowDto>,
    val sessions: List<AttendanceSessionDto>,
    val threshold: Int,
    @SerializedName("today_slots") val todaySlots: List<TimetableSlotDto>,
    val today: String
)

// ═══════════════════════════════════════════════════════════════════════════
// Assignments
// ═══════════════════════════════════════════════════════════════════════════

data class AssignmentDto(
    val id: Int,
    val title: String,
    val description: String = "",
    val attachment: String? = null,
    @SerializedName("due_date") val dueDate: String,
    val section: SectionDto? = null,
    @SerializedName("created_by") val createdBy: UserMinimalDto? = null,
    @SerializedName("is_past_due") val isPastDue: Boolean = false,
    @SerializedName("submission_count") val submissionCount: Int = 0,
    @SerializedName("total_students") val totalStudents: Int = 0,
    @SerializedName("created_at") val createdAt: String = ""
)

data class SubmissionDto(
    val id: Int,
    val student: UserMinimalDto? = null,
    val file: String = "",
    @SerializedName("submitted_at") val submittedAt: String = "",
    @SerializedName("is_late") val isLate: Boolean = false
)

data class StudentAssignmentDto(
    val assignment: AssignmentDto,
    val submission: SubmissionDto? = null,
    @SerializedName("is_past_due") val isPastDue: Boolean = false,
    @SerializedName("can_resubmit") val canResubmit: Boolean = false
)

data class SubmissionDashboardResponse(
    val assignment: AssignmentDto,
    @SerializedName("on_time") val onTime: List<SubmissionDto>,
    val late: List<SubmissionDto>,
    @SerializedName("missing_students") val missingStudents: List<UserMinimalDto>
)

data class SubmitAssignmentResponse(
    val submission: SubmissionDto,
    val message: String
)

// ═══════════════════════════════════════════════════════════════════════════
// Absence & Substitutions
// ═══════════════════════════════════════════════════════════════════════════

data class AbsenceReportDto(
    val id: Int,
    val faculty: UserMinimalDto? = null,
    @SerializedName("timetable_slot") val timetableSlot: TimetableSlotDto? = null,
    val date: String,
    val reason: String = "",
    val status: String,
    @SerializedName("status_display") val statusDisplay: String = "",
    @SerializedName("assigned_substitute") val assignedSubstitute: UserMinimalDto? = null,
    @SerializedName("is_makeup_candidate") val isMakeupCandidate: Boolean = false,
    @SerializedName("substitute_requests") val substituteRequests: List<SubstituteRequestDto> = emptyList(),
    @SerializedName("created_at") val createdAt: String = ""
)

data class ReportAbsenceRequest(
    @SerializedName("timetable_slot_id") val timetableSlotId: Int,
    val date: String,
    val reason: String = ""
)

data class ReportAbsenceResponse(
    val report: AbsenceReportDto,
    @SerializedName("sent_count") val sentCount: Int,
    val message: String
)

data class SubstituteRequestDto(
    val id: Int,
    @SerializedName("absence_report_id") val absenceReportId: Int = 0,
    @SerializedName("requested_faculty") val requestedFaculty: UserMinimalDto? = null,
    val status: String,
    @SerializedName("course_name") val courseName: String = "",
    @SerializedName("section_name") val sectionName: String = "",
    @SerializedName("absent_faculty_name") val absentFacultyName: String = "",
    val date: String = "",
    @SerializedName("period_info") val periodInfo: String = "",
    @SerializedName("responded_at") val respondedAt: String? = null,
    @SerializedName("created_at") val createdAt: String = ""
)

data class FacultyAvailabilityDto(
    val id: Int,
    @SerializedName("opted_in") val optedIn: Boolean,
    val notes: String = "",
    @SerializedName("updated_at") val updatedAt: String = ""
)

data class SubstitutionRecordDto(
    val id: Int,
    @SerializedName("substitute_faculty") val substituteFaculty: UserMinimalDto? = null,
    @SerializedName("original_faculty") val originalFaculty: String = "",
    @SerializedName("course_name") val courseName: String = "",
    val date: String = "",
    @SerializedName("was_random_tiebreak") val wasRandomTiebreak: Boolean = false,
    val timestamp: String = ""
)

data class SubRequestActionResponse(
    val message: String,
    val success: Boolean = true,
    @SerializedName("all_declined") val allDeclined: Boolean = false
)

// ═══════════════════════════════════════════════════════════════════════════
// Notifications
// ═══════════════════════════════════════════════════════════════════════════

data class NotificationDto(
    val id: Int,
    @SerializedName("notif_type") val notifType: String,
    @SerializedName("type_display") val typeDisplay: String = "",
    val message: String,
    @SerializedName("related_object_id") val relatedObjectId: Int? = null,
    @SerializedName("sent_at") val sentAt: String = "",
    @SerializedName("read_at") val readAt: String? = null,
    @SerializedName("delivery_status") val deliveryStatus: String = ""
)

data class RiskFlagDto(
    val id: Int,
    val student: UserMinimalDto? = null,
    val course: CourseDto? = null,
    val reason: String = "",
    @SerializedName("attendance_pct") val attendancePct: Double? = null,
    @SerializedName("missed_submissions") val missedSubmissions: Int = 0,
    @SerializedName("flagged_at") val flaggedAt: String = "",
    val resolved: Boolean = false,
    @SerializedName("resolved_at") val resolvedAt: String? = null
)

data class DeviceTokenRequest(
    val token: String,
    val platform: String = "android"
)

// ═══════════════════════════════════════════════════════════════════════════
// Dashboards
// ═══════════════════════════════════════════════════════════════════════════

data class FacultyDashboardResponse(
    val sections: List<SectionDto>,
    val today: String,
    @SerializedName("today_slots") val todaySlots: List<TodaySlotWithSession>,
    @SerializedName("pending_sub_requests") val pendingSubRequests: List<SubstituteRequestDto>,
    @SerializedName("recent_absences") val recentAbsences: List<AbsenceReportDto>,
    @SerializedName("unread_notifications") val unreadNotifications: Int
)

data class StudentDashboardResponse(
    val sections: List<SectionDto>,
    @SerializedName("attendance_summary") val attendanceSummary: List<AttendanceSummaryDto>,
    @SerializedName("upcoming_assignments") val upcomingAssignments: List<AssignmentDto>,
    @SerializedName("unread_notifications") val unreadNotifications: Int
)

data class AdminDashboardResponse(
    @SerializedName("total_faculty") val totalFaculty: Int,
    @SerializedName("total_students") val totalStudents: Int,
    @SerializedName("total_sections") val totalSections: Int,
    @SerializedName("total_courses") val totalCourses: Int,
    @SerializedName("self_study_count") val selfStudyCount: Int,
    @SerializedName("makeup_candidates") val makeCandidates: Int,
    @SerializedName("active_risk_flags") val activeRiskFlags: Int
)

// ═══════════════════════════════════════════════════════════════════════════
// Timetable
// ═══════════════════════════════════════════════════════════════════════════

data class TimetableCellDto(
    @SerializedName("slot_id") val slotId: Int,
    @SerializedName("course_code") val courseCode: String,
    @SerializedName("course_name") val courseName: String,
    @SerializedName("section_name") val sectionName: String,
    @SerializedName("faculty_name") val facultyName: String? = null,
    val room: String = "",
    @SerializedName("is_today") val isToday: Boolean = false,
    @SerializedName("is_substitute") val isSubstitute: Boolean = false,
    @SerializedName("substitute_name") val substituteName: String? = null,
    @SerializedName("absence_status") val absenceStatus: String? = null
)

data class TimetableRowDto(
    val band: String,
    val days: Map<String, List<TimetableCellDto>>
)

data class TimetableResponse(
    val grid: List<TimetableRowDto>,
    val days: List<Int>,
    @SerializedName("day_names") val dayNames: List<String>,
    val today: String,
    @SerializedName("today_weekday") val todayWeekday: Int
)

// ═══════════════════════════════════════════════════════════════════════════
// Generic Responses
// ═══════════════════════════════════════════════════════════════════════════

data class MessageResponse(
    val message: String
)

data class ErrorResponse(
    val error: String? = null,
    val detail: String? = null
)
