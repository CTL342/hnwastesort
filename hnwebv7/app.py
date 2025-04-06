# app.py - Simplified: No user/points logic on backend

import datetime
import difflib
import os
import uuid # For unique temporary filenames
import io # For handling image data

from flask import Flask, request, jsonify # Keep flask imports
from flask_cors import CORS
import google.generativeai as genai
import PIL.Image
from werkzeug.utils import secure_filename # For safer filenames

# --- Configuration & AI Model Setup ---
# !!! IMPORTANT: Make sure GOOGLE_API_KEY environment variable is set !!!
try:
    GOOGLE_API_KEY = 'AIzaSyBqzF2aK7q6PKw8HLmichkecIbsxnrCfu8'
    genai.configure(api_key=GOOGLE_API_KEY)
    # Initialize the specific Gemini model capable of understanding images
    # Check Google AI documentation for latest recommended vision models
    vision_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("AI Vision Model loaded successfully.")
except KeyError:
    print("\n\nERROR: GOOGLE_API_KEY environment variable not set!")
    print("Please set it before running the server.\n")
    vision_model = None # Indicate model failed to load
except Exception as e:
    print(f"\n\nERROR: Could not initialize AI model: {e}")
    vision_model = None

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing for your frontend
UPLOAD_FOLDER = 'uploads' # Create this folder in your project directory
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Data Store (Rule Dictionaries - EXAMPLE DATA - VERIFY/COMPLETE!) ---
# !!! REPLACE BELOW WITH ACCURATE, VERIFIED DATA FROM OFFICIAL SOURCES !!!

# --- EXAMPLE DC RULES (Illustrative & Incomplete - VERIFY!) ---
DC_DPW_RULES = {
    # Recyclables
    "plastic bottle": {"category": "Recyclable", "notes": "Empty, rinse, cap ON. Check numbers accepted by DC DPW (often #1, #2, #5)."},
    "plastic jug": {"category": "Recyclable", "notes": "Empty, rinse, cap ON. Typically #1, #2."},
    "plastic tub": {"category": "Recyclable", "notes": "Empty, rinse. Typically #5 accepted (yogurt, butter tubs)."},
    "plastic container": {"category": "Recyclable", "notes": "Empty, rinse. Rigid containers #1, #2, #5 usually ok. Check DPW list."},
    "glass jar": {"category": "Recyclable", "notes": "Empty, rinse. Lids separate (recycle metal lids)."},
    "glass bottle": {"category": "Recyclable", "notes": "Empty, rinse. Lids separate."},
    "aluminum can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "steel can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "tin can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "carton": {"category": "Recyclable", "notes": "Milk, juice, soup cartons. Empty, rinse, caps on/straws in."},
    "paper": {"category": "Recyclable", "notes": "Mail, office paper, magazines, newspapers, paperboard boxes (cereal, tissue boxes). Flatten boxes. No shredded paper in curbside."},
    "newspaper": {"category": "Recyclable", "notes": "Clean and dry."},
    "magazine": {"category": "Recyclable", "notes": "Clean and dry."},
    "cardboard box": {"category": "Recyclable", "notes": "Flatten. Keep clean and dry."},
    "cereal box": {"category": "Recyclable", "notes": "Flatten. Remove plastic liner."},
    "metal lid": {"category": "Recyclable", "notes": "From jars/bottles."},
    "aluminum foil": {"category": "Recyclable", "notes": "Clean and balled up only."},
    "aerosol can": {"category": "Recyclable", "notes": "Must be completely empty. Remove plastic cap."},

    # Food Scraps
    "food scraps": {"category": "Compost/Trash", "notes": "Check DC's food waste drop-off program details & locations. Not accepted in regular recycling/trash unless specific program used."},
    "apple core": {"category": "Compost/Trash", "notes": "See 'food scraps'"},
    "banana peel": {"category": "Compost/Trash", "notes": "See 'food scraps'"},
    "coffee grounds": {"category": "Compost/Trash", "notes": "See 'food scraps'"},
    "egg shells": {"category": "Compost/Trash", "notes": "See 'food scraps'"},
    "meat": {"category": "Compost/Trash", "notes": "Check specific program rules. Sometimes excluded."},
    "dairy": {"category": "Compost/Trash", "notes": "Check specific program rules. Sometimes excluded."},

    # Trash
    "styrofoam": {"category": "Trash", "notes": "Not recyclable in DC."},
    "foam cup": {"category": "Trash", "notes": "Not recyclable."},
    "plastic bag": {"category": "Trash", "notes": "Do NOT put in curbside recycling. Check store drop-off options."},
    "plastic film": {"category": "Trash", "notes": "Plastic wrap, bubble wrap, etc. Not curbside recyclable."},
    "chip bag": {"category": "Trash", "notes": "Multi-layer packaging."},
    "plastic straw": {"category": "Trash", "notes": "Not recyclable."},
    "plastic utensil": {"category": "Trash", "notes": "Not recyclable."},
    "coffee cup": {"category": "Trash", "notes": "Most disposable cups have plastic lining."},
    "pizza box": {"category": "Trash", "notes": "Generally trash due to grease. Check specific DPW guidance. Clean parts may be recyclable."},
    "broken glass": {"category": "Trash", "notes": "Wrap carefully."},
    "broken ceramic": {"category": "Trash", "notes": "Wrap carefully."},
    "textiles": {"category": "Donate/Trash", "notes": "See 'clothing'."},
    "garden hose": {"category": "Trash", "notes": "Tanglers - do not recycle."},
    "wire hanger": {"category": "Trash", "notes": "Often tangles machinery. Check alternatives or trash."},

    # Other Categories
    "battery": {"category": "Hazardous Waste", "notes": "Check DC DPW hazardous waste (Ft. Totten)."},
    "electronics": {"category": "E-waste", "notes": "Check DC DPW e-waste collection info (Ft. Totten)."},
    "light bulb": {"category": "Trash/Hazardous", "notes": "Incandescent/LED=Trash. CFLs=Hazardous Waste (check DPW)."},
    "clothing": {"category": "Donate/Textile Recycle", "notes": "Donate usable items or find specific textile recycling locations."},
    "paint": {"category": "Hazardous Waste", "notes": "Latex paint may have specific disposal (dry out?). Oil paint is HHW. Check DPW."},
    # ... ADD MANY MORE DC ITEMS ...
}

