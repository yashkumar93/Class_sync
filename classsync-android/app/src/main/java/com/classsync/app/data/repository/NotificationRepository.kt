package com.classsync.app.data.repository

import com.classsync.app.data.remote.ApiService
import com.classsync.app.data.remote.dto.DeviceTokenRequest
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NotificationRepository @Inject constructor(private val api: ApiService) {
    suspend fun all() = api.notifications()
    suspend fun markRead(id: Int) = api.markRead(id)
    suspend fun markAllRead() = api.markAllRead()
    suspend fun registerDevice(token: String) = api.registerDevice(DeviceTokenRequest(token))
    suspend fun riskFlags() = api.riskFlags()
    suspend fun resolveRiskFlag(id: Int) = api.resolveRiskFlag(id)
}
