I have pushed the code for AI parsing of the raw scan report generated from the backend in the branch named "Arihant". This reads the raw report and formats it into a JSON file.


The output JSON file contains three variables (keys): 

        **executive_summary - It is a string which summarizes the entire report into quick statements and point out the enitre risk level.
        **attack_chain - It is an array of strings listing multiple steps of the attack chain.
        **critical_remediation - It points out the most vulnarable bug in the software




Disclaimer: But to use it, you will have to add your API key in the Environment variable file (.env) to protect system from crashing.