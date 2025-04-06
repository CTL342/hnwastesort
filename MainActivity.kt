package com.example.waste // <-- Your package

// Android & Core KTX
import android.Manifest
import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.core.content.FileProvider // Needed for camera URI later
import java.io.File // Needed for camera URI later

// Compose UI & Foundation
import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle // Recommended state collection

// Compose Material 3
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.* // Imports common filled icons (like AddAPhoto, Close, ErrorOutline etc.)
// Explicitly import icons if needed and not covered by filled.*, check names carefully:
// import androidx.compose.material.icons.filled.CameraAlt // Make sure this exists or choose another
// import androidx.compose.material.icons.filled.Recycling
// import androidx.compose.material.icons.filled.DeleteOutline
// import androidx.compose.material.icons.filled.Eco
// import androidx.compose.material.icons.filled.HelpOutline
// import androidx.compose.material.icons.filled.WarningAmber // Make sure this exists or choose another
// import androidx.compose.material.icons.filled.PhotoCamera
// import androidx.compose.material.icons.filled.PhotoLibrary
import androidx.compose.material3.* // Imports Scaffold, Card, Button, Text, Icon etc.

// ViewModel & Lifecycle (Add if missing)
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel

// Coil (Image Loading) - Ensure these are correct
import coil.compose.AsyncImage
import coil.request.ImageRequest

// Accompanist Permissions - Ensure these are correct
import com.google.accompanist.permissions.*

// Coroutines
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

// Your Project Classes (VERIFY PACKAGE NAME)
import com.example.waste.R
import com.example.waste.WasteViewModel
import com.example.waste.WasteUiState
import com.example.waste.ui.theme.WasteClassifierTheme // Your Compose Theme

class MainActivity : ComponentActivity() {

    private val TAG = "MainActivity"
    private val viewModel: WasteViewModel by viewModels()

