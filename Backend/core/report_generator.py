import json
import os
from fpdf import FPDF

class PhantomReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.set_text_color(30, 58, 138) # Dark blue
        self.cell(0, 10, "PHANTOM Security Assessment Report", ln=True)
        self.ln(5)
        self.set_draw_color(30, 58, 138)
        self.set_line_width(1)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)

def generate_pdf_report():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'mock_report.json')
    output_pdf_path = os.path.join(current_dir, 'phantom_assessment_report.pdf')

    print("Reading mock data...")
    with open(json_path, 'r') as f:
        data = json.load(f)

    print("Building layout structure...")
    pdf = PhantomReport()
    pdf.add_page()
    
    # Target Meta Info
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(51, 51, 51)
    pdf.cell(0, 10, f"Target System: {data['target_url']}", ln=True)
    pdf.ln(5)

    # Risk Score Block (Red warning callout banner)
    pdf.set_fill_color(254, 226, 226)
    pdf.set_text_color(153, 27, 27)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 12, f"  Overall Risk Score: {data['risk_score']}/100", ln=True, fill=True)
    pdf.ln(8)

    # Executive Summary Section
    pdf.set_text_color(30, 58, 138)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Executive Summary", ln=True)
    pdf.set_text_color(51, 51, 51)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, data['summary'])
    pdf.ln(10)

    # Vulnerability Findings Loops
    pdf.set_text_color(30, 58, 138)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Vulnerability Findings", ln=True)
    pdf.ln(2)

    for finding in data['findings']:
        # Finding Header Box
        pdf.set_fill_color(248, 250, 252)
        pdf.set_text_color(30, 41, 59)
        pdf.set_font("Arial", "B", 11)
        header_text = f" [{finding['severity']}] {finding['id']}: {finding['title']}"
        pdf.cell(0, 10, header_text, ln=True, fill=True)
        
        # Finding Details
        pdf.set_font("Arial", "I", 9)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, f"   Discovered via: {finding['tool']}", ln=True)
        
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(51, 51, 51)
        pdf.multi_cell(0, 6, f"   {finding['description']}")
        pdf.ln(6)

    # Lock and save artifact
    print("Compiling final document...")
    pdf.output(output_pdf_path)
    print(f"Success! Final document locked and saved at: {output_pdf_path}")

if __name__ == "__main__":
    generate_pdf_report()