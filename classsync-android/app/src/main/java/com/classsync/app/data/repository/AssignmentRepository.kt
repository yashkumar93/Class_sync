package com.classsync.app.data.repository

import com.classsync.app.data.remote.ApiService
import okhttp3.MultipartBody
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AssignmentRepository @Inject constructor(private val api: ApiService) {
    suspend fun forStudent() = api.studentAssignments()
    suspend fun forFaculty() = api.facultyAssignments()
    suspend fun submissions(assignmentId: Int) = api.assignmentSubmissions(assignmentId)
    suspend fun submit(assignmentId: Int, file: MultipartBody.Part) = api.submitAssignment(assignmentId, file)
}
