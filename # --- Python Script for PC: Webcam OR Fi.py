# --- Python Script for PC: Webcam OR File Input ---
# Filename: smart_analyzer_pc.py

import cv2
import google.generativeai as genai
import PIL.Image
import os
import time
import textwrap # For wrapping long text lines on screen

# --- Configuration & AI Model Setup ---
# !!! IMPORTANT: Make sure GOOGLE_API_KEY environment variable is set BEFORE running !!!
try:
    # 1. GET API KEY: Reads the key you set in your terminal environment.
    GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    # 2. CONFIGURE LIBRARY: Tells the Google AI library to use your key.
    genai.configure(api_key=GOOGLE_API_KEY)
    # 3. INITIALIZE MODEL: Connects to a specific Gemini model capable of understanding images.
    #    'gemini-1.5-flash-latest' is a good, fast vision model (as of early 2025).
    #    Check Google AI documentation for the latest recommended vision models.
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("AI Model loaded successfully.") # Confirmation message
except KeyError:
    # Handles error if the API key wasn't set in the environment.
    print("\n############################################################")
    print("ERROR: GOOGLE_API_KEY environment variable not set.")
    print("Please set the environment variable and run the script again.")
    print("How to set (examples):")
    print("  Linux/macOS: export GOOGLE_API_KEY='Your_Key_Here'")
    print("  Windows CMD: set GOOGLE_API_KEY=Your_Key_Here")
    print("  Windows PowerShell: $env:GOOGLE_API_KEY='Your_Key_Here'")
    print("Replace 'Your_Key_Here' with your actual key.")
    print("############################################################\n")
    exit() # Stop the script if key is missing.
except Exception as e:
    # Handles other errors during setup (e.g., invalid key, network issue).
    print(f"ERROR: Could not initialize AI model: {e}")
    print("This might be due to an invalid API key or network issues.")
    exit() # Stop the script if setup fails.

