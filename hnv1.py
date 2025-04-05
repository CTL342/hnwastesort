import datetime
import difflib # Still needed for fallback suggestions

# --- Data Store for Waste Items (Based on Fairfax County, VA Rules - April 2025) ---
# Assume FAIRFAX_COUNTY_RULES is defined as before
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
# Assume ALIASES is defined as before
ALIASES = {
    "apple": "apple core", "banana": "banana peel", "peel": "banana peel", "core": "apple core",
    "grounds": "coffee grounds", "coffee": "coffee grounds", "tea": "tea bag", "eggshell": "egg shells",
    "eggshells": "egg shells", "bottle": "plastic bottle", "can": "aluminum can", "jar": "glass jar",
    "box": "cardboard box", "jug": "milk jug", "tub": "yogurt tub", "mail": "junk mail",
    "bag": "plastic bag", "wrapper": "candy wrapper", "straw": "plastic straw", "utensil": "plastic utensil",
    "wrap": "plastic wrap", "foam": "styrofoam", "cup": "coffee cup", "bulb": "light bulb",
    "batteries": "battery", "clothes": "clothing", "orange peel": "fruit", "potato peel": "vegetable",
}

# Combine all valid known terms and sort them longest first
VALID_TERMS = list(FAIRFAX_COUNTY_RULES.keys()) + list(ALIASES.keys())
VALID_TERMS = sorted(list(set(VALID_TERMS)), key=len, reverse=True) # Sort longest first

def get_sorting_info(item_description, rules, aliases, valid_terms_list):
    """
    Attempts to find sorting information by locating known item keywords within
    the user's input phrase. Falls back to suggesting corrections for the whole phrase.

    Args:
        item_description (str): The user's input description.
        rules (dict): The main sorting rules dictionary.
        aliases (dict): Dictionary mapping simple terms to keys in 'rules'.
        valid_terms_list (list): Sorted list of known terms (keys from rules/aliases).

    Returns:
        dict: Dictionary with status ('found', 'suggestion_found', etc.) and data.
    """
    query = item_description.lower().strip()
    if not query:
        return {"query": query, "status": "not_found", "category": "Unknown", "notes": "Please enter an item description."}

    # --- Step 1: Keyword Spotting ---
    # Iterate through known terms (longest first) and see if they exist in the query
    found_term = None
    for term in valid_terms_list:
        # Check if the known term is present as a substring in the user query
        if term in query:
            found_term = term
            break # Stop after finding the first (longest) match

    if found_term:
        # Found a known term within the user's input!
        canonical_key = found_term
        alias_used = None

        # Check if the found term is an alias that needs resolving
        if found_term in aliases:
            alias_used = found_term # Store the alias that was found
            canonical_key = aliases[found_term] # Get the actual key for the rules dict

        # Now look up the canonical key in the main rules
        if canonical_key in rules:
            result = rules[canonical_key]
            return {
                "query": query,
                "keyword_identified": found_term, # Show which keyword we spotted
                "alias_resolution": canonical_key if alias_used and alias_used != canonical_key else None, # Show what alias resolved to, if different
                "status": "found",
                **result # Unpack category/notes
            }
        else:
            # Data integrity issue: alias points to non-existent rule
            return {"query": query, "status": "error", "category": "Error", "notes": f"Internal data error: Alias '{found_term}' points to missing rule '{canonical_key}'."}


    # --- Step 2: Fallback to Misspelling Suggestion (if no keyword spotted) ---
    # Use difflib on the *entire* query against the valid terms list
    # Only do this if we didn't find any keywords inside the query
    suggestions = difflib.get_close_matches(query, valid_terms_list, n=3, cutoff=0.6)

    if suggestions:
        if len(suggestions) == 1:
            return {"query": query, "status": "suggestion_found", "suggestion": suggestions[0]}
        else:
            return {"query": query, "status": "multiple_suggestions_found", "suggestions": suggestions}
    else:
        # --- Step 3: Truly Not Found ---
        return {"query": query, "status": "not_found", "category": "Unknown", "notes": "Sorry, couldn't identify a known item in your description or find close matches. Check Fairfax County's WasteWise tool or website."}


