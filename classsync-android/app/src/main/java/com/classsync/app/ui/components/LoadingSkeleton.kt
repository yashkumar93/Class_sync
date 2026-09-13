package com.classsync.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/** Lightweight placeholder used while live, non-cached API data loads. */
@Composable
fun LoadingSkeleton(rows: Int = 3) {
    Column {
        repeat(rows) {
            Spacer(
                Modifier
                    .padding(vertical = 6.dp)
                    .fillMaxWidth()
                    .height(68.dp)
                    .background(MaterialTheme.colorScheme.surfaceVariant, MaterialTheme.shapes.medium),
            )
        }
    }
}
