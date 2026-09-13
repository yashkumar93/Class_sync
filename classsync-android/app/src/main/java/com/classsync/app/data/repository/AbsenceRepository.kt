package com.classsync.app.data.repository

import com.classsync.app.data.remote.ApiService
import com.classsync.app.data.remote.dto.ReportAbsenceRequest
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AbsenceRepository @Inject constructor(private val api: ApiService) {
    suspend fun myAbsences() = api.myAbsences()
    suspend fun pendingRequests() = api.substituteRequests()
    suspend fun report(request: ReportAbsenceRequest) = api.reportAbsence(request)
    suspend fun accept(requestId: Int) = api.acceptSubstitute(requestId)
    suspend fun decline(requestId: Int) = api.declineSubstitute(requestId)
    suspend fun history() = api.substitutionHistory()
}