# --- EXAMPLE Arlington County, VA Rules (Illustrative & Incomplete - VERIFY!) ---
ARLINGTON_COUNTY_RULES = {
    # Recyclables (Arlington often takes #1-7 plastics, but VERIFY)
    "plastic bottle": {"category": "Recyclable", "notes": "Empty, rinse, cap on. #1, #2, #5 typically accepted, check Arlington site for full range."},
    "plastic jug": {"category": "Recyclable", "notes": "Empty, rinse, cap on. #1, #2."},
    "plastic tub": {"category": "Recyclable", "notes": "Empty, rinse. #5 (yogurt, butter, cottage cheese)."},
    "plastic container": {"category": "Recyclable", "notes": "Empty/rinse. Check website - often accepts rigid #1-#7 (NO foam)."},
    "clamshell container": {"category": "Recyclable", "notes": "Often #1 PET. Empty/clean. Check Arlington specifics."},
    "glass jar": {"category": "Recyclable", "notes": "Empty, rinse. Lids separate. All colors usually accepted."},
    "glass bottle": {"category": "Recyclable", "notes": "Empty, rinse. Lids separate."},
    "aluminum can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "steel can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "tin can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "carton": {"category": "Recyclable", "notes": "Milk, juice, soup. Empty, rinse, caps on/straws in."},
    "paper": {"category": "Recyclable", "notes": "Mail, office paper, magazines, newspapers, paperboard boxes. Flatten. Shredded paper in paper bag."},
    "newspaper": {"category": "Recyclable", "notes": "Clean and dry."},
    "magazine": {"category": "Recyclable", "notes": "Clean and dry."},
    "cardboard box": {"category": "Recyclable", "notes": "Flatten. Keep clean and dry."},
    "cereal box": {"category": "Recyclable", "notes": "Flatten. Remove plastic liner."},
    "metal lid": {"category": "Recyclable", "notes": "From jars/bottles."},
    "aerosol can": {"category": "Recyclable", "notes": "Empty. Remove plastic cap (trash)."},
    "aluminum foil": {"category": "Recyclable", "notes": "Clean and balled."},

    # Food Scraps (Arlington has specific program)
    "food scraps": {"category": "Compost (Food Scraps Program)", "notes": "Check Arlington's curbside food scrap collection rules (accepted items include meat, dairy, bones). Use provided cart/bags."},
    "apple core": {"category": "Compost (Food Scraps Program)", "notes": "See 'food scraps'."},
    "banana peel": {"category": "Compost (Food Scraps Program)", "notes": "See 'food scraps'."},
    "coffee grounds": {"category": "Compost (Food Scraps Program)", "notes": "See 'food scraps'."},
    "egg shells": {"category": "Compost (Food Scraps Program)", "notes": "See 'food scraps'."},
    "meat": {"category": "Compost (Food Scraps Program)", "notes": "Accepted in Arlington's program."},
    "dairy": {"category": "Compost (Food Scraps Program)", "notes": "Accepted in Arlington's program."},
    "pizza box": {"category": "Compost (Food Scraps Program)/Trash", "notes": "If participating in food scraps program, YES. Otherwise, greasy parts trash, clean parts recyclable."},

    # Trash
    "styrofoam": {"category": "Trash", "notes": "Not accepted in curbside. Check special drop-offs (E-CARE events)."},
    "foam cup": {"category": "Trash", "notes": "Not recyclable."},
    "plastic bag": {"category": "Trash", "notes": "Do NOT put in curbside recycling. Use store drop-offs."},
    "plastic film": {"category": "Trash", "notes": "Not curbside recyclable. Use store drop-offs."},
    "chip bag": {"category": "Trash", "notes": "Multi-layer packaging."},
    "plastic straw": {"category": "Trash", "notes": "Not recyclable."},
    "plastic utensil": {"category": "Trash", "notes": "Not recyclable."},
    "coffee cup": {"category": "Trash", "notes": "Most are trash."},
    "broken glass": {"category": "Trash", "notes": "Wrap carefully."},
    "textiles": {"category": "Donate/Trash", "notes": "See 'clothing'."},

    # Other Categories
    "battery": {"category": "Hazardous Waste/Drop-off", "notes": "Check Arlington hazardous waste/E-CARE info."},
    "electronics": {"category": "E-waste/Drop-off", "notes": "Check Arlington E-CARE collection info."},
    "light bulb": {"category": "Trash/Hazardous", "notes": "Incandescent/LED=Trash. CFLs=Hazardous (E-CARE)."},
    "clothing": {"category": "Donate/Textile Recycle", "notes": "Donate usable items or specific textile bins/drop-offs (e.g., E-CARE). Not curbside."},
    "paint": {"category": "Hazardous Waste/Drop-off", "notes": "Check E-CARE event info."},
     # ... ADD MANY MORE ARLINGTON ITEMS ...
}

