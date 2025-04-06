package com.example.waste // <-- *** REPLACE WITH YOUR ACTUAL PACKAGE NAME ***

import android.app.Application
import android.content.ContentResolver
import android.content.Context
import android.graphics.Bitmap
import android.graphics.ImageDecoder
import android.net.Uri
import android.os.Build
import android.provider.MediaStore
import android.util.Log
import androidx.annotation.Nullable
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.google.ai.client.generativeai.GenerativeModel
import com.google.ai.client.generativeai.type.* // Import all types
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.IOException

// Assumes WasteUiState.kt with ClassificationResult data class exists in the same package

class WasteViewModel(application: Application) : AndroidViewModel(application) {

    private val TAG = "WasteViewModel" // Tag for ViewModel specific logs

    // Holds the current state of the UI, observed by the Compose screen
    private val _uiState = MutableStateFlow<WasteUiState>(WasteUiState.Idle)
    val uiState: StateFlow<WasteUiState> = _uiState.asStateFlow()

    // Reference to the initialized Gemini Model
    private var generativeModel: GenerativeModel? = null
    // API Key retrieved securely from BuildConfig
    private val apiKey = BuildConfig.GEMINI_API_KEY // <-- Make sure BuildConfig is imported correctly

    // Initialization block: Called when the ViewModel is first created
    init {
        Log.d(TAG, "ViewModel INIT started.")
        initializeGeminiModel() // Start Gemini initialization asynchronously
        Log.d(TAG, "ViewModel INIT finished (Gemini init launched async).")
    }

    // Initializes the Gemini Model on a background thread
    private fun initializeGeminiModel() {
        viewModelScope.launch(Dispatchers.IO) { // Use IO dispatcher for potential network/setup
            Log.d(TAG, "Coroutine for Gemini Init launched.")

            val placeholderValue = "" // Match default value in build.gradle's getProperty if used
            if (apiKey.isEmpty() || apiKey == placeholderValue) {
                Log.e(TAG, "API Key missing or placeholder. AI Disabled. Updating UI state to Error.")
                // Update UI state to show an error if the key is invalid
                _uiState.update { WasteUiState.Error(null, null, "API Key Error. AI Disabled.") }
                return@launch // Stop initialization
            }
            try {
                // Create the GenerativeModel instance
                generativeModel = GenerativeModel(
                    modelName = "gemini-1.5-flash-latest", // Or your preferred vision model
                    apiKey = apiKey
                    // You can add SafetySettings and GenerationConfig here if needed:
                    // safetySettings = listOf(SafetySetting(...)),
                    // generationConfig = GenerationConfig.Builder()...build()
                )
                Log.i(TAG, "Gemini Model Initialized Successfully (ViewModel).")
            } catch (e: Exception) {
                Log.e(TAG, "Error initializing Gemini (ViewModel): ${e.message}", e)
                // Update UI state to show initialization error
                _uiState.update { WasteUiState.Error(null, null, "AI Model Init Failed: ${e.localizedMessage}") }
            }
        }
    }

    /**
     * Called from the UI when an image URI is selected (e.g., from Gallery or Camera).
     * It loads the Bitmap and triggers the analysis.
     */
    fun processImageUri(uri: Uri?) {
        if (uri == null) {
            Log.w(TAG, "processImageUri called with null URI. Setting Error state.")
            _uiState.update { WasteUiState.Error(null, null, "Failed to get image.") }
            return
        }
        Log.d(TAG, "processImageUri: Received URI $uri. Setting Analyzing state.")
        // Immediately update state to Analyzing to show loading indicator
        _uiState.update { WasteUiState.Analyzing(uri) }

        // Launch a coroutine to perform bitmap loading and analysis off the main thread
        viewModelScope.launch(Dispatchers.IO) {
            Log.d(TAG, "processImageUri: Coroutine launched for bitmap loading & analysis.")
            val bitmap = loadBitmapFromUri(getApplication(), uri) // Load bitmap in background
            if (bitmap != null) {
                Log.d(TAG, "processImageUri: Bitmap loaded successfully. Updating state before analysis.")
                // Update state again to include the loaded bitmap (UI might show preview)
                _uiState.update { WasteUiState.Analyzing(uri, bitmap) }
                // Proceed to analyze the image
                analyzeImage(uri, bitmap)
            } else {
                // If bitmap is null, loadBitmapFromUri should have already updated the UI state to Error
                Log.e(TAG, "processImageUri: Bitmap loading failed for URI: $uri (State should reflect error)")
            }
        }
    }

