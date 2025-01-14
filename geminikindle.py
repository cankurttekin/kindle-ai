#
import os
import json
import http.client
import ssl

# Constants
KINDLE_DOC_DIR = "/mnt/us/documents"
CLIPPINGS_FILE = os.path.join(KINDLE_DOC_DIR, "My Clippings.txt")
API_URL = "/v1beta/models/gemini-1.5-flash:generateContent"
API_HOST = "generativelanguage.googleapis.com"
API_KEY = "GEMINI_API_KEY"

# Terminal Colors
RESET = "\033[0m"          # Reset all styles
BOLD = "\033[1m"           # Bold text
UNDERLINE = "\033[4m"      # Underlined text
HIGHLIGHT = "\033[7m"      # Background highlight (reverse colors)
BRIGHT = "\033[90m"        # Bright text for subtle emphasis
DIM = "\033[2m"            # Dimmed text

# Colorless
TEXT_PRIMARY = BOLD        # Primary text style
TEXT_SECONDARY = BRIGHT    # Secondary text, subtle emphasis
TEXT_HIGHLIGHT = HIGHLIGHT  # Highlight for prompts and headers

def format_text(text, style):
    """Apply ANSI styles to text."""
    return f"{style}{text}{RESET}"


def load_clippings():
    """
    Load clippings from the file and return a list of tuples (title, text).
    Each clipping is to be separated by "==========".
    """
    if not os.path.isfile(CLIPPINGS_FILE):
        return []

    with open(CLIPPINGS_FILE, "r", encoding="utf-8") as file:
        clippings = file.read().split("==========")
        parsed_clippings = []
        for clipping in clippings:
            lines = [line.strip() for line in clipping.strip().split("\n") if line.strip()]
            if len(lines) < 2:
                continue
            title = lines[0]
            text = lines[-1]
            parsed_clippings.append((title, text))
        return parsed_clippings


def select_clippings(clippings):
    """
    Paginate through clippings and allow the user to select one or more.
    Returns the selected clippings as a list of strings.
    """
    selected = []
    per_page = 3
    total = len(clippings)
    current_page = 0

    while True:
        start = current_page * per_page
        end = start + per_page
        page_clippings = clippings[start:end]

        print(format_text("\nSelect a clipping to include (type the number):", BOLD))
        for idx, (title, text) in enumerate(page_clippings, start=1):
            print(f"{idx}. {format_text(title, TEXT_PRIMARY)}\n   {format_text(text[:100] + '...', TEXT_SECONDARY)}")

        print(format_text("\nType 'next' for more, 'done' to finish, or 'exit' to quit.", TEXT_SECONDARY))
        user_input = input(format_text("Your Choice: ", TEXT_HIGHLIGHT)).strip().lower()

        if user_input == "next":
            if end >= total:
                print(format_text("No more clippings to show.", DIM))
            else:
                current_page += 1
        elif user_input == "exit":
            print(format_text("Exiting selection.", DIM))
            break
        elif user_input == "done":
            break
        else:
            try:
                choice = int(user_input)
                if 1 <= choice <= len(page_clippings):
                    selected.append(page_clippings[choice - 1][1])
                    print(format_text("Clipping added to prompt.", TEXT_PRIMARY))
                else:
                    print(format_text("Invalid choice. Try again.", DIM))
            except ValueError:
                print(format_text("Invalid input. Try again.", DIM))

    return selected


def format_response(response_text):
    """
    Format the AI response with better readability.
    """
    formatted = []
    for line in response_text.splitlines():
        if line.startswith("- "):  # Bullet points
            formatted.append(f"  {format_text('•', TEXT_PRIMARY)} {line[2:]}")
        elif line.startswith("#"):  # Headings
            formatted.append(format_text(line, UNDERLINE))
        else:  # Regular text
            formatted.append(line)
    return "\n".join(formatted)


def get_response_from_gemini(prompt):
    """
    Send a prompt to the Gemini AI API and receive a response.
    """
    headers = {
        "Content-Type": "application/json",
    }
    payload = json.dumps({
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    })

    try:
        # Disable SSL certificate verification
        context = ssl._create_unverified_context()

        conn = http.client.HTTPSConnection(API_HOST, context=context)
        url_with_key = f"{API_URL}?key={API_KEY}"
        conn.request("POST", url_with_key, payload, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()

        if response.status == 200:
            response_data = json.loads(data.decode("utf-8"))
            raw_response = "\n".join(part["text"] for part in response_data["candidates"][0]["content"]["parts"])
            return format_response(raw_response)
        else:
            return f"{format_text('Error:', DIM)} {response.status} - {response.reason}"

    except Exception as e:
        return f"{format_text('Error:', DIM)} {e}"


def generate_prompt_with_clippings(clippings, question):
    """
    Combine clippings and a question into a structured prompt.
    """
    combined_clippings = "\n\n".join(f"- {clip}" for clip in clippings)
    prompt = (
        f"I have some reading clippings. Please analyze them and answer my question.\n\n"
        f"Clippings:\n{combined_clippings}\n\nQuestion:\n{question}\n"
    )
    return prompt


def main():
    print("█" * 42)
    print(format_text("KINDLE CLIPPINGS AI ASSISTANT", TEXT_PRIMARY))
    print(format_text("github.com/cankurttekin/kindle-ai", TEXT_SECONDARY))

    print(format_text("Type 'exit' to quit.", TEXT_SECONDARY))
    print("█" * 42)
    print()
    clippings = load_clippings()
    if not clippings:
        print(format_text("No clippings/highlights found in your device.", DIM))
        #return

    while True:
        print("")
        user_input = input(format_text("Question:", TEXT_HIGHLIGHT))
        if user_input.lower() == "exit":
            print(format_text("Bye.", DIM))
            break

        selected_clippings = select_clippings(clippings)
        if not selected_clippings:
            print(format_text("No clippings selected. Proceeding with question only.", TEXT_SECONDARY))
            prompt = user_input
        else:
            prompt = generate_prompt_with_clippings(selected_clippings, user_input)

        response = get_response_from_gemini(prompt)
        print()
        print(format_text("AI Response:", TEXT_HIGHLIGHT))
        print("★" * 42)
        print(response)
        print("★" * 42)


if __name__ == "__main__":
    main()