# --- EXAMPLE Montgomery County, MD Rules (Illustrative & Incomplete - VERIFY!) ---
MONTGOMERY_COUNTY_RULES = {
    # Recyclables
    "plastic bottle": {"category": "Recyclable", "notes": "Empty, rinse, cap on. Bottles/Jars/Jugs/Tubs/Containers - Check Mont. Co. specific number/shape guidance."},
    "plastic jug": {"category": "Recyclable", "notes": "Empty, rinse, cap on."},
    "plastic tub": {"category": "Recyclable", "notes": "Empty, rinse."},
    "plastic container": {"category": "Recyclable", "notes": "Empty, rinse. Typically wide-mouth containers, bottles, jugs. Check website."},
    "glass jar": {"category": "Recyclable", "notes": "Empty, rinse. Lids separate."},
    "glass bottle": {"category": "Recyclable", "notes": "Empty, rinse. Lids separate."},
    "aluminum foil": {"category": "Recyclable", "notes": "Clean and balled up (usually > 2 inches)."},
    "aluminum can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "steel can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "tin can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "carton": {"category": "Recyclable", "notes": "Milk, juice, soup. Empty, rinse, caps on/straws in."},
    "paper": {"category": "Recyclable", "notes": "Mixed paper including mail, magazines, newspaper, boxes. Flatten. No shredded paper curbside."},
    "newspaper": {"category": "Recyclable", "notes": "Clean and dry."},
    "magazine": {"category": "Recyclable", "notes": "Clean and dry."},
    "cardboard box": {"category": "Recyclable", "notes": "Flatten. Keep clean and dry."},
    "cereal box": {"category": "Recyclable", "notes": "Flatten. Remove liner."},
    "metal lid": {"category": "Recyclable", "notes": "From jars/bottles."},
    "aerosol can": {"category": "Recyclable", "notes": "Empty. Remove cap."},

    # Food Scraps
    "food scraps": {"category": "Compost/Trash", "notes": "Check Montgomery County's specific composting program rules and availability."},
    "apple core": {"category": "Compost/Trash", "notes": "See 'food scraps'."},
    "banana peel": {"category": "Compost/Trash", "notes": "See 'food scraps'."},
    "coffee grounds": {"category": "Compost/Trash", "notes": "See 'food scraps'."},
    "egg shells": {"category": "Compost/Trash", "notes": "See 'food scraps'."},

    # Trash
    "styrofoam": {"category": "Trash", "notes": "Specifically prohibited in recycling. Trash or check Shady Grove drop-off."},
    "foam cup": {"category": "Trash", "notes": "Not recyclable."},
    "plastic bag": {"category": "Trash", "notes": "NOT in recycling bin. Check store drop-offs."},
    "plastic film": {"category": "Trash", "notes": "NOT in recycling bin. Check store drop-offs."},
    "chip bag": {"category": "Trash", "notes": "Not recyclable."},
    "plastic straw": {"category": "Trash", "notes": "Trash."},
    "plastic utensil": {"category": "Trash", "notes": "Trash."},
    "pizza box": {"category": "Trash", "notes": "Generally trash if soiled. Clean parts recyclable."},
    "broken glass": {"category": "Trash", "notes": "Wrap carefully."},
    "garden hose": {"category": "Trash", "notes": "Tanglers - do not recycle."},
    "textiles": {"category": "Donate/Textile Recycle/Trash", "notes": "See 'clothing'."},

    # Other Categories
    "battery": {"category": "Hazardous Waste/Drop-off", "notes": "Check Montgomery Co. hazardous waste info (Shady Grove)."},
    "electronics": {"category": "E-waste/Drop-off", "notes": "Check Montgomery Co. electronics recycling info (Shady Grove)."},
    "light bulb": {"category": "Trash/Hazardous", "notes": "Incandescent/LED=Trash. CFLs=Hazardous (check HHW options)."},
    "clothing": {"category": "Donate/Textile Recycle/Trash", "notes": "Donate usable, check textile recycling options (Shady Grove?), otherwise trash."},
    "paint": {"category": "Hazardous Waste/Drop-off", "notes": "Check HHW options at Shady Grove."},
     # ... ADD MANY MORE MONTGOMERY COUNTY ITEMS ...
}

