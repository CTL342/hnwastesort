Prerequisites:

Python 3: Make sure you have Python 3 installed on your computer. You can check by opening your terminal or command prompt and typing python --version or python3 --version. If you don't have it, download it from python.org.
pip: Python's package installer. It usually comes with Python 3. You can check with pip --version or python -m pip --version.
Google API Key: You need a valid Google API key that is enabled for the Gemini API (specifically including access to vision models like gemini-1.5-flash-latest or gemini-pro-vision). Make sure billing might be enabled on your Google Cloud project if required. Get your key from Google AI Studio or the Google Cloud Console.
Setup Instructions:

Create Project Folder:

Create a new folder on your computer for this project (e.g., smart_sort_app).
Place all the code files (index.html, search.html, style.css, script.js, app.py) directly inside this folder.
Create uploads Folder:

Inside your project folder (smart_sort_app), create an empty subfolder named exactly uploads. The app.py script will use this to temporarily save images during analysis.
Install Python Libraries:

Open your Terminal or Command Prompt.
Navigate (cd) into your project folder (e.g., cd path/to/smart_sort_app).
Run the following command to install Flask, CORS support, the Google AI library, Pillow for image handling, and OpenCV (which might be needed by underlying dependencies or future image processing):
Bash

pip install Flask flask-cors google-generativeai Pillow opencv-python
(Wait for the installation to complete successfully.)
Set Google API Key Environment Variable:

This is crucial for app.py to authenticate with Google AI.
In the SAME terminal window you will use to run app.py in the next section, set the variable using the command appropriate for your system.

Execution Instructions:

Run the Python Backend Server:

Make sure you are still in your project folder (smart_sort_app) in the same terminal where you set the GOOGLE_API_KEY.
Run the Flask application:
Bash

python app.py
You should see output indicating the AI model loaded (hopefully successfully!) and the server starting, typically like:
AI Vision Model loaded successfully.
Starting Smart Sorter API server (Text & Image) on http://YOUR IP ADDRESS
Press CTRL+C to stop the server.

Login (Simulated): On the search.html page, click the "Login" button in the top right. Enter user for the username and password for the password when prompted. The navbar should update to show "Welcome, user!" and the points counters (starting at 0).
Text Search: Select a location from the dropdown, type an item name (e.g., "plastic bottle", "styrofoam") in the search bar, and click "Classify". The results (based on the example rules in app.py for that location) should appear below. If logged in and successful, points should increase.
Image Upload: Click the "Upload" button (middle button, bottom right), select an image file from your computer. The filename will briefly appear, and then the image analysis results from Gemini should appear in the results area. If logged in and successful, points should increase (by 5 in the example).
Camera: Click the "Camera" button (top button, bottom right). Your browser should ask for permission to use the camera. Allow it. A modal window showing your camera feed should appear. Aim it at an object, click "Capture & Analyze". The modal will close, and the analysis results should appear. If logged in and successful, points should increase. (Requires HTTPS or localhost usually).
QR Code: Click the QR code button (bottom button, bottom right). An overlay with a placeholder QR code should appear. Click outside the white box or press 'Escape' to close it.
Logout (Simulated): Click the "Logout" button in the navbar. Points will reset to 0 (in the browser), and the login button will reappear.
Stopping the Application:

Go back to the terminal window running python app.py and press Ctrl+C.
If you started the second server (python -m http.server), go to that terminal and press Ctrl+C.
