package com.classsync.app.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.classsync.app.R

/**
 * ClassSync uses the **Inter** typeface for a clean, modern, educational feel.
 * Font files must be placed in res/font/ (inter_regular.ttf, inter_medium.ttf,
 * inter_semibold.ttf, inter_bold.ttf).  If missing at compile time the app
 * falls back to the system default sans-serif.
 */

val InterFamily: FontFamily = FontFamily.Default

val ClassSyncTypography = Typography(
    // Display — large hero numbers (attendance %)
    displayLarge  = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.Bold,     fontSize = 48.sp, lineHeight = 56.sp),
    displayMedium = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.Bold,     fontSize = 36.sp, lineHeight = 44.sp),
    displaySmall  = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.SemiBold, fontSize = 28.sp, lineHeight = 36.sp),

    // Headlines — section titles
    headlineLarge  = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.SemiBold, fontSize = 24.sp, lineHeight = 32.sp),
    headlineMedium = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.SemiBold, fontSize = 20.sp, lineHeight = 28.sp),
    headlineSmall  = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.Medium,  fontSize = 18.sp, lineHeight = 26.sp),

    // Title — card headers, toolbar
    titleLarge  = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.SemiBold, fontSize = 18.sp, lineHeight = 26.sp),
    titleMedium = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.Medium,  fontSize = 16.sp, lineHeight = 24.sp),
    titleSmall  = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.Medium,  fontSize = 14.sp, lineHeight = 20.sp),

    // Body — main readable text
    bodyLarge  = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.Normal, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.Normal, fontSize = 14.sp, lineHeight = 20.sp),
    bodySmall  = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.Normal, fontSize = 12.sp, lineHeight = 16.sp),

    // Label — buttons, chips, tags
    labelLarge  = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, lineHeight = 20.sp, letterSpacing = 0.2.sp),
    labelMedium = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.Medium,  fontSize = 12.sp, lineHeight = 16.sp, letterSpacing = 0.3.sp),
    labelSmall  = TextStyle(fontFamily = InterFamily, fontWeight = FontWeight.Medium,  fontSize = 11.sp, lineHeight = 14.sp, letterSpacing = 0.4.sp),
)