# --- EXAMPLE Alexandria City, VA Rules (Illustrative & Incomplete - VERIFY!) ---
ALEXANDRIA_CITY_RULES = {
    # Recyclables (Similar to Arlington/Fairfax, but check specifics)
    "plastic bottle": {"category": "Recyclable", "notes": "Empty, rinse, cap ON. Check City website for accepted numbers."},
    "plastic jug": {"category": "Recyclable", "notes": "Empty, rinse, cap ON."},
    "plastic tub": {"category": "Recyclable", "notes": "Empty, rinse."},
    "glass jar": {"category": "Recyclable", "notes": "Empty, rinse. Lids separate. Check City guide."},
    "glass bottle": {"category": "Recyclable", "notes": "Empty, rinse. Lids separate."},
    "aluminum can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "steel can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "carton": {"category": "Recyclable", "notes": "Empty, rinse."},
    "paper": {"category": "Recyclable", "notes": "Mixed paper, newspaper, magazines, cardboard. Flatten boxes."},
    "cardboard box": {"category": "Recyclable", "notes": "Flatten."},

    # Food Scraps (Check City Program)
    "food scraps": {"category": "Compost/Trash", "notes": "Check City of Alexandria's food waste composting program (curbside or drop-off)."},
    "apple core": {"category": "Compost/Trash", "notes": "See 'food scraps'."},
    "banana peel": {"category": "Compost/Trash", "notes": "See 'food scraps'."},

    # Trash
    "styrofoam": {"category": "Trash", "notes": "Not accepted in City recycling."},
    "plastic bag": {"category": "Trash", "notes": "Not in curbside recycling. Store drop-off."},
    "plastic film": {"category": "Trash", "notes": "Not in curbside recycling."},
    "pizza box": {"category": "Trash", "notes": "Trash if greasy. Clean sections recyclable."},
    "broken glass": {"category": "Trash", "notes": "Wrap carefully."},

    # Other
    "battery": {"category": "Hazardous Waste/Drop-off", "notes": "Check City's HHW and electronics disposal events/locations."},
    "electronics": {"category": "E-waste/Drop-off", "notes": "Check City's HHW and electronics disposal events/locations."},
    "clothing": {"category": "Donate/Trash", "notes": "Donate usable items. Check textile recycling options."},
    # ... ADD MANY MORE ALEXANDRIA ITEMS ...
}

# --- EXAMPLE Loudoun County, VA Rules (Illustrative & Incomplete - VERIFY!) ---
LOUDOUN_COUNTY_RULES = {
     # Recyclables
    "plastic bottle": {"category": "Recyclable", "notes": "Empty, rinse, caps ON. Check county website for specific #s accepted."},
    "plastic jug": {"category": "Recyclable", "notes": "Empty, rinse, caps ON."},
    "plastic tub": {"category": "Recyclable", "notes": "Empty, rinse. Tubs/lids usually okay."},
    "glass jar": {"category": "Recyclable", "notes": "Empty, rinse. Lids off (recycle metal lids)."},
    "glass bottle": {"category": "Recyclable", "notes": "Empty, rinse. Lids off."},
    "aluminum can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "steel can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "carton": {"category": "Recyclable", "notes": "Empty, rinse."},
    "paper": {"category": "Recyclable", "notes": "Mixed paper, newspaper, magazines, cardboard. Flatten boxes."},
    "cardboard box": {"category": "Recyclable", "notes": "Flatten."},

    # Food Scraps (Less common curbside, check drop-off)
    "food scraps": {"category": "Trash/Drop-off", "notes": "Check Loudoun County for food scrap drop-off locations or private composting services."},
    "apple core": {"category": "Trash/Drop-off", "notes": "See 'food scraps'."},

    # Trash
    "styrofoam": {"category": "Trash", "notes": "Not accepted in Loudoun recycling."},
    "plastic bag": {"category": "Trash", "notes": "Not in curbside. Store drop-off."},
    "plastic film": {"category": "Trash", "notes": "Not in curbside."},
    "pizza box": {"category": "Trash", "notes": "Trash if greasy. Clean parts okay."},
    "broken glass": {"category": "Trash", "notes": "Wrap."},

    # Other
    "battery": {"category": "Hazardous Waste/Drop-off", "notes": "Check Loudoun County HHW collection events."},
    "electronics": {"category": "E-waste/Drop-off", "notes": "Check Loudoun County electronics recycling events/locations."},
    "clothing": {"category": "Donate/Trash", "notes": "Donate usable. Check other recycling options."},
    # ... ADD MANY MORE LOUDOUN ITEMS ...
}