# --- Main Program Loop (Modified Output for 'found') ---
if __name__ == "__main__":
    print("Welcome to the Waste Sorter Helper (Tysons/Fairfax County, VA Rules)")
    print(f"Using rules based on Fairfax County guidelines (as of approx {datetime.date.today().strftime('%B %Y')}).")
    print("Rules can change - always double-check official sources if unsure.")
    print("Enter a description containing the item you want to sort (e.g., 'what about an apple core?', 'empty milk jug'), or type 'quit' to exit.")


    while True:
        user_input = input("\nItem Description: ")
        if user_input.lower() == 'quit':
            break

        # Pass the pre-sorted valid_terms list
        info = get_sorting_info(user_input, FAIRFAX_COUNTY_RULES, ALIASES, VALID_TERMS)

        # --- Handle different statuses ---
        if info['status'] == 'found':
            print("-" * 20)
            print(f"Query: '{info['query']}'")
            # Display the keyword that triggered the match
            print(f"Identified Keyword: '{info['keyword_identified']}'")
            # Optionally show how an alias was resolved if it happened
            if info.get('alias_resolution'):
                 print(f"(Interpreted as: '{info['alias_resolution']}')")
            print(f"Category: {info['category']}")
            print(f"Notes: {info['notes']}")
            print("-" * 20)

        # --- Suggestion handling logic remains the same as before ---
        elif info['status'] == 'suggestion_found':
            suggestion = info['suggestion']
            print(f"No known item found in your phrase. Did you misspell and mean '{suggestion}'? [y/n]") # Modified prompt slightly
            confirmation = input("> ").lower()
            if confirmation == 'y' or confirmation == 'yes':
                # Re-run with the suggestion
                info = get_sorting_info(suggestion, FAIRFAX_COUNTY_RULES, ALIASES, VALID_TERMS)
                # Handle result (mostly 'found' now, print its details)
                if info['status'] == 'found':
                     print("-" * 20)
                     print(f"Query: '{suggestion}' (using suggestion)")
                     print(f"Identified Keyword: '{info['keyword_identified']}'")
                     if info.get('alias_resolution'):
                         print(f"(Interpreted as: '{info['alias_resolution']}')")
                     print(f"Category: {info['category']}")
                     print(f"Notes: {info['notes']}")
                     print("-" * 20)
                else:
                     print(f"Sorry, couldn't find details for suggested item '{suggestion}'.")

        elif info['status'] == 'multiple_suggestions_found':
            suggestions = info['suggestions']
            print("No known item found in your phrase. Did you misspell and mean one of these?") # Modified prompt slightly
            for i, sug in enumerate(suggestions):
                print(f"{i+1}. {sug}")
            print("Enter the number of your choice, or 'n' for none:")
            choice = input("> ").lower()
            try:
                num_choice = int(choice)
                if 1 <= num_choice <= len(suggestions):
                    chosen_suggestion = suggestions[num_choice - 1]
                    # Re-run with chosen suggestion
                    info = get_sorting_info(chosen_suggestion, FAIRFAX_COUNTY_RULES, ALIASES, VALID_TERMS)
                    if info['status'] == 'found':
                        print("-" * 20)
                        print(f"Query: '{chosen_suggestion}' (using selection)")
                        print(f"Identified Keyword: '{info['keyword_identified']}'")
                        if info.get('alias_resolution'):
                            print(f"(Interpreted as: '{info['alias_resolution']}')")
                        print(f"Category: {info['category']}")
                        print(f"Notes: {info['notes']}")
                        print("-" * 20)
                    else:
                        print(f"Sorry, couldn't find details for selected item '{chosen_suggestion}'.")
                else:
                    print("Invalid number chosen.")
            except ValueError:
                if choice != 'n' and choice != 'no':
                    print("Invalid input.")

        # --- Not Found and Error handling remain the same ---
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