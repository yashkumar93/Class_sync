package com.classsync.app.service

import com.classsync.app.data.repository.NotificationRepository
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import javax.inject.Inject
import javax.inject.Singleton

/** Registers the current FCM token after authentication, including tokens issued before login. */
@Singleton
class FcmTokenRegistrar @Inject constructor(private val notifications: NotificationRepository) {
    fun registerCurrentToken() {
        runCatching {
            FirebaseMessaging.getInstance().token.addOnSuccessListener { token ->
                CoroutineScope(Dispatchers.IO).launch { runCatching { notifications.registerDevice(token) } }
            }
        }
    }
}