# --- EXAMPLE Prince William County, VA Rules (Illustrative & Incomplete - VERIFY!) ---
PRINCE_WILLIAM_COUNTY_RULES = {
    # Recyclables
    "plastic bottle": {"category": "Recyclable", "notes": "Empty, rinse, caps ON. Check PWC website for accepted #s (often #1,#2)."},
    "plastic jug": {"category": "Recyclable", "notes": "Empty, rinse, caps ON."},
    "plastic tub": {"category": "Recyclable", "notes": "Empty, rinse. Usually #5 ok, verify."},
    "glass jar": {"category": "Recyclable", "notes": "Empty, rinse. Lids off (recycle metal lids)."},
    "glass bottle": {"category": "Recyclable", "notes": "Empty, rinse. Lids off."},
    "aluminum can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "steel can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "carton": {"category": "Recyclable", "notes": "Empty, rinse."},
    "paper": {"category": "Recyclable", "notes": "Mixed paper, newspaper, magazines, cardboard. Flatten boxes."},
    "cardboard box": {"category": "Recyclable", "notes": "Flatten."},

    # Food Scraps (Check PWC Landfill Compost)
    "food scraps": {"category": "Trash/Drop-off", "notes": "Check Prince William County Landfill composting options/rules."},
    "apple core": {"category": "Trash/Drop-off", "notes": "See 'food scraps'."},

    # Trash
    "styrofoam": {"category": "Trash", "notes": "Not accepted in PWC recycling."},
    "plastic bag": {"category": "Trash", "notes": "Not in curbside. Store drop-off."},
    "plastic film": {"category": "Trash", "notes": "Not in curbside."},
    "pizza box": {"category": "Trash", "notes": "Trash if greasy. Clean parts okay."},
    "broken glass": {"category": "Trash", "notes": "Wrap."},

    # Other
    "battery": {"category": "Hazardous Waste/Drop-off", "notes": "Check PWC Landfill HHW options."},
    "electronics": {"category": "E-waste/Drop-off", "notes": "Check PWC Landfill electronics recycling."},
    "clothing": {"category": "Donate/Trash", "notes": "Donate usable."},
    # ... ADD MANY MORE PRINCE WILLIAM ITEMS ...
}

# --- EXAMPLE Prince George's County, MD Rules (Illustrative & Incomplete - VERIFY!) ---
PRINCE_GEORGES_COUNTY_RULES = {
    # Recyclables
    "plastic bottle": {"category": "Recyclable", "notes": "Empty, rinse, cap ON. Check PG County website for accepted numbers/types."},
    "plastic jug": {"category": "Recyclable", "notes": "Empty, rinse, cap ON."},
    "plastic tub": {"category": "Recyclable", "notes": "Empty, rinse. Check acceptable types."},
    "glass jar": {"category": "Recyclable", "notes": "Empty, rinse. Lids separate."},
    "glass bottle": {"category": "Recyclable", "notes": "Empty, rinse. Lids separate."},
    "aluminum can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "steel can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "carton": {"category": "Recyclable", "notes": "Empty, rinse."},
    "paper": {"category": "Recyclable", "notes": "Mixed paper, newspaper, magazines, cardboard. Flatten boxes."},
    "cardboard box": {"category": "Recyclable", "notes": "Flatten."},
    "aerosol can": {"category": "Recyclable", "notes": "Empty. Cap off."},

    # Food Scraps (Check PGC Program)
    "food scraps": {"category": "Compost/Trash", "notes": "Check Prince George's County composting program rules/availability."},
    "apple core": {"category": "Compost/Trash", "notes": "See 'food scraps'."},

    # Trash
    "styrofoam": {"category": "Trash", "notes": "Not accepted in PG County recycling."},
    "plastic bag": {"category": "Trash", "notes": "Not in curbside. Store drop-off."},
    "plastic film": {"category": "Trash", "notes": "Not in curbside."},
    "pizza box": {"category": "Trash", "notes": "Trash if greasy."},
    "broken glass": {"category": "Trash", "notes": "Wrap."},

    # Other
    "battery": {"category": "Hazardous Waste/Drop-off", "notes": "Check PG County HHW drop-off info."},
    "electronics": {"category": "E-waste/Drop-off", "notes": "Check PG County electronics recycling locations/events."},
    "clothing": {"category": "Donate/Trash", "notes": "Donate usable."},
    # ... ADD MANY MORE PRINCE GEORGE'S ITEMS ...
}

