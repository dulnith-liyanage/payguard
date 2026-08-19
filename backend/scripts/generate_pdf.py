import os
import subprocess
import shutil
import markdown

REPORT_MD_PATH = "/Users/dulnithliyanage/Academics/payguard/ENGINEERING_REPORT.md"
DOCS_MD_PATH = "/Users/dulnithliyanage/Academics/payguard/docs/ENGINEERING_REPORT.md"
HTML_OUTPUT_PATH = "/Users/dulnithliyanage/Academics/payguard/docs/ENGINEERING_REPORT.html"
PDF_DOCS_PATH = "/Users/dulnithliyanage/Academics/payguard/docs/ENGINEERING_REPORT.pdf"
PDF_ROOT_PATH = "/Users/dulnithliyanage/Academics/payguard/ENGINEERING_REPORT.pdf"

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Copy concise MD to docs
shutil.copyfile(REPORT_MD_PATH, DOCS_MD_PATH)

with open(REPORT_MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert markdown to HTML
html_body = markdown.markdown(
    md_content,
    extensions=[
        "tables",
        "fenced_code",
        "codehilite",
        "toc",
        "sane_lists",
    ]
)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>PayGuard - Short Engineering Report</title>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
  @page {{
    size: A4;
    margin: 12mm 14mm 12mm 14mm;
    @bottom-right {{
      content: "Page " counter(page);
      font-size: 8pt;
      color: #64748b;
    }}
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1e293b;
    line-height: 1.38;
    font-size: 9.2pt;
    background: #ffffff;
    margin: 0;
    padding: 0;
  }}

  h1 {{
    color: #0f172a;
    font-size: 16pt;
    border-bottom: 2px solid #2563eb;
    padding-bottom: 4px;
    margin-top: 0;
    margin-bottom: 4px;
  }}

  h2 {{
    color: #0f172a;
    font-size: 11pt;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 2px;
    margin-top: 10px;
    margin-bottom: 4px;
    page-break-after: avoid;
  }}

  h3 {{
    color: #1e293b;
    font-size: 9.8pt;
    margin-top: 8px;
    margin-bottom: 3px;
    page-break-after: avoid;
  }}

  p {{
    margin: 3px 0 5px 0;
  }}

  ul, ol {{
    margin: 3px 0 5px 0;
    padding-left: 18px;
  }}

  li {{
    margin-bottom: 2px;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 6px 0;
    font-size: 8.2pt;
    page-break-inside: avoid;
  }}

  th, td {{
    border: 1px solid #cbd5e1;
    padding: 4px 6px;
    text-align: left;
  }}

  th {{
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 600;
  }}

  tr:nth-child(even) {{
    background-color: #f8fafc;
  }}

  pre {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 6px 8px;
    overflow-x: auto;
    font-size: 7.8pt;
    line-height: 1.25;
    margin: 4px 0 6px 0;
    page-break-inside: avoid;
  }}

  code {{
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
    font-size: 8.5pt;
    background: #f1f5f9;
    padding: 1px 3px;
    border-radius: 3px;
    color: #0f172a;
  }}

  pre code {{
    background: transparent;
    padding: 0;
  }}

  hr {{
    border: 0;
    height: 1px;
    background: #e2e8f0;
    margin: 8px 0;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

with open(HTML_OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Generated HTML at {HTML_OUTPUT_PATH}")

# Convert HTML to PDF using Chrome Headless
chrome_cmd = [
    CHROME_PATH,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    "--run-all-compositor-stages-before-draw",
    "--virtual-time-budget=2000",
    f"--print-to-pdf={PDF_DOCS_PATH}",
    f"file://{HTML_OUTPUT_PATH}"
]

subprocess.run(chrome_cmd, check=True)
shutil.copyfile(PDF_DOCS_PATH, PDF_ROOT_PATH)
print("Successfully generated PDF!")
