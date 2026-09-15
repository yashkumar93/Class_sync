package com.classsync.app.ui.theme

import androidx.compose.ui.graphics.Color

// ── Primary Brand ────────────────────────────────────────────────────────────
val ClassSyncBlue        = Color(0xFF124E8C)
val ClassSyncBlueDark    = Color(0xFF9BCBFF)
val ClassSyncBlueLight   = Color(0xFFD9E9FF)
val ClassSyncGold        = Color(0xFFC58A11)

// ── Extended Palette (8-point grid aligned) ──────────────────────────────────
// Deep navy for dark theme / login background
val Navy900              = Color(0xFF0D1B2E)
val Navy800              = Color(0xFF122640)
val Navy700              = Color(0xFF1A3152)
val Navy600              = Color(0xFF234169)
val Navy500              = Color(0xFF2E5280)

// Surface tones (dark theme)
val ClassSyncSurfaceDark = Color(0xFF10161F)
val SurfaceDark200       = Color(0xFF1A2233)
val SurfaceDark300       = Color(0xFF243044)

// Neutral text on light backgrounds
val OnSurface100         = Color(0xFF0F1A2E)   // headings  (100% opacity feel)
val OnSurface80          = Color(0xFF3D4F6A)   // body text  (80%)
val OnSurface60          = Color(0xFF6B7D99)   // secondary  (60%)

// Neutral text on dark backgrounds
val OnDarkSurface100     = Color(0xFFF0F4FA)
val OnDarkSurface80      = Color(0xFFBDC8D8)
val OnDarkSurface60      = Color(0xFF8494AD)

// Semantic / feedback
val SemanticGreen        = Color(0xFF1DB954)   // success / attendance ≥75 %
val SemanticGreenBg      = Color(0xFFE6F9EE)
val SemanticAmber        = Color(0xFFF59E0B)   // warning / attendance 65–74 %
val SemanticAmberBg      = Color(0xFFFFF8E1)
val SemanticRed          = Color(0xFFEF4444)   // error / attendance < 65 %
val SemanticRedBg        = Color(0xFFFEE2E2)

// Accent tints (10 % of primary for subtle backgrounds)
val BlueTint             = Color(0x1A124E8C)   // ≈ 10 % opacity blue
val GoldTint             = Color(0x1AC58A11)