# --- Fairfax County Rules (Keep your full list here) ---
FAIRFAX_COUNTY_RULES = {
    # --- Recyclables ---
    "plastic bottle": {"category": "Recyclable", "notes": "Empty and rinse. Replace cap. Typically #1, #2 accepted."},
    "water bottle": {"category": "Recyclable", "notes": "Empty. Replace cap. Typically #1, #2 accepted."},
    "soda bottle": {"category": "Recyclable", "notes": "Empty and rinse. Replace cap. Typically #1, #2 accepted."},
    "milk jug": {"category": "Recyclable", "notes": "Empty and rinse. Replace cap. Typically #2 accepted."},
    "detergent jug": {"category": "Recyclable", "notes": "Empty and rinse. Replace cap. Typically #2 accepted."},
    "shampoo bottle": {"category": "Recyclable", "notes": "Empty and rinse. Replace cap. Typically #2 accepted."},
    "yogurt tub": {"category": "Recyclable", "notes": "Empty and rinse. Typically #5 accepted."},
    "butter tub": {"category": "Recyclable", "notes": "Empty and rinse. Typically #5 accepted."},
    "cottage cheese tub": {"category": "Recyclable", "notes": "Empty and rinse. Typically #5 accepted."},
    "cardboard box": {"category": "Recyclable", "notes": "Flatten. Keep clean and dry. Remove excessive tape."},
    "cereal box": {"category": "Recyclable", "notes": "Flatten. Remove plastic liner (trash)."},
    "paper": {"category": "Recyclable", "notes": "Clean paper like mail, office paper, magazines, newspapers."},
    "newspaper": {"category": "Recyclable", "notes": "Clean and dry."},
    "magazine": {"category": "Recyclable", "notes": "Clean and dry."},
    "junk mail": {"category": "Recyclable", "notes": "Remove plastic windows if possible."},
    "aluminum can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "soda can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "beer can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "steel can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "tin can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "food can": {"category": "Recyclable", "notes": "Empty and rinse."},
    "glass bottle": {"category": "Recyclable", "notes": "Empty and rinse. Remove metal lids (recycle separately)."},
    "glass jar": {"category": "Recyclable", "notes": "Empty and rinse. Remove metal lids (recycle separately)."},
    "wine bottle": {"category": "Recyclable", "notes": "Empty and rinse. Cork is trash."},
    "metal lid": {"category": "Recyclable", "notes": "From jars/bottles. Recycle separately."},
    "carton": {"category": "Recyclable", "notes": "Milk, juice, soup cartons. Empty, rinse, replace cap/push straw in."},
    "aerosol can": {"category": "Recyclable", "notes": "Empty. Remove cap."},
    "aluminum foil": {"category": "Recyclable", "notes": "Clean and balled."},

    # --- Compostable ---
    "apple core": {"category": "Compost", "notes": "Food scraps. Check Fairfax County drop-off programs or backyard compost."},
    "banana peel": {"category": "Compost", "notes": "Food scraps. Check Fairfax County drop-off programs or backyard compost."},
    "coffee grounds": {"category": "Compost", "notes": "Food scraps. Check Fairfax County drop-off programs or backyard compost."},
    "tea bag": {"category": "Compost", "notes": "Remove staple/tag if possible. Check Fairfax County drop-off programs or backyard compost."},
    "egg shells": {"category": "Compost", "notes": "Food scraps. Check Fairfax County drop-off programs or backyard compost."},
    "fruit": {"category": "Compost", "notes": "Food scraps. Check Fairfax County drop-off programs or backyard compost."},
    "vegetable": {"category": "Compost", "notes": "Food scraps. Check Fairfax County drop-off programs or backyard compost."},
    "leaves": {"category": "Yard Waste", "notes": "Collected separately by Fairfax County during season. Check schedule."},
    "grass clippings": {"category": "Yard Waste", "notes": "Collected separately by Fairfax County during season. Check schedule."},
    "food soiled paper": {"category": "Compost", "notes": "Napkins/paper towels ONLY if your specific composting program accepts them. Otherwise, trash. Check Fairfax County drop-off rules."},
    "napkin": {"category": "Compost", "notes": "Soiled paper napkin. ONLY if your specific composting program accepts them. Otherwise, trash."},
    "paper towel": {"category": "Compost", "notes": "Soiled paper towel. ONLY if your specific composting program accepts them. Otherwise, trash."},

    # --- Landfill (Trash) ---
    "styrofoam": {"category": "Trash", "notes": "Not accepted in Fairfax County recycling."},
    "foam cup": {"category": "Trash", "notes": "Not accepted in Fairfax County recycling."},
    "foam takeout container": {"category": "Trash", "notes": "Not accepted in Fairfax County recycling."},
    "plastic bag": {"category": "Trash", "notes": "Do NOT put in curbside recycling. Check store drop-off programs."},
    "plastic film": {"category": "Trash", "notes": "Like grocery bags, bread bags, bubble wrap. Do NOT put in curbside recycling. Check store drop-off."},
    "chip bag": {"category": "Trash", "notes": "Multi-layer flexible plastic packaging."},
    "candy wrapper": {"category": "Trash", "notes": "Typically multi-layer flexible plastic."},
    "plastic straw": {"category": "Trash", "notes": "Generally not recyclable."},
    "plastic utensil": {"category": "Trash", "notes": "Generally not recyclable."},
    "plastic wrap": {"category": "Trash", "notes": "Cling film. Not recyclable."},
    "broken glass": {"category": "Trash", "notes": "Wrap carefully before placing in trash."},
    "broken ceramic": {"category": "Trash", "notes": "Wrap carefully before placing in trash."},
    "diaper": {"category": "Trash", "notes": ""},
    "pipette tip box": {"category": "Trash", "notes": "Often #5 PP, but lab waste may have specific disposal procedures. Generally trash in household context."},
    "coffee cup": {"category": "Trash", "notes": "Most disposable coffee cups have a plastic lining and are not recyclable or compostable. Lid might be recyclable if # matches."},
    "greasy pizza box": {"category": "Trash", "notes": "Food soiled cardboard. Remove clean parts for recycling, trash the greasy parts. Some composting programs might accept."},
    "light bulb": {"category": "Trash", "notes": "Incandescent/LED bulbs are trash. CFLs contain mercury - check Fairfax County hazardous waste disposal."},
    "battery": {"category": "Hazardous Waste", "notes": "Do NOT put in trash or recycling. Check Fairfax County hazardous waste disposal options."},
    "electronics": {"category": "E-waste", "notes": "Do NOT put in trash or recycling. Check Fairfax County e-waste collection events/locations."},
    "clothing": {"category": "Donate/Textile Recycle", "notes": "Do not put in curbside recycling. Donate if usable, or find textile recycling drop-offs."},
    "shoes": {"category": "Donate/Trash", "notes": "Donate if usable, otherwise trash."},
    "rubber band": {"category": "Trash", "notes": ""},
    "pen": {"category": "Trash", "notes": ""},
    "pizza box": {"category": "Trash", "notes": "Often greasy. Check 'greasy pizza box'. If completely clean/dry, recycle."},
    "garden hose": {"category": "Trash", "notes": "Do not recycle."},
    "textiles": {"category": "Donate/Textile Recycle", "notes": "See 'clothing'."},
     # ... (Ensure your Fairfax list is complete) ...
}

