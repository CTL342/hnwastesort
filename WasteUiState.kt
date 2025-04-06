package com.example.waste // <-- Your Package

import android.graphics.Bitmap
import android.net.Uri

// Represents the different states the UI can be in
sealed interface WasteUiState {
    data object Idle : WasteUiState // Home screen
    data class ImageSelected(val imageUri: Uri, val bitmap: Bitmap? = null) : WasteUiState // Bitmap optional here
    data class Analyzing(val imageUri: Uri, val bitmap: Bitmap? = null) : WasteUiState
    data class Success(
        val imageUri: Uri,
        val bitmap: Bitmap? = null,
        val classification: String,
        val identifiedObject: String, // Renamed for clarity
        val reason: String
    ) : WasteUiState
    data class Error(
        val imageUri: Uri?, // Can have error even before image is fully processed
        val bitmap: Bitmap? = null,
        val message: String
    ) : WasteUiState
}

// Data class to hold parsed results
data class ClassificationResult(
    val classification: String,
    val identifiedObject: String,
    val reason: String
)
