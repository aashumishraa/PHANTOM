import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Load environment variables from the .env file
load_dotenv()

# 2. Initialize the official Google GenAI client
# It automatically looks for GEMINI_API_KEY inside your .env
client = genai.Client()

def generate_attack_chain(raw_scan_json):
    """
    Takes raw JSON from the scanner and asks Gemini to write an executive attack chain.
    """
    
    system_prompt = """
    You are an expert Senior Penetration Tester. 
    I will give you raw JSON output from a vulnerability scanner. 
    Your job is to read the findings and write a short, 3-step 'Attack Chain' explaining how a hacker would exploit these vulnerabilities together.
    Keep it plain English for executives. Do not use markdown blocks, just raw text.
    """

    print("🧠 Gemini is processing the vulnerabilities...")
    
    # 3. Call the Gemini 2.5 Flash model (perfect for speed and efficiency in hackathons)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"Here is the raw scanner data: {raw_scan_json}",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=1000,
        )
    )
    
    return response.text

if __name__ == "__main__":
    # Pointing directly to the file your teammate Aditya pushed!
    target_file = os.path.join(os.path.dirname(__file__), "..", "temp_results", "6c6ffc5c-ecb2-418e-b8f1-15e48b014760_raw.json")
    
    try:
        with open(target_file, "r") as file:
            real_scan_data = file.read() 
            
        result = generate_attack_chain(real_scan_data)
        print("\n=== FINAL GEMINI ATTACK CHAIN REPORT ===")
        print(result)
        
    except FileNotFoundError:
        print(f"⚠️ Could not find {target_file}. Make sure you pulled the backend files!")
    except Exception as e:
        print(f"⚠️ An error occurred: {e}")