# Shared Aliases (Assumption - Review if necessary for different locations)
ALIASES = {
    "apple": "apple core", "banana": "banana peel", "peel": "banana peel", "core": "apple core",
    "grounds": "coffee grounds", "coffee": "coffee grounds", "tea": "tea bag", "eggshell": "egg shells",
    "eggshells": "egg shells", "bottle": "plastic bottle", "can": "aluminum can", "jar": "glass jar",
    "box": "cardboard box", "jug": "milk jug", "tub": "yogurt tub", "mail": "junk mail",
    "bag": "plastic bag", "wrapper": "candy wrapper", "straw": "plastic straw", "utensil": "plastic utensil",
    "wrap": "plastic wrap", "foam": "styrofoam", "cup": "coffee cup", "bulb": "light bulb",
    "batteries": "battery", "clothes": "clothing", "orange peel": "fruit", "potato peel": "vegetable",
    "foil": "aluminum foil",
    "card board": "cardboard box",
    "clamshell": "plastic container", # Example alias
    "takeout container": "foam takeout container", # Example alias - check if foam or plastic needed
}

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# --- Text Sorting Logic Function ---
def get_sorting_info(item_description, location_context, rules, aliases, rules_source):
    print(f"Logic using rules for: {location_context} (Source: {rules_source})")
    query = item_description.lower().strip()
    if not query:
        return {"query": query, "location": location_context, "status": "not_found", "category": "Unknown", "notes": "Please enter an item description.", "rules_source": rules_source}
    current_valid_terms = list(rules.keys()) + list(aliases.keys())
    current_valid_terms = sorted(list(set(current_valid_terms)), key=len, reverse=True)
    found_term = None
    for term in current_valid_terms:
        if term in query:
            found_term = term
            break
    if found_term:
        canonical_key = found_term
        alias_used = None
        if found_term in aliases:
            alias_used = found_term
            if aliases[found_term] in rules: canonical_key = aliases[found_term]
            else: return {"query": query, "location": location_context, "status": "not_found", "category": "Unknown", "notes": f"Item '{found_term}' (alias for '{aliases[found_term]}') not specifically listed in rules for {rules_source}.", "rules_source": rules_source}
        if canonical_key in rules:
            result = rules[canonical_key].copy()
            result.update({"query": query, "location": location_context, "keyword_identified": found_term, "alias_resolution": canonical_key if alias_used and alias_used != canonical_key else None, "status": "found", "rules_source": rules_source})
            return result
        else: return {"query": query, "location": location_context, "status": "not_found", "category": "Unknown", "notes": f"Could not find specific rule for '{canonical_key}' in {rules_source}.", "rules_source": rules_source}
    suggestions = difflib.get_close_matches(query, current_valid_terms, n=3, cutoff=0.6)
    if suggestions:
         if len(suggestions) == 1 and difflib.SequenceMatcher(None, query, suggestions[0]).ratio() > 0.7: return {"query": query, "location": location_context, "status": "suggestion_found", "suggestion": suggestions[0], "rules_source": rules_source}
         else: return {"query": query, "location": location_context, "status": "multiple_suggestions_found", "suggestions": suggestions, "rules_source": rules_source}
    else: return {"query": query, "location": location_context, "status": "not_found", "category": "Unknown", "notes": f"Item not found or no close match in rules for {rules_source}.", "rules_source": rules_source}


# --- Image Analysis & Parsing Functions ---
def analyze_image_with_ai(image_path):
    print(f"Analyzing image file: {image_path}...")
    if not vision_model: return "Error: AI Vision Model not initialized."
    try:
        img_pil = PIL.Image.open(image_path)
        if img_pil.mode != 'RGB': img_pil = img_pil.convert('RGB')
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
        response = vision_model.generate_content([prompt, img_pil])
        print("AI analysis complete.")
        if response.parts: return response.text.strip()
        else:
            try: return f"Analysis Blocked by API. Reason: {response.prompt_feedback.block_reason}"
            except Exception: return "Analysis Failed: Received empty or blocked response from AI."
    except FileNotFoundError: return f"Error: Image file not found at '{image_path}'"
    except Exception as e: print(f"Error during image analysis call: {e}"); return f"Error during AI analysis: {e}"

