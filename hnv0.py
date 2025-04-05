import datetime
import difflib # Import the library for finding close matches

# --- Data Store for Waste Items (Based on Fairfax County, VA Rules - April 2025) ---
# (Keeping the dictionary definition short for brevity, assume it's the same as before)
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

    # --- Compostable (Check local program details!) ---
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
}

# --- Alias Dictionary ---
# (Assume the same ALIASES dictionary as before)
ALIASES = {
    "apple": "apple core", "banana": "banana peel", "peel": "banana peel", "core": "apple core",
    "grounds": "coffee grounds", "coffee": "coffee grounds", "tea": "tea bag", "eggshell": "egg shells",
    "eggshells": "egg shells", "bottle": "plastic bottle", "can": "aluminum can", "jar": "glass jar",
    "box": "cardboard box", "jug": "milk jug", "tub": "yogurt tub", "mail": "junk mail",
    "bag": "plastic bag", "wrapper": "candy wrapper", "straw": "plastic straw", "utensil": "plastic utensil",
    "wrap": "plastic wrap", "foam": "styrofoam", "cup": "coffee cup", "bulb": "light bulb",
    "batteries": "battery", "clothes": "clothing", "orange peel": "fruit", "potato peel": "vegetable",
}

# Combine all valid known terms for spell checking
VALID_TERMS = list(FAIRFAX_COUNTY_RULES.keys()) + list(ALIASES.keys())
# Optional: Remove duplicates if any overlap exists, though unlikely here
VALID_TERMS = list(set(VALID_TERMS))


def get_sorting_info(item_description, rules, aliases, valid_terms_list):
    """
    Attempts to find sorting information for an item, checking aliases,
    exact matches, keyword matches, and finally suggesting corrections for typos.

    Args:
        item_description (str): The user's input description of the item.
        rules (dict): The dictionary containing item keywords and sorting rules.
        aliases (dict): Dictionary mapping simple terms to keys in 'rules'.
        valid_terms_list (list): A combined list of keys from rules and aliases.

    Returns:
        dict: A dictionary containing status and relevant data. Status can be:
              'found', 'not_found', 'suggestion_found', 'multiple_suggestions_found', 'error'.
    """
    query = item_description.lower().strip()
    if not query:
        return {"query": query, "status": "not_found", "category": "Unknown", "notes": "Please enter an item description."}

    # Step 1: Check Aliases
    if query in aliases:
        canonical_key = aliases[query]
        if canonical_key in rules:
            result = rules[canonical_key]
            return {"query": query, "alias_used": canonical_key, "status": "found", **result}
        else:
             return {"query": query, "status": "error", "category": "Error", "notes": f"Internal data error: Alias '{query}' points to missing rule '{canonical_key}'."}

    # Step 2: Exact Match in Rules
    if query in rules:
        result = rules[query]
        return {"query": query, "status": "found", **result}

    # Step 3: Keyword Matching in Rules (as fallback)
    # (Keeping keyword logic brief here, assume same as before)
    matched_key = None
    # ... (keyword matching logic) ...
    if matched_key:
         result = rules[matched_key]
         return {"query": query, "match_used": matched_key, "status": "found", **result}


    # --- Step 4: Check for Misspellings/Suggestions (if not found yet) ---
    # Use difflib to find close matches in our combined list of known terms
    # cutoff=0.6 means sequences must be at least 60% similar. Adjust if needed.
    suggestions = difflib.get_close_matches(query, valid_terms_list, n=3, cutoff=0.6)

    if suggestions:
        if len(suggestions) == 1:
            # Found a single likely correction
            return {"query": query, "status": "suggestion_found", "suggestion": suggestions[0]}
        else:
            # Found multiple possibilities
            return {"query": query, "status": "multiple_suggestions_found", "suggestions": suggestions}
    else:
        # --- Step 5: Truly Not Found ---
        return {"query": query, "status": "not_found", "category": "Unknown", "notes": "Sorry, I don't have specific info or suggestions for that item. Check Fairfax County's WasteWise tool or website."}

