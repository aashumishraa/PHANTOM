I have pushed the code for AI parsing of the raw scan report generated from the backend in the branch named "Arihant". This reads the raw report and formats it into a JSON file.

//Update
The output JSON file contains three variables (keys): 

        **executive_summary - It is a string which summarizes the entire report into quick statements and point out the enitre risk level.
        **possible_attack_chains - It is an array of strings listing multiple steps of the multiple attack chain.
        **critical_remediation - It points out the most vulnarable bug in the software




Disclaimer: But to use it, you will have to add your API key in the Environment variable file (.env) to protect system from crashing.


Sample Report File

{
    "executive_summary": "The target system exhibits critical vulnerabilities across multiple services, indicating a high likelihood of compromise. Immediate action is required to secure database endpoints and enforce strict authentication protocols.",
    "possible_attack_chains": [
        {
            "chain_name": "Database Exfiltration via SQL Injection",
            "steps": [
                "Step 1: The attacker identifies an unescaped input parameter on the `/login` endpoint.",
                "Step 2: By injecting a malicious SQL payload, the attacker bypasses the authentication check and gains administrative access.",
                "Step 3: The attacker dumps the user table, exposing sensitive customer credentials and personal data."
            ]
        },
        {
            "chain_name": "Server Takeover via Weak SSH Credentials",
            "steps": [
                "Step 1: The attacker performs an automated port scan and discovers SSH port 22 is open to the public internet.",
                "Step 2: A brute-force dictionary attack successfully guesses the default root password.",
                "Step 3: The attacker installs a persistent backdoor and uses the server as a pivot point to attack internal network resources."
            ]
        }
    ],
    "critical_remediation": "Immediately patch all SQL injection vulnerabilities on public-facing endpoints and disable external access to SSH port 22."
}