    /**
     * Alternative entry point if you already have a Bitmap (e.g., from camera preview).
     */
    fun processImageBitmap(bitmap: Bitmap?) {
        if (bitmap == null) {
            Log.w(TAG, "processImageBitmap called with null Bitmap. Setting Error state.")
            _uiState.update { WasteUiState.Error(null, null, "Failed to get image.") }
            return
        }
        // Need a dummy URI or handle state differently if only bitmap is available
        val dummyUri = Uri.EMPTY
        Log.d(TAG, "processImageBitmap: Received Bitmap. Setting Analyzing state.")
        _uiState.update { WasteUiState.Analyzing(dummyUri, bitmap) }

        viewModelScope.launch(Dispatchers.IO) {
            Log.d(TAG, "processImageBitmap: Coroutine launched for analysis.")
            analyzeImage(dummyUri, bitmap) // Analyze directly
        }
    }


    /**
     * Performs the actual analysis using the Gemini model.
     * Called internally after an image is available.
     */
    private suspend fun analyzeImage(imageUri: Uri, imageBitmap: Bitmap) {
        val model = generativeModel // Get the initialized model instance
        if (model == null) {
            Log.e(TAG, "analyzeImage: Gemini model not initialized for analysis. Setting Error state.")
            _uiState.update { WasteUiState.Error(imageUri, imageBitmap, "AI Model not ready.") }
            return
        }

        Log.i(TAG, "analyzeImage: Starting AI analysis...")
        // Get the prompt string from resources (requires Application context)
        val prompt = getApplication<Application>().getString(R.string.gemini_prompt)

        try {
            // Build the input content using the Content Kotlin DSL
            val inputContent = content {
                image(imageBitmap) // Add the bitmap part
                text(prompt)       // Add the text prompt part
            }

            // Call the suspend function from the Gemini Kotlin SDK
            val response: GenerateContentResponse = model.generateContent(inputContent)

            // Process the response (still on the background thread)
            val responseText = response.text // Extracts text from the first valid candidate
            if (responseText == null) {
                // Check for blocking reasons if text is null
                val blockReason = response.promptFeedback?.blockReason?.toString() ?: "Unknown reason (null text)"
                val finishReason = response.candidates.firstOrNull()?.finishReason?.toString() ?: "Unknown reason (null text)"
                Log.w(TAG, "analyzeImage: Gemini response text was null. BlockReason: $blockReason, FinishReason: $finishReason")
                throw IOException("Empty or blocked response from AI. Reason: $finishReason / $blockReason")
            }

            Log.d(TAG, "analyzeImage: AI Raw Response received (Length: ${responseText.length}).")
            val result: ClassificationResult? = parseClassificationResult(responseText)

            if (result != null) {
                // If parsing is successful, update the UI state to Success
                Log.i(TAG, "analyzeImage: Parsing successful. Updating state to Success.")
                _uiState.update {
                    WasteUiState.Success(
                        imageUri = imageUri,
                        bitmap = imageBitmap,
                        classification = result.classification,
                        identifiedObject = result.identifiedObject,
                        reason = result.reason
                    )
                }
            } else {
                // If parsing fails, treat it as an error
                Log.w(TAG, "analyzeImage: Failed to parse AI response. Throwing IOException. Raw: $responseText")
                throw IOException("Could not understand AI response format.")
            }

        } catch (e: Exception) { // Catch exceptions during API call or parsing
            Log.e(TAG, "analyzeImage: Gemini analysis/processing failed: ${e.message}", e)
            // Update UI state to show the error
            _uiState.update { WasteUiState.Error(imageUri, imageBitmap, "Analysis failed: ${e.localizedMessage}") }
        }
    }

    /**
     * Resets the UI state back to the initial Idle state. Called by the UI (e.g., Clear button).
     */
    fun resetState() {
        Log.d(TAG, "resetState: Setting UI state to Idle.")
        _uiState.update { WasteUiState.Idle }
    }

