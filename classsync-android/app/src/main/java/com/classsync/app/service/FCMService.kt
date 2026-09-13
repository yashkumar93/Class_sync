package com.classsync.app.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.classsync.app.MainActivity
import com.classsync.app.R
import com.classsync.app.data.remote.ApiService
import com.classsync.app.data.remote.dto.DeviceTokenRequest
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class FCMService : FirebaseMessagingService() {
    @Inject lateinit var api: ApiService

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        registerToken(token)
    }

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)
        val type = message.data["type"] ?: "announcement"
        val channel = channelFor(type)
        createChannel(channel)

        val launchIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            putExtra(MainActivity.EXTRA_NOTIFICATION_TYPE, type)
            putExtra(MainActivity.EXTRA_RELATED_OBJECT_ID, message.data["related_object_id"])
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            type.hashCode(),
            launchIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val notification = NotificationCompat.Builder(this, channel.id)
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle(message.data["title"] ?: "ClassSync")
            .setContentText(message.data["message"] ?: "You have an update.")
            .setStyle(NotificationCompat.BigTextStyle().bigText(message.data["message"]))
            .setPriority(channel.priority)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setGroup("classsync_${channel.id}")
            .build()
        NotificationManagerCompat.from(this).notify((System.currentTimeMillis() % Int.MAX_VALUE).toInt(), notification)
    }

    private fun registerToken(token: String) {
        CoroutineScope(Dispatchers.IO).launch { runCatching { api.registerDevice(DeviceTokenRequest(token)) } }
    }

    private fun createChannel(channel: NotificationChannelSpec) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val notificationChannel = NotificationChannel(channel.id, channel.label, channel.importance)
            notificationChannel.description = "ClassSync ${channel.label.lowercase()} notifications"
            getSystemService(NotificationManager::class.java).createNotificationChannel(notificationChannel)
        }
    }
}

private data class NotificationChannelSpec(
    val id: String,
    val label: String,
    val importance: Int,
    val priority: Int,
)

private fun channelFor(type: String): NotificationChannelSpec = when (type) {
    "substitution_request" -> NotificationChannelSpec("classsync_substitution", "Substitutions", NotificationManager.IMPORTANCE_HIGH, NotificationCompat.PRIORITY_HIGH)
    "class_reassigned", "self_study" -> NotificationChannelSpec("classsync_schedule", "Schedule", NotificationManager.IMPORTANCE_HIGH, NotificationCompat.PRIORITY_HIGH)
    "assignment_reminder" -> NotificationChannelSpec("classsync_assignments", "Assignments", NotificationManager.IMPORTANCE_HIGH, NotificationCompat.PRIORITY_HIGH)
    "attendance_alert", "absence_marked" -> NotificationChannelSpec("classsync_attendance", "Attendance", NotificationManager.IMPORTANCE_HIGH, NotificationCompat.PRIORITY_HIGH)
    "risk_flag" -> NotificationChannelSpec("classsync_alerts", "Alerts", NotificationManager.IMPORTANCE_HIGH, NotificationCompat.PRIORITY_HIGH)
    else -> NotificationChannelSpec("classsync_announcements", "Announcements", NotificationManager.IMPORTANCE_DEFAULT, NotificationCompat.PRIORITY_DEFAULT)
}
