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
API_KEY = "GEMINI API KEY"

# Terminal Colors
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
RED = "\033[31m"

def color_text(text, color):
    """ ANSI color."""
    return f"{color}{text}{RESET}"


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

        print(color_text("\nSelect a clipping to include (type the number):", BOLD))
        for idx, (title, text) in enumerate(page_clippings, start=1):
            print(f"{idx}. {color_text(title, CYAN)}\n   {color_text(text[:100] + '...', YELLOW)}")

        print(color_text("\nType 'next' for more, 'done' to finish, or 'exit' to quit.", MAGENTA))
        user_input = input(color_text("Your Choice: ", BLUE)).strip().lower()

        if user_input == "next":
            if end >= total:
                print(color_text("No more clippings to show.", RED))
            else:
                current_page += 1
        elif user_input == "exit":
            print(color_text("Exiting selection.", RED))
            break
        elif user_input == "done":
            break
        else:
            try:
                choice = int(user_input)
                if 1 <= choice <= len(page_clippings):
                    selected.append(page_clippings[choice - 1][1])
                    print(color_text("Clipping added to prompt.", GREEN))
                else:
                    print(color_text("Invalid choice. Try again.", RED))
            except ValueError:
                print(color_text("Invalid input. Try again.", RED))

    return selected


def format_response(response_text):
    """
    Format the AI response for better readability.
    """
    formatted = []
    for line in response_text.splitlines():
        if line.startswith("- "):  # Bullet points
            formatted.append(f"  {color_text('•', GREEN)} {line[2:]}")
        elif line.startswith("#"):  # Headings
            formatted.append(color_text(line, CYAN))
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
            return f"{color_text('Error:', RED)} {response.status} - {response.reason}"

    except Exception as e:
        return f"{color_text('Error:', RED)} {e}"


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
    print(color_text("KINDLE CLIPPINGS AI ASSISTANT", BOLD))
    print(color_text("github.com/cankurttekin/kindle-ai", BOLD))
    print(color_text("Type 'exit' to quit.", MAGENTA))

    clippings = load_clippings()
    if not clippings:
        print(color_text("No clippings found!", RED))
        #return

    while True:
        user_input = input(color_text("\nQuestion: ", BLUE))
        if user_input.lower() == "exit":
            print(color_text("Goodbye!", GREEN))
            break

        selected_clippings = select_clippings(clippings)
        if not selected_clippings:
            print(color_text("No clippings selected. Proceeding with question only.", YELLOW))

        prompt = generate_prompt_with_clippings(selected_clippings, user_input)
        response = get_response_from_gemini(prompt)
        print(color_text("\nGemini AI Response:", CYAN))
        print("-" * 40)
        print(response)
        print("-" * 40)


if __name__ == "__main__":
    main()