# --- Helper Function to Draw Text (for webcam mode) ---
def draw_text(img, text, pos=(10, 30), scale=0.7, thick=2, color=(255, 255, 255), bg_color=(0, 0, 0)):
    """Draws text (potentially multi-line) on an image with a background."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    # Wrap text automatically based on width
    wrapped_text = textwrap.wrap(text, width=60) # Adjust width if needed
    x, y = pos
    # Draw each line separately
    for i, line in enumerate(wrapped_text):
        text_size, _ = cv2.getTextSize(line, font, scale, thick)
        text_w, text_h = text_size
        # Calculate position for the current line
        line_y = y + i * int(text_h * 1.5)
        # Calculate coordinates ensuring they stay within image boundaries
        bg_tl = (x, max(0, line_y - text_h - 5)) # Background Top-Left
        bg_br = (min(img.shape[1], x + text_w + 5), min(img.shape[0], line_y + 5)) # Background Bottom-Right
        text_org = (x, min(img.shape[0] - 5, line_y)) # Text Origin

        # Draw black background rectangle
        cv2.rectangle(img, bg_tl, bg_br, bg_color, -1)
        # Draw white text
        cv2.putText(img, line, text_org, font, scale, color, thick)

# --- Function to Analyze Image (Handles the actual AI communication) ---
def analyze_image_with_ai(image_path):
    """Opens an image, sends it to Gemini with a prompt, returns the result."""
    print(f"\nAnalyzing image: {image_path}...")
    try:
        # 1. OPEN IMAGE: Uses the Pillow library (PIL) to open the image file.
        img_pil = PIL.Image.open(image_path)

        # 2. DEFINE PROMPT: Creates the instructions for the AI.
        prompt = """
        From the provided image, identify the single, main object clearly visible. State the object's name.
        Based on common US recycling guidelines (mention rules can vary by location, especially for specific plastics like #3-#7),
        classify this object as 'Recycling', 'Trash', or 'Uncertain/Check Locally'.
        Provide a brief reason for the classification (max 1-2 short sentences).
        Format your response exactly like this, with each part on a new line:
        Object: [Object Name]
        Classification: [Recycling/Trash/Uncertain/Check Locally]
        Reason: [Brief Explanation]
        """

        # 3. *** CALL GEMINI API ***: This is the key step. Sends the prompt and the image
        #    data to the Google servers where the Gemini model runs.
        response = model.generate_content([prompt, img_pil])

        # 4. PROCESS RESPONSE: Checks if the AI sent back valid content.
        print("AI analysis complete.")
        if response.parts:
            # Success: Return the text part of the AI's response.
            return response.text.strip()
        else:
            # Handle cases where the API blocked the request (e.g., safety filters)
            try:
                 block_reason = response.prompt_feedback.block_reason
                 block_message = f"Analysis Blocked by API. Reason: {block_reason}"
                 print(block_message)
                 return block_message
            except Exception:
                 # Handle other cases of empty responses.
                 msg = "Analysis Failed: Received empty response from AI."
                 print(msg)
                 return msg
    except FileNotFoundError:
        # Handle error if the image file doesn't exist.
        msg = f"Error: Image file not found at '{image_path}'"
        print(msg)
        return msg
    except Exception as e:
        # Handle other potential errors (image loading issues, network problems, API errors).
        msg = f"Error during AI analysis: {e}"
        print(msg)
        return msg


# --- Function to Handle PC Webcam Input ---
def process_webcam_input():
    """Runs the live webcam feed, captures images, and analyzes them."""
    print("\nStarting PC Webcam...")
    # Access the default webcam (usually index 0).
    cap = cv2.VideoCapture(0)
    # Check if the webcam opened successfully.
    if not cap.isOpened():
        print("ERROR: Could not open PC webcam. Check if it's connected and not used by another app.")
        return # Exit this function if webcam failed.

    # Create and name the display window. Allow resizing.
    window_name = 'PC Webcam - SPACE: Capture | Q: Quit'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    status_message = "Aim PC webcam, press SPACE to capture."
    last_result_display = "" # Stores formatted result string
    img_count = 0

    # Loop continuously to show video frames.
    while True:
        # Read one frame from the webcam.
        ret, frame = cap.read()
        # Check if frame reading was successful.
        if not ret:
            status_message = "Error: Can't receive frame from webcam. Exiting."
            print(status_message)
            break # Exit the loop if error.

        # Make a copy to draw on, keeping the original frame clean.
        display_frame = frame.copy()

        # Draw status and results onto the display frame.
        draw_text(display_frame, f"Status: {status_message}", pos=(10, 30))
        if last_result_display:
            result_y_pos = max(60, display_frame.shape[0] - 90)
            draw_text(display_frame, f"Last Result:\n{last_result_display}", pos=(10, result_y_pos))

        # Show the frame with text in the window.
        cv2.imshow(window_name, display_frame)

        # Wait 1ms for a key press. Important for window updates.
        key = cv2.waitKey(1) & 0xFF

        # --- Handle SPACE key press for capture ---
        if key == ord(' '):
            img_count += 1
            filename = f"webcam_capture_{img_count}.jpg" # Temp filename

            # Update status and redraw immediately for user feedback.
            status_message = f"Capturing as {filename}..."
            print(status_message)
            temp_frame = frame.copy()
            draw_text(temp_frame, f"Status: {status_message}", pos=(10, 30))
            if last_result_display: draw_text(temp_frame, f"Last Result:\n{last_result_display}", pos=(10, temp_frame.shape[0] - 90))
            cv2.imshow(window_name, temp_frame)
            cv2.waitKey(1) # Allow screen update

            # Save the current frame to the file.
            cv2.imwrite(filename, frame)

            # Update status and redraw again before analysis.
            status_message = f"Analyzing {filename}..."
            print(status_message)
            temp_frame = frame.copy()
            draw_text(temp_frame, f"Status: {status_message}", pos=(10, 30))
            if last_result_display: draw_text(temp_frame, f"Last Result:\n{last_result_display}", pos=(10, temp_frame.shape[0] - 90))
            cv2.imshow(window_name, temp_frame)
            cv2.waitKey(1) # Allow screen update

            # Call the AI analysis function with the saved image path.
            analysis_result_raw = analyze_image_with_ai(filename)
            # Parse and format the result for display.
            last_result_display = parse_and_format_result(analysis_result_raw)
            # Reset status message.
            status_message = "Ready. Aim PC webcam, press SPACE."

            # Clean up the temporary image file.
            try:
                os.remove(filename)
            except OSError as e:
                print(f"Warning: Could not remove temp file {filename}: {e}")

        # --- Handle 'q' key press to quit ---
        elif key == ord('q'):
            print("Quitting webcam mode.")
            break # Exit the loop.

    # Release the webcam and close OpenCV windows when loop ends.
    cap.release()
    cv2.destroyAllWindows()
    print("Webcam resources released.")


# --- Function to Handle PC File Input ---
def process_file_input():
    """Asks user for image file path on PC and analyzes it."""
    print("\nProcessing Image File from PC...")
    # Loop to allow analyzing multiple files.
    while True:
        try:
            # Get file path from user input.
            image_path = input("Enter the full path to the image file on your PC (or type 'quit'): ")
            # Allow user to quit.
            if image_path.lower() == 'quit':
                break
            # Check if the entered file path actually exists.
            if not os.path.exists(image_path):
                print(f"Error: File not found at '{image_path}'. Please check the path and try again.")
                continue # Ask for input again.

            # Call the AI analysis function.
            analysis_result_raw = analyze_image_with_ai(image_path)
            # Parse and format the result.
            formatted_result = parse_and_format_result(analysis_result_raw)

            # Print results to the console.
            print("\n--- Analysis Result ---")
            print(analysis_result_raw) # Show the raw response from AI
            print("\n--- Parsed Result ---")
            print(formatted_result) # Show the parsed/formatted version
            print("-" * 20)

            # Ask if user wants to analyze another file.
            another = input("Analyze another file? (y/n): ").lower()
            if another != 'y':
                break # Exit the loop if not 'y'.
        except Exception as e:
            # Catch any unexpected errors during file processing.
            print(f"An unexpected error occurred: {e}")
            break # Exit loop on error.


# --- Helper to Parse and Format Result String ---
def parse_and_format_result(analysis_result_raw):
    """Parses the AI's response string to extract key info."""
    # Default values
    object_name = "Unknown"
    classification = "Unknown"
    reason = "N/A"
    try:
        # Check if the input is already an error/block message
        if analysis_result_raw.lower().startswith(("error:", "analysis failed:", "analysis blocked:")):
             return analysis_result_raw # Return the error message directly

        # Split the response into lines.
        lines = analysis_result_raw.split('\n')
        # Loop through lines to find keywords.
        for line in lines:
            if line.lower().startswith("object:"):
                object_name = line.split(":", 1)[1].strip()
            elif line.lower().startswith("classification:"):
                classification = line.split(":", 1)[1].strip()
            elif line.lower().startswith("reason:"):
                reason = line.split(":", 1)[1].strip()
        # Return a nicely formatted string.
        return f"Object: {object_name}\nClassification: {classification}\nReason: {reason}"
    except Exception:
        # If parsing fails for any other reason, return the raw string.
        return f"Could not parse result.\nRaw:\n{analysis_result_raw}"


# --- Main Script Execution ---
if __name__ == "__main__":
    # This block runs when the script is executed directly.
    print("--- Smart Waste Analyzer (PC Version) ---")
    # Loop for the main menu.
    while True:
        print("\nChoose input method:")
        print(" 1: Use PC Webcam")
        print(" 2: Use Image File from PC")
        print(" q: Quit")
        choice = input("Enter choice (1, 2, or q): ").lower()

        # Call the appropriate function based on user choice.
        if choice == '1':
            process_webcam_input()
        elif choice == '2':
            process_file_input()
        elif choice == 'q':
            print("Exiting.")
            break # Exit the main menu loop.
        else:
            # Handle invalid input.
            print("Invalid choice, please try again.")