# --- Main Program Loop (Modified to handle suggestions) ---
if __name__ == "__main__":
    print("Welcome to the Waste Sorter Helper (Tysons/Fairfax County, VA Rules)")
    print(f"Using rules based on Fairfax County guidelines (as of approx {datetime.date.today().strftime('%B %Y')}).")
    print("Rules can change - always double-check official sources if unsure.")
    print("Enter the item you want to sort (e.g., 'apple', 'bottle', 'styrofoam cup'), or type 'quit' to exit.")

    while True:
        user_input = input("\nItem Description: ")
        if user_input.lower() == 'quit':
            break

        # Get initial info attempt
        info = get_sorting_info(user_input, FAIRFAX_COUNTY_RULES, ALIASES, VALID_TERMS)

        # --- Handle different statuses from get_sorting_info ---
        if info['status'] == 'found':
            print("-" * 20)
            print(f"Query: '{info['query']}'")
            print(f"Category: {info['category']}")
            if info.get('alias_used'):
                 print(f"(Interpreted as: '{info['alias_used']}')")
            elif info.get('match_used'):
                 print(f"(Based on keyword match for: '{info['match_used']}')")
            print(f"Notes: {info['notes']}")
            print("-" * 20)

        elif info['status'] == 'suggestion_found':
            suggestion = info['suggestion']
            print(f"Did you mean '{suggestion}'? [y/n]")
            confirmation = input("> ").lower()
            if confirmation == 'y' or confirmation == 'yes':
                # Re-run the search with the suggested term
                info = get_sorting_info(suggestion, FAIRFAX_COUNTY_RULES, ALIASES, VALID_TERMS)
                # Check the result of the new search (should be 'found' now)
                if info['status'] == 'found':
                     print("-" * 20)
                     print(f"Query: '{suggestion}' (using suggestion)")
                     print(f"Category: {info['category']}")
                     if info.get('alias_used'):
                          print(f"(Interpreted as: '{info['alias_used']}')")
                     print(f"Notes: {info['notes']}")
                     print("-" * 20)
                else: # Should not happen if suggestion logic is correct
                     print(f"Sorry, couldn't find details for suggested item '{suggestion}'.")

        elif info['status'] == 'multiple_suggestions_found':
            suggestions = info['suggestions']
            print("Did you mean one of these?")
            for i, sug in enumerate(suggestions):
                print(f"{i+1}. {sug}")
            print("Enter the number of your choice, or 'n' for none:")
            choice = input("> ").lower()
            try:
                num_choice = int(choice)
                if 1 <= num_choice <= len(suggestions):
                    chosen_suggestion = suggestions[num_choice - 1]
                    # Re-run the search with the chosen suggestion
                    info = get_sorting_info(chosen_suggestion, FAIRFAX_COUNTY_RULES, ALIASES, VALID_TERMS)
                    if info['status'] == 'found':
                         print("-" * 20)
                         print(f"Query: '{chosen_suggestion}' (using selection)")
                         print(f"Category: {info['category']}")
                         if info.get('alias_used'):
                             print(f"(Interpreted as: '{info['alias_used']}')")
                         print(f"Notes: {info['notes']}")
                         print("-" * 20)
                    else: # Should not happen
                         print(f"Sorry, couldn't find details for selected item '{chosen_suggestion}'.")
                else:
                    print("Invalid number chosen.")
            except ValueError:
                if choice != 'n' and choice != 'no':
                    print("Invalid input.")

        elif info['status'] == 'not_found':
             print("-" * 20)
             print(f"Query: '{info['query']}'")
             print(f"Category: {info['category']}")
             print(f"Notes: {info['notes']}")
             print("-" * 20)

        elif info['status'] == 'error':
             print("-" * 20)
             print(f"Query: '{info['query']}'")
             print(f"ERROR: {info['notes']}")
             print("-" * 20)


    print("Goodbye!")