    @OptIn(ExperimentalPermissionsApi::class, ExperimentalMaterial3Api::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d(TAG, "onCreate: Activity starting.")
        setContent {
            WasteClassifierTheme { // Apply your custom theme
                Log.d(TAG, "setContent -> WasteClassifierTheme applying...")
                val uiState by viewModel.uiState.collectAsState()
                Log.d(TAG, "setContent -> Current UI State collected: ${uiState::class.java.simpleName}")

                val cameraPermissionState = rememberPermissionState(Manifest.permission.CAMERA)
                val storagePermission = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    Manifest.permission.READ_MEDIA_IMAGES
                } else {
                    Manifest.permission.READ_EXTERNAL_STORAGE
                }
                val storagePermissionState = rememberPermissionState(storagePermission)
                var showRationaleDialog by rememberSaveable { mutableStateOf<String?>(null) }

                val imagePickerLauncher = rememberLauncherForActivityResult(
                    contract = ActivityResultContracts.PickVisualMedia(),
                    onResult = { uri ->
                        Log.d(TAG, "ImagePicker Result: URI received $uri")
                        viewModel.processImageUri(uri)
                    }
                )
                val context = LocalContext.current
                var tempCameraUri by remember { mutableStateOf<Uri?>(null) }
                val cameraLauncher = rememberLauncherForActivityResult(
                    contract = ActivityResultContracts.TakePicture(),
                    onResult = { success ->
                        Log.d(TAG, "CameraLauncher Result: Success=$success, URI=$tempCameraUri")
                        if (success) {
                            viewModel.processImageUri(tempCameraUri)
                        } else {
                            Log.w(TAG, "Camera capture failed or was cancelled.")
                            Toast.makeText(context, R.string.message_photo_capture_failed, Toast.LENGTH_SHORT).show()
                        }
                    }
                )
                fun getTempUri(): Uri? { // Needs REAL FileProvider implementation
                    Log.w(TAG, "getTempUri: Using placeholder temp URI - Camera WILL NOT WORK without FileProvider!")
                    tempCameraUri = Uri.EMPTY // Placeholder!
                    // TODO: Implement FileProvider correctly here
                    return tempCameraUri
                }

                var showBottomSheet by remember { mutableStateOf(false) }
                val scope = rememberCoroutineScope()
                val modalBottomSheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

                // Main UI Structure using Scaffold
                Scaffold(
                    floatingActionButton = {
                        // FAB is hidden during analysis for clarity
                        if (uiState !is WasteUiState.Analyzing) {
                            FloatingActionButton(
                                onClick = {
                                    Log.d(TAG,"FAB clicked, showing bottom sheet.")
                                    showBottomSheet = true
                                },
                                containerColor = MaterialTheme.colorScheme.primary, // Use primary color
                                contentColor = MaterialTheme.colorScheme.onPrimary // Ensure contrast
                            ) {
                                Icon(
                                    // Use Camera icon for primary action, or AddAPhoto
                                    imageVector = Icons.Filled.CameraAlt,
                                    contentDescription = stringResource(R.string.add_image_fab_description)
                                )
                            }
                        }
                    }
                ) { paddingValues ->
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(paddingValues) // Apply padding for content area
                    ) {
                        // Content switches based on state
                        WasteClassifierScreenContent(
                            uiState = uiState,
                            onClear = {
                                Log.d(TAG, "onClear lambda called, resetting state.")
                                viewModel.resetState()
                            },
                            modifier = Modifier.fillMaxSize()
                        )

                        // Loading indicator centered, overlaying content when analyzing
                        AnimatedVisibility(
                            visible = uiState is WasteUiState.Analyzing,
                            enter = fadeIn(), exit = fadeOut(),
                            modifier = Modifier.align(Alignment.Center)
                        ) {
                            // Use a slightly larger indicator maybe with background scrim
                            Box(modifier = Modifier
                                .size(80.dp)
                                .clip(CircleShape)
                                .background(MaterialTheme.colorScheme.scrim.copy(alpha = 0.3f)),
                                contentAlignment = Alignment.Center
                            ) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(48.dp),
                                    color = MaterialTheme.colorScheme.onPrimaryContainer
                                )
                            }
                        }
                    }
                } // End Scaffold

                // Permission Rationale Dialog (Uses updated strings)
                showRationaleDialog?.let { permissionType ->
                    AlertDialog(
                        onDismissRequest = { showRationaleDialog = null },
                        icon = { Icon(Icons.Filled.Info, null)},
                        title = { Text(stringResource(R.string.permission_dialog_title)) },
                        text = { Text(getRationaleText(permissionType)) },
                        confirmButton = {
                            TextButton(onClick = {
                                Log.d(TAG,"Rationale Dialog: Grant clicked for $permissionType")
                                showRationaleDialog = null
                                when(permissionType) {
                                    "Camera" -> cameraPermissionState.launchPermissionRequest()
                                    "Storage" -> storagePermissionState.launchPermissionRequest()
                                }
                            }) { Text(stringResource(R.string.permission_dialog_grant_button)) }
                        },
                        dismissButton = {
                            TextButton(onClick = {
                                Log.d(TAG,"Rationale Dialog: Deny clicked")
                                showRationaleDialog = null
                            }) { Text(stringResource(R.string.permission_dialog_deny_button)) }
                        }
                    )
                }

                // Bottom Sheet Content (Uses updated strings)
                if (showBottomSheet) {
                    Log.d(TAG, "Composing ModalBottomSheet")
                    ModalBottomSheet(
                        onDismissRequest = {
                            Log.d(TAG,"ModalBottomSheet: Dismiss requested.")
                            showBottomSheet = false
                        },
                        sheetState = modalBottomSheetState
                    ) {
                        // Use standard M3 list items for options
                        Column(modifier = Modifier.padding(bottom = 16.dp)) { // Padding at bottom
                            Text( // Optional Title
                                text = stringResource(R.string.dialog_title_add_image),
                                style = MaterialTheme.typography.titleMedium,
                                modifier = Modifier.padding(start = 16.dp, top = 16.dp, bottom = 8.dp)
                            )
                            HorizontalDivider() // Visual separator
                            ListItem(
                                headlineContent = { Text(stringResource(R.string.dialog_option_take_photo)) },
                                leadingContent = { Icon(Icons.Filled.PhotoCamera, contentDescription = null) },
                                modifier = Modifier.clickable {
                                    Log.d(TAG,"BottomSheet: Take Photo clicked.")
                                    scope.launch { modalBottomSheetState.hide() }.invokeOnCompletion {
                                        if (!modalBottomSheetState.isVisible) {
                                            showBottomSheet = false
                                            Log.d(TAG,"BottomSheet: Take Photo action - handling permission.")
                                            handlePermission(
                                                permissionState = cameraPermissionState,
                                                rationaleTitle = "Camera",
                                                onGranted = {
                                                    Log.d(TAG,"BottomSheet: Camera permission granted, getting URI.")
                                                    val uri = getTempUri() // Needs FileProvider!
                                                    if (uri != null && uri != Uri.EMPTY) {
                                                        Log.d(TAG,"BottomSheet: Launching camera with URI: $uri")
                                                        cameraLauncher.launch(uri)
                                                    } else {
                                                        Log.e(TAG, "BottomSheet: Cannot launch camera - invalid URI from getTempUri (FileProvider needed).")
                                                        Toast.makeText(context, R.string.error_camera_unavailable, Toast.LENGTH_LONG).show()
                                                    }
                                                },
                                                showRationale = { permType ->
                                                    Log.d(TAG,"BottomSheet: Camera permission needs rationale.")
                                                    showRationaleDialog = permType
                                                }
                                            )
                                        }
                                    }
                                }
                            )
                            ListItem(
                                headlineContent = { Text(stringResource(R.string.dialog_option_choose_gallery)) },
                                leadingContent = { Icon(Icons.Filled.PhotoLibrary, contentDescription = null) },
                                modifier = Modifier.clickable {
                                    Log.d(TAG,"BottomSheet: Choose from Gallery clicked.")
                                    scope.launch { modalBottomSheetState.hide() }.invokeOnCompletion {
                                        if (!modalBottomSheetState.isVisible) {
                                            showBottomSheet = false
                                            Log.d(TAG,"BottomSheet: Gallery action - handling permission.")
                                            handlePermission(
                                                permissionState = storagePermissionState,
                                                rationaleTitle = "Storage",
                                                onGranted = {
                                                    Log.d(TAG,"BottomSheet: Storage permission granted, launching image picker.")
                                                    imagePickerLauncher.launch(
                                                        PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)
                                                    )
                                                },
                                                showRationale = { permType ->
                                                    Log.d(TAG,"BottomSheet: Storage permission needs rationale.")
                                                    showRationaleDialog = permType
                                                }
                                            )
                                        }
                                    }
                                }
                            )
                            Spacer(Modifier.height(8.dp)) // Spacer before cancel
                            HorizontalDivider()
                            TextButton(
                                onClick = {
                                    Log.d(TAG,"BottomSheet: Cancel clicked.")
                                    scope.launch { modalBottomSheetState.hide() }.invokeOnCompletion {
                                        if (!modalBottomSheetState.isVisible) {
                                            showBottomSheet = false
                                        }
                                    }
                                },
                                modifier = Modifier.align(Alignment.CenterHorizontally).padding(top = 8.dp)
                            ) {
                                Text(stringResource(R.string.dialog_option_cancel))
                            }
                        }
                    }
                }
            }
        }
    }

    @OptIn(ExperimentalPermissionsApi::class)
    private fun handlePermission(
        permissionState: PermissionState,
        rationaleTitle: String,
        onGranted: () -> Unit,
        showRationale: (String) -> Unit
    ) {
        Log.d(TAG, "handlePermission: Checking status for $rationaleTitle")
        when {
            permissionState.status.isGranted -> {
                Log.d(TAG, "handlePermission: Already granted for $rationaleTitle.")
                onGranted()
            }
            permissionState.status.shouldShowRationale -> {
                Log.d(TAG, "handlePermission: Rationale needed for $rationaleTitle.")
                showRationale(rationaleTitle)
            }
            else -> {
                Log.d(TAG, "handlePermission: Requesting permission for $rationaleTitle.")
                permissionState.launchPermissionRequest()
            }
        }
    }

    // Use updated strings for rationale
    @Composable
    private fun getRationaleText(permissionType: String): String {
        return when(permissionType) {
            "Camera" -> stringResource(R.string.permission_rationale_camera)
            "Storage" -> stringResource(R.string.permission_rationale_storage)
            else -> "This app needs permission to function." // Generic fallback
        }
    }

}

