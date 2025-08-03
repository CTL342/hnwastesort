# Smart Sort API Backend

This repository contains the Python Flask backend for the Smart Sort application. The server provides the core logic for waste classification through two primary methods: a rule-based text search and an AI-powered image analysis service using the Google Gemini API.

---

## Core Features

-   **RESTful API:** Exposes simple endpoints for easy integration with a frontend client.
-   **Rule-Based Text Classification:** Utilizes a comprehensive set of predefined rules for various localities (including DC, Fairfax County, Arlington County, and others) to provide accurate, location-specific sorting instructions.
-   **AI Image Analysis:** Integrates the `gemini-1.5-flash-latest` model to identify and classify objects from user-uploaded images in real-time.
-   **Scalable Structure:** Easily extendable to include new locations or update existing disposal rules by modifying the data dictionaries.

---

## Technology Stack

-   **Backend:** Python 3
-   **Framework:** Flask
-   **AI Service:** Google Gemini API
-   **Libraries:** `google-generativeai`, `Pillow`, `Flask-Cors`

---

## Prerequisites

Before proceeding, ensure your development environment meets the following requirements.

### 1. Python 3.x and pip

This application requires Python 3 to run. The package installer, `pip`, is typically included with modern Python installations.

**How to Install Python:**

1.  **Download:** Go to the official Python website: [python.org/downloads/](https://www.python.org/downloads/)
2.  **Run Installer:** Download the latest Python 3 installer for your operating system (Windows or macOS) and run it.
    -   **On Windows:** Make sure to check the box that says **"Add Python to PATH"** during the installation process.
3.  **Verify Installation:** Once installed, open your terminal or Command Prompt and verify the installation by running:
    ```bash
    python --version
    ```
    or on some systems:
    ```bash
    python3 --version
    ```
    You should see a version number like `Python 3.x.x`. You can verify `pip` with `pip --version`.

### 2. Google API Key

A valid Google API key with the Gemini API enabled is required for the image analysis functionality. This can be obtained from Google AI Studio or the Google Cloud Console.

---

## Setup and Installation

Follow these steps to configure the project on your local machine.

### 1. Project Structure

Create a root folder for the project and a necessary subfolder for image uploads.

```bash
# Create the main project directory
mkdir smart_sort_app

# Navigate into the new directory
cd smart_sort_app

# Create the folder for temporary image uploads
mkdir uploads
```

Place the app.py script and any frontend files (index.html, style.css, etc.) inside the smart_sort_app directory.

### 2. Install Dependencies

Install the required Python libraries using pip:

```bash
pip install Flask flask-cors google-generativeai Pillow opencv-python
```

### 3. Environment Configuration

The application requires your Google API Key to be set as an environment variable. This is a critical step for authenticating with the Gemini API. Execute the appropriate command for your operating system in the terminal session you will use to run the server.

* macOS / Linux:

```bash
export GOOGLE_API_KEY='YOUR_API_KEY_HERE'
```

* Windows (Command Prompt):

```bash
set GOOGLE_API_KEY=YOUR_API_KEY_HERE
```

* Windows (PowerShell):

```bash
$env:GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```

Note: Replace YOUR_API_KEY_HERE with your actual API key.


## Execution

### 1. Run the server

From the root of your project directory (smart_sort_app), execute the following command to start the Flask server:

```bash
python app.py
```

Upon successful startup, you will see output similar to the following:

```bash
AI Vision Model loaded successfully.
Starting Smart Sorter API server (Text & Image) on [http://127.0.0.1:5000](http://127.0.0.1:5000)
Press CTRL+C to stop the server.
```

The backend is now running and ready to accept requests.

### 2. Application Usage

With the server running, a frontend client can interact with the following API endpoints:

* Text Search: Send a GET request to /sort with location and query parameters to get rule-based classification.
    * Example http://127.0.0.1:5000/sort?location=fairfax_va&query=plastic%20bottle
* Image Analysis: Send a POST request to /analyze_image with a multipart/form-data payload containing the image_file to get an AI-based classification.

### 3. Stopping the Application

To terminate the server process, return to the terminal window where it is running and press Ctrl+C.
