// Complete script.js file - Simplified points system with hardcoded credentials

document.addEventListener('DOMContentLoaded', () => {

    // --- Hardcoded Credentials (DEMO ONLY - NOT SECURE) ---
    const hardcodedUsername = 'user';
    const hardcodedPassword = 'password';

    // --- State Variables (Local - Reset on Refresh) ---
    let isLoggedIn = false;
    let currentUsername = '';
    let userPoints = 0;

    // --- Elements ---
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-bar');
    const locationSelect = document.getElementById('location-select');
    const resultsOutput = document.getElementById('results-output');
    // Navbar Auth Elements (Exist on both pages now potentially)
    const loginButton = document.getElementById('login-button');
    const userInfoDiv = document.getElementById('user-info');
    const usernameDisplay = document.getElementById('username-display');
    const pointsDisplay = document.getElementById('points-display'); // Top-right points
    const logoutButton = document.getElementById('logout-button');
    const brandPointsDisplay = document.getElementById('brand-points-display'); // Under-logo points container
    const brandPointsValue = document.getElementById('brand-points-value'); // Under-logo points value span
    // Other buttons/modals...
    const fileUploadInput = document.getElementById('file-upload-input');
    const fileInfoArea = document.getElementById('file-info');
    const cameraButton = document.getElementById('camera-button');
    const qrButton = document.getElementById('qr-button');
    const qrOverlay = document.getElementById('qr-overlay');
    const qrContainer = document.getElementById('qr-code-container');
    const cameraModal = document.getElementById('camera-modal');
    const videoElement = document.getElementById('camera-video');
    const canvasElement = document.getElementById('camera-canvas');
    const captureButton = document.getElementById('capture-button');
    const closeCameraButton = document.getElementById('close-camera-button');
    let currentStream = null;

    // --- Update Navbar UI ---
    function updateNavbarUI() {
        // Update top-right auth section (Login button OR User Info)
        // Check elements exist first, as this runs on both pages
        if (loginButton && userInfoDiv) {
             if (isLoggedIn) {
                 loginButton.style.display = 'none';
                 userInfoDiv.style.display = 'flex';
                 if(usernameDisplay) usernameDisplay.textContent = currentUsername;
             } else {
                 loginButton.style.display = 'inline-block';
                 userInfoDiv.style.display = 'none';
             }
        }
         // Update under-logo points display
         if (brandPointsDisplay) {
             if (isLoggedIn) {
                 brandPointsDisplay.style.display = 'block'; // Show points under logo
             } else {
                 brandPointsDisplay.style.display = 'none'; // Hide points under logo
             }
         }
         // Always ensure points are up-to-date when UI changes
         updatePointsDisplay();
    }

    // --- Update Points Display (Both Locations) ---
    function updatePointsDisplay() {
        // Check if elements exist before trying to update
        if (pointsDisplay) {
            pointsDisplay.textContent = userPoints;
        }
         if (brandPointsValue) {
            brandPointsValue.textContent = userPoints;
        }
    }

    // --- Login Logic (Simplified) ---
    if (loginButton) { // Only add listener if button exists (search.html)
        loginButton.addEventListener('click', () => {
            const enteredUsername = prompt("Enter username:", "user");
            if (enteredUsername === null) return;
            const enteredPassword = prompt("Enter password:", "password");
            if (enteredPassword === null) return;

            if (enteredUsername === hardcodedUsername && enteredPassword === hardcodedPassword) {
                isLoggedIn = true;
                currentUsername = enteredUsername;
                userPoints = 0; // Reset points on login
                alert(`Login successful! Welcome, ${currentUsername}.`);
                updateNavbarUI(); // Update display immediately
            } else {
                alert("Invalid credentials.");
                isLoggedIn = false; // Ensure logged out
                updateNavbarUI();
            }
        });
    }

    // --- Logout Logic (Simplified) ---
    if (logoutButton) { // Only add listener if button exists (search.html initially, maybe index.html later if needed)
        logoutButton.addEventListener('click', () => {
            isLoggedIn = false;
            currentUsername = '';
            userPoints = 0; // Points are lost on logout in this simple version
            alert("Logged out.");
            updateNavbarUI();
        });
    }


    // --- Text Search Functionality ---
    if (searchForm && searchInput && locationSelect && resultsOutput) {
        searchForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const query = searchInput.value.trim();
            const locationValue = locationSelect.value;
            if (!locationValue) { alert('Please select a location.'); resultsOutput.innerHTML = '<p>Please select a location.</p>'; return; }
            if (query) {
                 fetchTextResults(query, locationValue);
            } else { resultsOutput.innerHTML = '<p>Please enter an item.</p>'; }
        });
    }

    // --- Text Search API Call ---
    async function fetchTextResults(query, location) {
        resultsOutput.innerHTML = '<p><i>Searching rules...</i></p>';
        let apiUrl = `http://127.0.0.1:5000/sort?query=${encodeURIComponent(query)}`;
        if (location) { apiUrl += `&location=${encodeURIComponent(location)}`; }

        try {
            // No Auth header needed for this simplified version
            const response = await fetch(apiUrl);
            if (!response.ok) { throw new Error(`Server error: ${response.status}`); }
            const data = await response.json();
            const locationDisplayText = locationSelect.options[locationSelect.selectedIndex].text;
            displayTextResults(data, locationDisplayText); // Call display function

            // Award point if successful and "logged in"
            if (data.status === 'found' && isLoggedIn) {
                userPoints += 1; // Increment JS variable
                updatePointsDisplay(); // Update both displays
                console.log(`Point awarded for text search! New total: ${userPoints}`);
            }

        } catch (error) { console.error("Error fetching text results:", error); resultsOutput.innerHTML = `<p class="error">Could not connect. Is app.py running?</p><p><small>${error}</small></p>`; }
    }

    // --- Display Text Search Results ---
    function displayTextResults(data, locationDisplayText) {
         let html = '';
         html += `<p><strong>Query:</strong> ${escapeHTML(data.query)}</p>`;
         html += `<p><strong>Location:</strong> ${escapeHTML(data.location)}</p><hr>`;
         switch (data.status) {
              case 'found':
                 html += `<p><strong>Identified:</strong> ${escapeHTML(data.keyword_identified)}</p>`;
                 if (data.alias_resolution) html += `<p><em>(Interpreted as: ${escapeHTML(data.alias_resolution)})</em></p>`;
                 html += `<p class="category-${data.category.toLowerCase().replace('/','-').replace(' ','-')}"><strong>Category:</strong> ${escapeHTML(data.category)}</p>`;
                 html += `<p><strong>Notes:</strong> ${escapeHTML(data.notes || 'N/A')} <em>(Based on ${escapeHTML(data.rules_source || 'Selected Location')} Rules)</em></p>`;
                 break;
             case 'suggestion_found':
                 html += `<p>For ${escapeHTML(data.location)}, did you mean this?</p><button class="suggestion-btn" data-suggestion="${escapeHTML(data.suggestion)}" data-location-value="${escapeHTML(data.location_value)}">${escapeHTML(data.suggestion)}</button>`;
                 break;
            case 'multiple_suggestions_found':
                  html += `<p>For ${escapeHTML(data.location)}, did you mean one of these?</p>`;
                  data.suggestions.forEach(sug => { html += `<button class="suggestion-btn" data-suggestion="${escapeHTML(sug)}" data-location-value="${escapeHTML(data.location_value)}">${escapeHTML(sug)}</button> `; });
                  break;
            case 'not_found':
                 html += `<p class="category-unknown"><strong>Category:</strong> ${escapeHTML(data.category)}</p>`;
                 html += `<p><strong>Notes:</strong> ${escapeHTML(data.notes || 'N/A')} <em>(Based on ${escapeHTML(data.rules_source || 'Selected Location')} Rules)</em></p>`;
                 break;
            case 'error':
                   html += `<p class="error"><strong>Error:</strong> ${escapeHTML(data.notes || data.error || 'Unknown Error')}</p>`;
                   break;
             default:
                  console.warn("Received unknown status:", data.status); html += '<p class="error">Received an unknown response.</p>';
         }
         if (resultsOutput) { resultsOutput.innerHTML = html; addSuggestionListeners(); }
    }

    // --- Text Search Suggestion Listeners ---
    function addSuggestionListeners() {
          const currentResultsArea = document.getElementById('results-output');
        if (!currentResultsArea) return;
        currentResultsArea.querySelectorAll('.suggestion-btn').forEach(button => {
            const newButton = button.cloneNode(true); button.parentNode.replaceChild(newButton, button);
            newButton.addEventListener('click', function() {
                const suggestion = this.dataset.suggestion;
                const locationValue = this.dataset.locationValue;
                if(searchInput) searchInput.value = suggestion;
                if(locationSelect && locationValue) { if ([...locationSelect.options].some(option => option.value === locationValue)) { locationSelect.value = locationValue; } }
                fetchTextResults(suggestion, locationValue); // Use text fetch
            });
        });
    }

    // --- File Upload Functionality ---
    if (fileUploadInput && fileInfoArea) {
         fileUploadInput.addEventListener('change', function(event) {
            if (event.target.files && event.target.files.length > 0) {
                const file = event.target.files[0];
                fileInfoArea.textContent = `Selected: ${file.name}`;
                fileInfoArea.classList.add('visible');
                setTimeout(() => { fileInfoArea.classList.remove('visible'); }, 5000);
                const formData = new FormData();
                formData.append('image_file', file);
                uploadAndAnalyze(formData); // Call upload/analysis function
            } else { /* Clear info */ fileInfoArea.textContent = ''; fileInfoArea.classList.remove('visible'); }
        });
     }

    // --- Camera Functionality ---
    if (cameraButton && cameraModal && videoElement && canvasElement && captureButton && closeCameraButton) {
        cameraButton.addEventListener('click', startCamera);
        closeCameraButton.addEventListener('click', stopCameraStream);
        captureButton.addEventListener('click', captureAndAnalyze);
    }

    // --- Start Camera ---
    async function startCamera() {
        if(resultsOutput) resultsOutput.innerHTML = '';
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { alert('Camera API not available.'); return; }
        try {
            const constraints = { video: { facingMode: "environment" } }; // Prefer back camera
            currentStream = await navigator.mediaDevices.getUserMedia(constraints);
            videoElement.srcObject = currentStream; videoElement.style.transform = 'scaleX(1)'; // Ensure back camera isn't flipped
            cameraModal.classList.add('visible');
        } catch (err) {
             console.error("Error accessing environment camera:", err);
             try { // Fallback to any camera
                  currentStream = await navigator.mediaDevices.getUserMedia({ video: true });
                  videoElement.srcObject = currentStream; videoElement.style.transform = 'scaleX(-1)'; // Flip front camera
                  cameraModal.classList.add('visible');
             } catch (frontErr) { alert(`Could not access camera. Error: ${frontErr.message || frontErr.name}. Ensure permission granted & check HTTPS.`); }
        }
    }

     // --- Stop Camera Stream ---
     function stopCameraStream() {
         if (currentStream) { currentStream.getTracks().forEach(track => track.stop()); }
         videoElement.srcObject = null; currentStream = null;
         if(cameraModal) cameraModal.classList.remove('visible');
     }

     // --- Capture Frame and Send for Analysis ---
     function captureAndAnalyze() {
          if (!currentStream || !canvasElement || !videoElement) return;
          const videoWidth = videoElement.videoWidth; const videoHeight = videoElement.videoHeight;
          canvasElement.width = videoWidth; canvasElement.height = videoHeight;
          const context = canvasElement.getContext('2d');
          // Handle potential mirroring before drawing
          if (videoElement.style.transform === 'scaleX(-1)') {
              context.translate(videoWidth, 0); context.scale(-1, 1);
          }
          context.drawImage(videoElement, 0, 0, videoWidth, videoHeight);
          // Reset transform if applied before getting blob
           if (videoElement.style.transform === 'scaleX(-1)') {
              context.setTransform(1, 0, 0, 1, 0, 0);
          }
          stopCameraStream(); // Stop stream and hide modal after capture
          canvasElement.toBlob(function(blob) {
              if (blob) {
                  const formData = new FormData();
                  formData.append('image_file', blob, 'camera_capture.jpg');
                  uploadAndAnalyze(formData); // Call common upload function
              } else { if(resultsOutput) resultsOutput.innerHTML = `<p class="error">Failed to capture image.</p>`; }
          }, 'image/jpeg', 0.9); // Specify JPEG format and quality
     }

    // --- Function to Upload Image Data and Analyze ---
    async function uploadAndAnalyze(formData) {
        resultsOutput.innerHTML = '<p><i>Uploading & Analyzing Image...</i></p>';
        const apiUrl = 'http://127.0.0.1:5000/analyze_image';

        try {
            // No Auth header needed
            const response = await fetch(apiUrl, { method: 'POST', body: formData });
            if (!response.ok) { throw new Error(`Server error: ${response.status}`); }
            const data = await response.json(); // Expecting {object, classification, reason, error}
            displayImageAnalysisResult(data);

            // Award point if successful and "logged in"
            if (!data.error && isLoggedIn) {
                 userPoints += 5; // Example: Award 5 points for image analysis
                 updatePointsDisplay(); // Update both displays
                 console.log(`Points awarded for image analysis! New total: ${userPoints}`);
            }
        } catch (error) { console.error("Error uploading/analyzing:", error); resultsOutput.innerHTML = `<p class="error">Failed to analyze. Is app.py running & AI configured?</p><p><small>${error}</small></p>`; }
    }

     // --- Function to Display Image Analysis Results ---
     function displayImageAnalysisResult(data) {
           let html = '<h2>Image Analysis Result</h2><hr>';
           if (data.error) { html += `<p class="error"><strong>Error:</strong> ${escapeHTML(data.error)}</p>`; }
           else {
                html += `<p><strong>Object:</strong> ${escapeHTML(data.object || 'N/A')}</p>`;
                html += `<p class="category-${(data.classification || 'unknown').toLowerCase().replace('/','-').replace(' ','-')}"><strong>Classification:</strong> ${escapeHTML(data.classification || 'N/A')}</p>`;
                html += `<p><strong>Reason:</strong> ${escapeHTML(data.reason || 'N/A')}</p>`;
           }
           if(resultsOutput) resultsOutput.innerHTML = html;
     }

    // --- Helper to escape HTML special characters ---
    function escapeHTML(str) {
        if (typeof str !== 'string') return '';
        const p = document.createElement('p');
        p.appendChild(document.createTextNode(str));
        return p.innerHTML;
    }

    // --- QR Code Functionality ---
    if (qrButton && qrOverlay && qrContainer) {
        qrButton.addEventListener('click', () => { qrOverlay.classList.add('visible'); });
        qrOverlay.addEventListener('click', (event) => { if (event.target === qrOverlay) { qrOverlay.classList.remove('visible'); } });
        qrContainer.addEventListener('click', (event) => { event.stopPropagation(); });
        document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && qrOverlay.classList.contains('visible')) { qrOverlay.classList.remove('visible'); } });
    }

    // --- Initial UI Update on Load ---
    updateNavbarUI(); // Set initial state of navbar login/user info display

}); // End DOMContentLoaded