// --- Composable UI Components ---

@Composable
fun WasteClassifierScreenContent(
    uiState: WasteUiState,
    onClear: () -> Unit,
    modifier: Modifier = Modifier
) {
    Log.d("ComposeUI", "WasteClassifierScreenContent composing. State: ${uiState::class.java.simpleName}")
    Column(
        modifier = modifier.padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Determines which main content area to show
        AnimatedContent(
            targetState = uiState is WasteUiState.Idle, // Boolean state: isIdle?
            transitionSpec = {
                // Fade in/out when switching between home and active states
                fadeIn(animationSpec = tween(500)) togetherWith fadeOut(animationSpec = tween(200))
            },
            label = "HomeScreen/ActiveScreen Transition"
        ) { isIdle ->
            if (isIdle) {
                Log.d("ComposeUI", "WasteClassifierScreenContent -> Composing HomeScreen")
                HomeScreen()
            } else {
                // Active state content (Image + Result/Error Card)
                val imageUri = when (uiState) { /* ... */ is WasteUiState.ImageSelected -> uiState.imageUri; is WasteUiState.Analyzing -> uiState.imageUri; is WasteUiState.Success -> uiState.imageUri; is WasteUiState.Error -> uiState.imageUri; else -> null }
                val bitmap = when (uiState) { /* ... */ is WasteUiState.ImageSelected -> uiState.bitmap; is WasteUiState.Analyzing -> uiState.bitmap; is WasteUiState.Success -> uiState.bitmap; is WasteUiState.Error -> uiState.bitmap; else -> null }

                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Log.d("ComposeUI", "WasteClassifierScreenContent -> Composing ImagePreviewCard (Visible=${imageUri != null || bitmap != null})")
                    ImagePreviewCard(
                        imageUri = imageUri, bitmap = bitmap,
                        showClearButton = uiState !is WasteUiState.Analyzing,
                        onClearClick = onClear
                    )
                    Spacer(modifier = Modifier.height(16.dp))

                    // Animated visibility for the result/error card within the active state
                    AnimatedVisibility(
                        visible = uiState is WasteUiState.Success || uiState is WasteUiState.Error,
                        enter = slideInVertically(initialOffsetY = { it / 2 }) + fadeIn(),
                        exit = slideOutVertically(targetOffsetY = { it / 2 }) + fadeOut()
                    ) {
                        Log.d("ComposeUI", "WasteClassifierScreenContent -> Composing Result/Error Card")
                        when (uiState) {
                            is WasteUiState.Success -> ResultCard(
                                classification = uiState.classification,
                                identifiedObject = uiState.identifiedObject,
                                reason = uiState.reason
                            )
                            is WasteUiState.Error -> ErrorCard(message = uiState.message)
                            else -> Spacer(Modifier.height(0.dp)) // Empty spacer if somehow visible in wrong state
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun HomeScreen(modifier: Modifier = Modifier) {
    Log.d("ComposeUI", "HomeScreen composing.")
    Column(
        modifier = modifier.fillMaxHeight(0.75f), // Occupy more height
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center // Center vertically within its space
    ) {
        // App Title (Optional, could use AppBar)
        Text(
            text = stringResource(R.string.app_greeting),
            style = MaterialTheme.typography.headlineMedium, // Good size
            color = MaterialTheme.colorScheme.primary
        )
        Spacer(modifier = Modifier.height(32.dp)) // Adjust spacing

        // Use the new friendly placeholder
        Image(
            painter = painterResource(id = R.drawable.baseline_recycling_24), // <-- USE NEW DRAWABLE
            contentDescription = stringResource(R.string.home_placeholder_description),
            modifier = Modifier
                .size(200.dp) // Make it larger
                .padding(bottom = 16.dp), // Add padding below
            // No tint needed if the drawable has its own colors
            // colorFilter = ColorFilter.tint(MaterialTheme.colorScheme.secondary)
        )

        // Instruction Text
        Text(
            text = stringResource(R.string.home_instruction),
            style = MaterialTheme.typography.titleMedium, // Slightly larger instruction
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(horizontal = 24.dp) // More horizontal padding
        )
    }
}

@Composable
fun ImagePreviewCard(
    imageUri: Uri?,
    bitmap: Bitmap?,
    showClearButton: Boolean,
    onClearClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Log.d("ComposeUI", "ImagePreviewCard composing. URI: $imageUri, Bitmap null: ${bitmap == null}, ShowClear: $showClearButton")
    Card( // Use Card from Material 3
        modifier = modifier
            .fillMaxWidth()
            .aspectRatio(4f / 3f), // Keep aspect ratio
        shape = RoundedCornerShape(16.dp), // Keep rounded corners
        elevation = CardDefaults.cardElevation(defaultElevation = 6.dp) // Slightly more elevation
    ) {
        Box(modifier = Modifier.fillMaxSize()) {
            AsyncImage(
                model = ImageRequest.Builder(LocalContext.current)
                    .data(bitmap ?: imageUri) // Prioritize bitmap
                    .error(R.drawable.baseline_recycling_24) // Use friendly placeholder on error
                    .crossfade(true)
                    .build(),
                contentDescription = stringResource(R.string.image_preview_description),
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop // Crop is usually good for previews
            )

            // Clear Button (keep as is, maybe adjust tint/bg based on theme)
            AnimatedVisibility(
                visible = showClearButton,
                modifier = Modifier.align(Alignment.TopEnd).padding(8.dp),
                enter = scaleIn(), exit = scaleOut()
            ) {
                FloatingActionButton(
                    onClick = onClearClick,
                    modifier = Modifier.size(40.dp),
                    shape = CircleShape,
                    containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.7f), // Use theme color slightly transparent
                    contentColor = MaterialTheme.colorScheme.onSurfaceVariant
                ) {
                    Icon(Icons.Filled.Close, contentDescription = stringResource(R.string.clear_image_button_description))
                }
            }
        }
    }
}

@Composable
fun ResultCard(
    classification: String,
    identifiedObject: String,
    reason: String,
    modifier: Modifier = Modifier
) {
    Log.d("ComposeUI", "ResultCard composing. Classification: $classification")
    val resultType = getResultType(classification)
    val icon = getResultIcon(resultType)
    val backgroundColor = getResultColor(resultType) // Get the color based on type

    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        colors = CardDefaults.cardColors(containerColor = backgroundColor) // Apply dynamic bg color
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.Top // Align icon to top with text
        ) {
            Icon(
                imageVector = icon,
                contentDescription = classification, // Use classification as description
                modifier = Modifier.size(40.dp).padding(top = 4.dp), // Slightly smaller icon, add padding
                tint = LocalContentColor.current.copy(alpha = 0.8f) // Use local content color, slightly transparent
            )
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                // Use the updated labels from strings.xml
                Text(
                    text = stringResource(R.string.result_label_disposal),
                    style = MaterialTheme.typography.labelSmall, // Small label style
                    color = LocalContentColor.current.copy(alpha = 0.7f) // Muted label color
                )
                Text(
                    text = classification,
                    style = MaterialTheme.typography.titleMedium, // Keep classification clear
                    color = LocalContentColor.current // Use local content color for readability
                )
                Spacer(modifier = Modifier.height(8.dp)) // More spacing

                Text(
                    text = stringResource(R.string.result_label_item),
                    style = MaterialTheme.typography.labelSmall,
                    color = LocalContentColor.current.copy(alpha = 0.7f)
                )
                Text(
                    text = identifiedObject,
                    style = MaterialTheme.typography.bodyMedium,
                    color = LocalContentColor.current
                )
                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = stringResource(R.string.result_label_tip),
                    style = MaterialTheme.typography.labelSmall,
                    color = LocalContentColor.current.copy(alpha = 0.7f)
                )
                Text(
                    text = reason,
                    style = MaterialTheme.typography.bodySmall, // Keep reason slightly smaller
                    color = LocalContentColor.current
                )
            }
        }
    }
}

@Composable
fun ErrorCard(
    message: String,
    modifier: Modifier = Modifier
) {
    Log.d("ComposeUI", "ErrorCard composing. Message: $message")
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer) // Use theme error color
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                // Use a slightly less alarming icon? Or keep warning.
                imageVector = Icons.Filled.WarningAmber, // Example alternative
                contentDescription = stringResource(R.string.error_card_title),
                modifier = Modifier.size(40.dp), // Match result card icon size
                tint = MaterialTheme.colorScheme.onErrorContainer // Ensure contrast
            )
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text(
                    text = stringResource(R.string.error_card_title), // "Uh Oh!"
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onErrorContainer
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = message, // Show the specific friendly error message
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onErrorContainer
                )
            }
        }
    }
}