    // --- Helper Functions ---

    /**
     * Loads a Bitmap from a given URI using the appropriate method based on SDK version.
     * Runs on a background thread (called within viewModelScope.launch).
     * Updates UI state directly in case of errors.
     */
    private fun loadBitmapFromUri(context: Context, uri: Uri): Bitmap? {
        var bitmap: Bitmap? = null
        Log.d(TAG, "loadBitmapFromUri: Attempting to load bitmap for URI: $uri")
        try {
            val resolver: ContentResolver = context.contentResolver
            bitmap = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                // Use modern ImageDecoder
                ImageDecoder.decodeBitmap(ImageDecoder.createSource(resolver, uri))
            } else {
                // Use deprecated MediaStore method for older APIs
                @Suppress("DEPRECATION")
                MediaStore.Images.Media.getBitmap(resolver, uri)
            }
            Log.d(TAG, "loadBitmapFromUri: Bitmap loaded successfully.")
        } catch (e: IOException) {
            Log.e(TAG, "loadBitmapFromUri: IOException loading bitmap: ${e.message}", e)
            _uiState.update { WasteUiState.Error(uri, null, "Error loading image file.") }
        } catch (e: SecurityException) {
            Log.e(TAG, "loadBitmapFromUri: SecurityException loading bitmap: ${e.message}", e)
            _uiState.update { WasteUiState.Error(uri, null, "Permission error loading image.") }
        } catch (e: OutOfMemoryError) {
            Log.e(TAG, "loadBitmapFromUri: OutOfMemoryError loading bitmap: ${e.message}", e)
            _uiState.update { WasteUiState.Error(uri, null, "Image is too large.") }
        } catch (e: Exception) {
            Log.e(TAG, "loadBitmapFromUri: Generic error loading bitmap: ${e.message}", e)
            _uiState.update { WasteUiState.Error(uri, null, "Could not load image.") }
        }
        // Optional: Implement scaling here if needed
        // e.g., return scaleBitmap(bitmap, 1024, 1024);
        return bitmap
    }

    /**
     * Parses the raw text response from Gemini into a structured ClassificationResult object.
     * Returns null if parsing fails (e.g., Classification is missing).
     */
    @Nullable
    private fun parseClassificationResult(rawText: String?): ClassificationResult? {
        Log.d(TAG, "parseClassificationResult: Attempting to parse raw text.")
        if (rawText.isNullOrBlank()) {
            Log.w(TAG, "parseClassificationResult: Raw text is null or blank.")
            return null
        }

        var obj: String? = null
        var classification: String? = null
        var reason: String? = null

        // Split into lines and process each line
        rawText.trim().lines().forEach { line ->
            val trimmedLine = line.trim()
            when {
                // Use substringAfter for slightly more robust parsing
                trimmedLine.startsWith("Object:", ignoreCase = true) -> {
                    obj = trimmedLine.substringAfter("Object:", "").trim() // Provide default "" if missing
                    if (obj.equals("[Object Name]", ignoreCase = true)) obj = null // Reset if placeholder
                }
                trimmedLine.startsWith("Classification:", ignoreCase = true) -> {
                    classification = trimmedLine.substringAfter("Classification:", "").trim()
                    if (classification.equals("[Recycling/Trash/Compost/Uncertain/Check Locally]", ignoreCase = true)) classification = null
                }
                trimmedLine.startsWith("Reason:", ignoreCase = true) -> {
                    reason = trimmedLine.substringAfter("Reason:", "").trim()
                    if (reason.equals("[Brief Explanation]", ignoreCase = true)) reason = null
                }
            }
        }

        // Classification is considered essential for a meaningful result
        if (classification.isNullOrBlank()) {
            Log.w(TAG, "parseClassificationResult: Parsing failed - Classification missing. Raw: $rawText")
            return null
        }

        Log.d(TAG, "parseClassificationResult: Parsing successful.")
        // Return the structured result, providing defaults for missing optional fields
        return ClassificationResult(
            classification = classification!!, // Known to be non-blank here
            identifiedObject = obj ?: "Unknown Item", // Use friendly default
            reason = reason ?: "No specific tip provided." // Use friendly default
        )
    }
}
