package com.classsync.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// ── Light scheme ────────────────────────────────────────────────────────────
private val ClassSyncColors = lightColorScheme(
    primary            = ClassSyncBlue,
    onPrimary          = Color.White,
    primaryContainer   = ClassSyncBlueLight,
    onPrimaryContainer = ClassSyncBlue,

    secondary          = ClassSyncGold,
    onSecondary        = Color.White,
    secondaryContainer = GoldTint,
    onSecondaryContainer = ClassSyncGold,

    tertiary           = SemanticGreen,
    tertiaryContainer  = SemanticGreenBg,

    background         = Color(0xFFF6F8FC),
    onBackground       = OnSurface100,
    surface            = Color.White,
    onSurface          = OnSurface100,
    onSurfaceVariant   = OnSurface60,
    surfaceVariant     = Color(0xFFEEF2F8),

    error              = SemanticRed,
    errorContainer     = SemanticRedBg,
    onError            = Color.White,

    outline            = Color(0xFFD0D9E6),
    outlineVariant     = Color(0xFFE6ECF4),
)

// ── Dark scheme ─────────────────────────────────────────────────────────────
private val ClassSyncDarkColors = darkColorScheme(
    primary            = ClassSyncBlueDark,
    onPrimary          = Navy900,
    primaryContainer   = Navy600,
    onPrimaryContainer = ClassSyncBlueDark,

    secondary          = ClassSyncGold,
    onSecondary        = Navy900,
    secondaryContainer = Color(0xFF3D2E0A),
    onSecondaryContainer = ClassSyncGold,

    tertiary           = SemanticGreen,
    tertiaryContainer  = Color(0xFF0E3320),

    background         = Navy900,
    onBackground       = OnDarkSurface100,
    surface            = ClassSyncSurfaceDark,
    onSurface          = OnDarkSurface100,
    onSurfaceVariant   = OnDarkSurface60,
    surfaceVariant     = SurfaceDark200,

    error              = SemanticRed,
    errorContainer     = Color(0xFF3B1010),
    onError            = Color.White,

    outline            = Color(0xFF3D4F6A),
    outlineVariant     = Color(0xFF2A3A52),
)

@Composable
fun ClassSyncTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) ClassSyncDarkColors else ClassSyncColors,
        typography  = ClassSyncTypography,
        shapes      = ClassSyncShapes,
        content     = content,
    )
}
