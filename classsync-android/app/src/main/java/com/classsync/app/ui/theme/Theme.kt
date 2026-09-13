package com.classsync.app.ui.theme

import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.foundation.isSystemInDarkTheme

private val ClassSyncColors = lightColorScheme(
    primary = ClassSyncBlue,
    secondary = ClassSyncGold,
    tertiary = ClassSyncBlue,
    primaryContainer = ClassSyncBlueLight,
)

private val ClassSyncDarkColors = darkColorScheme(
    primary = ClassSyncBlueDark,
    secondary = ClassSyncGold,
    tertiary = ClassSyncBlueDark,
    surface = ClassSyncSurfaceDark,
)

@Composable
fun ClassSyncTheme(darkTheme: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (darkTheme) ClassSyncDarkColors else ClassSyncColors,
        typography = ClassSyncTypography,
        shapes = ClassSyncShapes,
        content = content,
    )
}
