package com.classsync.app.data.repository

import com.classsync.app.data.TokenStore
import com.classsync.app.data.remote.ApiService
import com.classsync.app.data.remote.dto.LoginRequest
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val api: ApiService,
    private val tokens: TokenStore,
) {
    val role = tokens.role

    suspend fun login(username: String, password: String): String {
        val result = api.login(LoginRequest(username, password))
        tokens.save(result.access, result.refresh, result.user.role)
        return result.user.role
    }

    suspend fun logout() = tokens.clear()
}
