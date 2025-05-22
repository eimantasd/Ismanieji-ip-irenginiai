import requests
import json

# The API endpoint for dictionaryapi.dev
API_BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

def get_word_meaning(word):
    """
    Fetches word meanings from dictionaryapi.dev.
    """
    if not word:
        return "Error: No word provided."

    url = f"{API_BASE_URL}{word}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        
        data = response.json()
        return format_api_response(data, word)

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            return f"Sorry, couldn't find a definition for '{word}'."
        return f"HTTP error occurred: {http_err} - {response.text}"
    except requests.exceptions.RequestException as req_err:
        return f"Error fetching definition: {req_err}"
    except json.JSONDecodeError:
        return "Error: Could not decode the server's response."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def format_api_response(api_data, original_word):
    """
    Formats the JSON response from dictionaryapi.dev into a readable string.
    """
    if not api_data or not isinstance(api_data, list):
        # The API might return an object with 'title', 'message', 'resolution' on 404
        if isinstance(api_data, dict) and "title" in api_data:
            return f"{api_data.get('title', 'Error')}: {api_data.get('message', 'Could not find the word.')}"
        return f"No definitions found for '{original_word}' or unexpected API response format."

    formatted_output = []
    
    # The API returns a list, usually with one main entry for the word
    for entry_index, entry in enumerate(api_data):
        word = entry.get("word", original_word)
        phonetic = entry.get("phonetic", "")
        
        if entry_index == 0: # Main header for the first entry
            formatted_output.append(f"Word: {word}")
            if phonetic:
                formatted_output.append(f"Phonetic: {phonetic}")
        elif len(api_data) > 1: # If multiple entries (e.g. different etymologies)
            formatted_output.append(f"\n--- Alternative Entry for {word} ---")
            if phonetic:
                formatted_output.append(f"Phonetic: {phonetic}")

        if "meanings" in entry:
            for meaning in entry["meanings"]:
                part_of_speech = meaning.get("partOfSpeech", "N/A")
                formatted_output.append(f"\nAs {part_of_speech.capitalize()}:")
                
                for i, definition_obj in enumerate(meaning.get("definitions", [])):
                    definition = definition_obj.get("definition", "No definition text.")
                    example = definition_obj.get("example", "")
                    
                    formatted_output.append(f"  {i+1}. {definition}")
                    if example:
                        formatted_output.append(f"     Example: \"{example}\"")
        else:
            formatted_output.append("  No specific meanings found in this entry.")
            
    if not formatted_output or (len(formatted_output) == 2 and "Phonetic" in formatted_output[1] and not "meanings" in api_data[0]):
        return f"No detailed definitions found for '{original_word}'."

    return "\n".join(formatted_output)

# --- Example Usage (for testing this file directly) ---
if __name__ == "__main__":
    test_word = "hello"
    print(f"--- Looking up: {test_word} ---")
    meaning = get_word_meaning(test_word)
    print(meaning)

    print("\n--- Looking up: programming ---")
    meaning_programming = get_word_meaning("programming")
    print(meaning_programming)

    print("\n--- Looking up: nonexistingwordxyz123 ---")
    meaning_nonexistent = get_word_meaning("nonexistingwordxyz123")
    print(meaning_nonexistent)