// --- Result Styling Helpers ---
enum class ResultType { RECYCLE, TRASH, COMPOST, UNCERTAIN, ERROR }

fun getResultType(classification: String): ResultType { /* ... Unchanged ... */
    val lowerCase = classification.lowercase(); return when { lowerCase.contains("recycling") -> ResultType.RECYCLE; lowerCase.contains("trash") -> ResultType.TRASH; lowerCase.contains("compost") -> ResultType.COMPOST; lowerCase.contains("uncertain") || lowerCase.contains("check locally") -> ResultType.UNCERTAIN; else -> ResultType.UNCERTAIN } }

@Composable
fun getResultColor(type: ResultType): Color {
    // Use Material Theme colors for better adaptability (light/dark mode)
    // Adjust these based on your defined theme colors (Color.kt)
    return when (type) {
        ResultType.RECYCLE -> Color(0xFFB9F6CA) // Brighter Green
        ResultType.TRASH -> Color(0xFFCFD8DC) // Slightly different Gray
        ResultType.COMPOST -> Color(0xFFD7CCC8) // Keep light brown
        ResultType.UNCERTAIN -> Color(0xFFFFECB3) // Brighter Yellow
        ResultType.ERROR -> MaterialTheme.colorScheme.errorContainer // Standard error bg
    }
}

