document.addEventListener('DOMContentLoaded', () => {
    // Get references to elements needed for QR functionality
    const qrButton = document.getElementById('qr-button');
    const qrOverlay = document.getElementById('qr-overlay');
    const qrContainer = document.getElementById('qr-code-container');

    // --- IMPORTANT CHECK ---
    // Only add event listeners if all the necessary elements are found on the current page
    if (qrButton && qrOverlay && qrContainer) {

        // Show overlay when button is clicked
        qrButton.addEventListener('click', () => {
            qrOverlay.classList.add('visible');
        });

        // Hide overlay when the background is clicked
        qrOverlay.addEventListener('click', (event) => {
            if (event.target === qrOverlay) {
                qrOverlay.classList.remove('visible');
            }
        });

        // Prevent clicks inside the container from closing the overlay
        qrContainer.addEventListener('click', (event) => {
            event.stopPropagation();
        });

        // Optional: Hide overlay with the Escape key
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && qrOverlay.classList.contains('visible')) {
                qrOverlay.classList.remove('visible');
            }
        });

    } else {
        // Optional: Log if elements aren't found (useful for debugging)
        // console.log("QR code elements not found on this page. Listeners not attached.");
    }
});