def parse_result_to_dict(analysis_result_raw):
    result = {"object": "Unknown", "classification": "Unknown", "reason": "N/A", "error": None }
    if not analysis_result_raw or not isinstance(analysis_result_raw, str): result["error"] = "Invalid analysis result."; return result
    if analysis_result_raw.lower().startswith(("error:", "analysis failed:", "analysis blocked:")): result["error"] = analysis_result_raw; result["classification"] = "Error"; return result
    try:
        lines = analysis_result_raw.strip().split('\n')
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1); key_lower = key.lower().strip(); value_strip = value.strip()
                if key_lower == "object": result["object"] = value_strip
                elif key_lower == "classification": result["classification"] = value_strip
                elif key_lower == "reason": result["reason"] = value_strip
    except Exception as e: print(f"Error parsing AI response: {e}\nRaw:\n{analysis_result_raw}"); result["error"] = "Failed to parse AI response."; result["reason"] = analysis_result_raw; result["classification"] = "Error"
    return result


# --- API Endpoint for Text Search ---
@app.route('/sort', methods=['GET'])
def sort_api():
    user_query = request.args.get('query', '')
    location_value = request.args.get('location', '')
    if not user_query: return jsonify({"error": "Query parameter is missing", "status": "error"}), 400
    if not location_value: return jsonify({"error": "Location parameter is missing", "status": "error"}), 400

    # Select Rules Based on Location VALUE from Dropdown
    rules_to_use = FAIRFAX_COUNTY_RULES # Default
    aliases_to_use = ALIASES
    rules_source = "Fairfax County, VA (Default)"
    display_location = "Fairfax County, VA (Default)"

    if location_value == "dc": rules_to_use, rules_source, display_location = DC_DPW_RULES, "District of Columbia", "Washington, DC"
    elif location_value == "arlington_va": rules_to_use, rules_source, display_location = ARLINGTON_COUNTY_RULES, "Arlington County, VA", "Arlington County, VA"
    elif location_value == "alexandria_va": rules_to_use, rules_source, display_location = ALEXANDRIA_CITY_RULES, "Alexandria City, VA", "Alexandria City, VA"
    elif location_value == "loudoun_va": rules_to_use, rules_source, display_location = LOUDOUN_COUNTY_RULES, "Loudoun County, VA", "Loudoun County, VA"
    elif location_value == "prince_william_va": rules_to_use, rules_source, display_location = PRINCE_WILLIAM_COUNTY_RULES, "Prince William County, VA", "Prince William County, VA"
    elif location_value == "montgomery_md": rules_to_use, rules_source, display_location = MONTGOMERY_COUNTY_RULES, "Montgomery County, MD", "Montgomery County, MD"
    elif location_value == "prince_georges_md": rules_to_use, rules_source, display_location = PRINCE_GEORGES_COUNTY_RULES, "Prince George's County, MD", "Prince George's County, MD"
    elif location_value == "fairfax_va": rules_to_use, rules_source, display_location = FAIRFAX_COUNTY_RULES, "Fairfax County, VA", "Fairfax County, VA"
    # else uses default Fairfax rules

    print(f"Request Location Value: '{location_value}', Using Rules For: {rules_source}")

    result_data = get_sorting_info(user_query, display_location, rules_to_use, aliases_to_use, rules_source)
    result_data['location_value'] = location_value # Keep for JS context

    # NO point logic in this simplified backend version
    return jsonify(result_data)

# --- API Endpoint for Image Analysis ---
@app.route('/analyze_image', methods=['POST'])
def analyze_image_api():
    if not vision_model: return jsonify({"error": "AI Vision Model not available"}), 503
    if 'image_file' not in request.files: return jsonify({"error": "No image file part"}), 400
    file = request.files['image_file']
    if file.filename == '': return jsonify({"error": "No image file selected"}), 400

    if file:
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        try:
            file.save(temp_file_path)
            raw_analysis_result = analyze_image_with_ai(temp_file_path)
            parsed_result = parse_result_to_dict(raw_analysis_result)
            # NO point logic in this simplified backend version
            return jsonify(parsed_result)
        except Exception as e:
             print(f"Error processing uploaded image: {e}")
             return jsonify({"error": f"Failed to process image. Details: {e}"}), 500
        finally:
             if os.path.exists(temp_file_path):
                 try: os.remove(temp_file_path)
                 except OSError as e: print(f"Error deleting {temp_file_path}: {e}")
    else:
         return jsonify({"error": "Invalid file or upload error"}), 400

# --- Run the Server ---
if __name__ == '__main__':
    print("Starting Smart Sorter API server (Text & Image) on http://127.0.0.1:5000")
    print("Ensure GOOGLE_API_KEY is set.")
    print("Press CTRL+C to stop the server.")
    app.run(host='127.0.0.1', port=5000, debug=True)