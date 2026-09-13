package com.classsync.app.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.classSyncDataStore by preferencesDataStore("classsync_preferences")

/** Stores credentials encrypted at rest; DataStore is reserved for non-sensitive UI preferences. */
@Singleton
class TokenStore @Inject constructor(@ApplicationContext private val context: Context) {
    private val accessKey = "access_token"
    private val refreshKey = "refresh_token"
    private val roleKey = "role"
    private val selectedSectionKey = stringPreferencesKey("selected_section_id")
    private val encryptedPreferences by lazy {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context,
            "classsync_secure_session",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }
    private val _accessToken = MutableStateFlow(encryptedPreferences.getString(accessKey, null))
    private val _role = MutableStateFlow(encryptedPreferences.getString(roleKey, null))

    val accessToken: StateFlow<String?> = _accessToken
    val role: StateFlow<String?> = _role
    val selectedSectionId = context.classSyncDataStore.data.map { it[selectedSectionKey] }

    suspend fun save(access: String, refresh: String, role: String) {
        encryptedPreferences.edit()
            .putString(accessKey, access)
            .putString(refreshKey, refresh)
            .putString(roleKey, role)
            .apply()
        _accessToken.value = access
        _role.value = role
    }

    suspend fun saveSelectedSection(sectionId: String?) {
        context.classSyncDataStore.edit { preferences ->
            if (sectionId == null) preferences.remove(selectedSectionKey) else preferences[selectedSectionKey] = sectionId
        }
    }

    suspend fun clear() {
        encryptedPreferences.edit().clear().apply()
        _accessToken.value = null
        _role.value = null
    }
}
