import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Load environment variables
load_dotenv()

# 2. Initialize the client
client = genai.Client()

def generate_attack_chain(raw_scan_json):
    """
    Takes raw JSON from the scanner and asks Gemini to write a structured JSON executive report.
    """
    # === NEW: THE BULLETPROOF SAFETY NET ===
    # If the file is empty, missing, or just contains empty brackets {}
    if not raw_scan_json or raw_scan_json.strip() == "" or raw_scan_json.strip() == "{}":
        print("🛡️ Safety Net Triggered: No vulnerabilities found in scan data.")
        # Return a perfectly formatted default JSON so the PDF generator doesn't crash
        return json.dumps({
            "executive_summary": "No vulnerabilities were detected during this scan. The target appears secure.",
            "attack_chain": [
                "Step 1: Scan initiated and completed.",
                "Step 2: No exploitable vulnerabilities or misconfigurations discovered.",
                "Step 3: Target deemed safe against standard automated attacks."
            ],
            "critical_remediation": "No immediate action required. Continue regular monitoring."
        })
    # ========================================

    system_prompt = """
    You are an expert Senior Penetration Tester. 
    Analyze the raw vulnerability scan JSON.
    You MUST output a strictly formatted JSON object following this exact structure:
    {
        "executive_summary": "A 2-sentence summary of the overall risk level.",
        "attack_chain": [
            "Step 1: Explain the initial foothold...",
            "Step 2: Explain the privilege escalation or lateral movement...",
            "Step 3: Explain the final impact (data exfiltration, takeover, etc.)..."
        ],
        "critical_remediation": "The number one thing the development team must fix immediately."
    }
    """

    print("🧠 Gemini is generating the structured JSON report...")
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"Here is the raw scanner data: {raw_scan_json}",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=1000,
            response_mime_type="application/json",
        )
    )
    
    return response.text

if __name__ == "__main__":
    target_file = os.path.join(os.path.dirname(__file__), "..", "temp_results", "6c6ffc5c-ecb2-418e-b8f1-15e48b014760_raw.json")
    
    try:
        with open(target_file, "r") as file:
            real_scan_data = file.read() 
            
        result = generate_attack_chain(real_scan_data)
        
        # NEW: We parse the result to prove it is valid JSON
        parsed_json = json.loads(result)
        
        print("\n=== FINAL STRUCTURED REPORT ===")
        print(json.dumps(parsed_json, indent=4))
        
    except FileNotFoundError:
        print(f"⚠️ Could not find {target_file}. Make sure you pulled the backend files!")
    except json.JSONDecodeError:
        print("⚠️ Gemini did not return valid JSON! Here is what it returned instead:")
        print(result)
    except Exception as e:
        print(f"⚠️ An error occurred: {e}")