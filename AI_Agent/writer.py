import os
from dotenv import load_dotenv
import asyncio
import datetime
import requests
import json


load_dotenv()
mistral_api = os.getenv("mistral")


def generate(title, contents, additional_prompt = ""):

    load_dotenv()
    mistral_api = os.getenv("mistral")
    mistral_response_string = None

    prompt = f"""
    You are an AI writer tasked with rewriting ("spinning") a book chapter to make it more modern, engaging, and accessible while preserving the original meaning.

    ### Chapter Title:
    {title}

    ### Original Chapter:
    \"\"\"
    {contents}
    \"\"\"

    ### Your Task:
    Rewrite the chapter in a clear, modern style with better flow, easier words, and improved coherence. Keep the core storyline intact.

    Begin your rewritten chapter below:
    """
    prompt += additional_prompt
    url = "https://api.mistral.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {mistral_api}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-small-2503",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        if "choices" in data and data["choices"]: # Ensure choices list is not empty
            mistral_response_string = data["choices"][0]["message"]["content"]
            print(f"Mistral Response (first 200 chars): {mistral_response_string[:200]}...")
        else:
            print("Unexpected response from Mistral API: 'choices' key not found or empty.")
            print("Response data:", data)
    except requests.exceptions.Timeout:
        print("Error: Mistral API request timed out.")
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to Mistral API. Check your internet connection or API endpoint. {e}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
        print("Response Text:", e.response.text)
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from Mistral API response.")
        print("Raw Response:", response.text if 'response' in locals() else "No response received.")
    except Exception as e:
        print(f"An unexpected error occurred during API call: {e}")
        print("Raw Response (if available):", response.text if 'response' in locals() else "No response received.")

    return mistral_response_string, contents
