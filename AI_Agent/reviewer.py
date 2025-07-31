
import asyncio
import datetime
import os

import requests
import json
from dotenv import load_dotenv
from web_scraping.scraper import fetch_chapter

load_dotenv()
# mistral_api = os.getenv("mistral")
gemini_api = os.getenv("gemini")


def reviewer(original_text, spun_text, chapter_title):
    gemini_response_string = None

    prompt = f"""
    You are a scoring agent. Your job is to evaluate a rewritten book chapter.

    Original Chapter:
    \"\"\"
    {original_text[:2000]}
    \"\"\"

    Spun Chapter:
    \"\"\"
    {spun_text[:2000]}
    \"\"\"

    Score the rewritten chapter from 1 to 10 in these 5 areas:
    1. Coherence
    2. Readability
    3. Grammar
    4. Faithfulness to original
    5. Creativity

    Format:
    Coherence: #
    Readability: #
    Grammar: #
    Faithfulness: #
    Creativity: #
    Total Score: ##/50

    Then provide 2–3 lines of justification. Also suggest some areas of improvement.So that the score can be increased.
    """

    model_name = "gemini-1.5-flash"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_api}"

    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192
        }

    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()

        if "candidates" in data and data["candidates"]:
            if "content" in data["candidates"][0] and "parts" in data["candidates"][0]["content"] and data["candidates"][0]["content"]["parts"]:
                gemini_response_string = data["candidates"][0]["content"]["parts"][0]["text"]
                # print(f"Gemini Response (first 200 chars): {gemini_response_string[:200]}...")
            else:
                print("Gemini API response missing expected 'content' or 'parts' in candidate.")
                print("Response data:", data)
        elif "promptFeedback" in data:
            print("Gemini API blocked content due to safety settings or other feedback.")
            print("Prompt Feedback:", data["promptFeedback"])
        else:
            print("Unexpected response from Gemini API: 'candidates' key not found or empty.")
            print("Response data:", data)
    except requests.exceptions.Timeout:
        print("Error: Gemini API request timed out.")
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to Gemini API. Check your internet connection or API endpoint. {e}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
        print("Response Text:", e.response.text) # Use e.response.text for HTTP errors
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from Gemini API response.")
        print("Raw Response:", response.text if 'response' in locals() else "No response received.")
    except Exception as e:
        print(f"An unexpected error occurred during API call: {e}")
        print("Raw Response (if available):", response.text if 'response' in locals() else "No response received.")

    return gemini_response_string