fun getResultIcon(type: ResultType): ImageVector {
    // Keep standard icons for clarity unless you have custom friendly ones
    return when (type) {
        ResultType.RECYCLE -> Icons.Filled.Recycling
        ResultType.TRASH -> Icons.Filled.DeleteOutline
        ResultType.COMPOST -> Icons.Filled.Eco // Or Leaf from extended icons
        ResultType.UNCERTAIN -> Icons.Filled.HelpOutline
        ResultType.ERROR -> Icons.Filled.WarningAmber // Changed icon
    }
}

// --- Preview Composable ---
@Preview(showBackground = true, name = "Idle Home Screen")
@Composable
fun IdlePreview() {
    WasteClassifierTheme {
        WasteClassifierScreenContent(uiState = WasteUiState.Idle, onClear = {})
    }
}

@Preview(showBackground = true, name = "Result Success (Recycle)")
@Composable
fun SuccessPreviewRecycle() {
    WasteClassifierTheme {
        WasteClassifierScreenContent(
            uiState = WasteUiState.Success(
                imageUri = Uri.EMPTY, classification = "Recycling ♻️", // Example with emoji
                identifiedObject = "Plastic Water Bottle",
                reason = "Most places recycle #1 and #2 plastics. Make sure it's empty!"
            ), onClear = {} )
    }
}

@Preview(showBackground = true, name = "Result Error Screen")
@Composable
fun ErrorPreview() {
    WasteClassifierTheme {
        WasteClassifierScreenContent(
            uiState = WasteUiState.Error(
                imageUri = Uri.EMPTY,
                message = stringResource(R.string.error_network) // Use friendly string
            ), onClear = {} )
    }
}