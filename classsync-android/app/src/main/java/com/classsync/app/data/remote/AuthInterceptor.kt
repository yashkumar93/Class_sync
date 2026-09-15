package com.classsync.app.data.remote

import com.classsync.app.BuildConfig
import com.classsync.app.data.TokenStore
import com.google.gson.Gson
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import javax.inject.Inject

/** Adds the current JWT to every API request; auto-refreshes token on 401/403 or clears session on failure. */
class AuthInterceptor @Inject constructor(private val tokenStore: TokenStore) : Interceptor {
    private val gson = Gson()

    override fun intercept(chain: Interceptor.Chain): Response {
        val token = runBlocking { tokenStore.accessToken.first() }
        val originalRequest = chain.request()

        // Don't intercept auth endpoints
        if (originalRequest.url.encodedPath.contains("auth/login") ||
            originalRequest.url.encodedPath.contains("auth/refresh")) {
            return chain.proceed(originalRequest)
        }

        val requestWithToken = if (!token.isNullOrBlank()) {
            originalRequest.newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        } else {
            originalRequest
        }

        var response = chain.proceed(requestWithToken)

        if (response.code == 401 || response.code == 403) {
            synchronized(this) {
                // Check if token was refreshed by another thread
                val currentToken = runBlocking { tokenStore.accessToken.first() }
                if (!currentToken.isNullOrBlank() && currentToken != token) {
                    response.close()
                    val newRequest = originalRequest.newBuilder()
                        .header("Authorization", "Bearer $currentToken")
                        .build()
                    return chain.proceed(newRequest)
                }

                // Attempt to refresh the token using refresh_token
                val refreshToken = tokenStore.getRefreshToken()
                if (!refreshToken.isNullOrBlank()) {
                    val jsonMediaType = "application/json; charset=utf-8".toMediaType()
                    val body = gson.toJson(mapOf("refresh" to refreshToken)).toRequestBody(jsonMediaType)
                    val refreshRequest = Request.Builder()
                        .url(BuildConfig.BASE_URL + "api/auth/refresh/")
                        .post(body)
                        .build()

                    try {
                        val refreshResponse = chain.proceed(refreshRequest)
                        if (refreshResponse.isSuccessful) {
                            val responseBody = refreshResponse.body?.string()
                            @Suppress("UNCHECKED_CAST")
                            val refreshData = gson.fromJson(responseBody, Map::class.java) as? Map<String, Any>
                            val newAccess = refreshData?.get("access") as? String
                            val newRefresh = (refreshData?.get("refresh") as? String) ?: refreshToken
                            val role = runBlocking { tokenStore.role.first() } ?: ""

                            if (!newAccess.isNullOrBlank()) {
                                runBlocking {
                                    tokenStore.save(newAccess, newRefresh, role)
                                }
                                response.close()
                                refreshResponse.close()

                                val newRequest = originalRequest.newBuilder()
                                    .header("Authorization", "Bearer $newAccess")
                                    .build()
                                return chain.proceed(newRequest)
                            }
                        } else {
                            refreshResponse.close()
                        }
                    } catch (_: Exception) {
                        // Refresh failed
                    }
                }

                // If refresh failed or no refresh token, clear session
                runBlocking {
                    tokenStore.clear()
                }
            }
        }

        return response
    }
}
