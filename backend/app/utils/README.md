# Lighthouse Matcher Test Tool

A testing tool for the SEO Agent's Lighthouse parser and HTML matcher. This tool demonstrates how to analyze HTML content with Lighthouse and match SEO issues back to specific code locations.

## 🎯 What This Tool Does

The `test_lighthouse_parser.py` script:

1. **Loads** your HTML file (`test_seo_page.html`)
2. **Sends** it to the Lighthouse service for SEO analysis
3. **Parses** the Lighthouse results into normalized issues
4. **Matches** each issue to specific HTML code locations
5. **Generates** a detailed report with line numbers

## 🚀 Quick Start

### Prerequisites

- Lighthouse service running on port 3002
- Python 3.8+ with required packages

### Run the Test

```bash
cd backend/app/utils
python3 test_lighthouse_parser.py
```

## 📊 Understanding the Output

### Console Summary

The tool shows a real-time summary:

```
🚀 Starting Lighthouse Parser + Matcher Test
============================================================
📄 Reading HTML file: test_seo_page.html
✅ HTML loaded (19113 characters)
🔄 Calling Lighthouse service...
✅ Lighthouse analysis completed! SEO Score: 54
🔄 Running LHR parser (normalize issues)...
✅ Parser completed! Normalized issues: 6
🔄 Running matcher to locate issues in HTML...
✅ Matcher completed! Located 6 / 6 issues
🔄 Generating detailed report with line numbers...
✅ Report saved to: lighthouse_parser_test_result_20250814_002213.json
```

### Key Metrics

- **SEO Score**: 0-100 (higher is better)
- **Total Issues**: Number of SEO problems found
- **Issues Located**: How many were successfully matched to HTML

## 📁 Where to Find Results

### 1. Console Output

The terminal shows a summary of each issue type:

```
Issue Types and Sample Locations:
  • canonical: 1 located
    [1] Lines 41-41 via matched
       HTML: <link rel="canonical" href="/relative-canonical">
  • image-alt: 2 located
    [1] Lines 144-144 via matched
       HTML: <img src="hero-5000x3000.jpg" loading="lazy" alt="">
```

### 2. Detailed JSON Report

**File Location**: `lighthouse_parser_test_result_YYYYMMDD_HHMMSS.json`

**What's Inside**:

- **Raw Lighthouse Data**: Complete audit results
- **Normalized Issues**: Parsed and structured SEO problems
- **HTML Matching**: Exact line numbers and code snippets
- **Match Status**: How each issue was located

### 3. Report File Structure

```json
{
  "lighthouse_data": {
    "seoScore": 54,
    "audits": { ... }
  },
  "normalized_issues": [
    {
      "audit_id": "image-alt",
      "title": "Images do not have alt attributes",
      "match_status": "matched",
      "match_line_start": 144,
      "match_line_end": 144,
      "match_html": "<img src=\"hero-5000x3000.jpg\" loading=\"lazy\" alt=\"\">"
    }
  ]
}
```

## 🔍 How to Use the Results

### Find Specific Issues

1. **Open the JSON report** in your editor
2. **Search for audit_id** (e.g., "image-alt", "canonical")
3. **Look at match_line_start/end** for exact line numbers
4. **Check match_html** for the problematic code

### Example: Fix Image Alt Issues

```json
{
  "audit_id": "image-alt",
  "match_line_start": 144,
  "match_html": "<img src=\"hero-5000x3000.jpg\" loading=\"lazy\" alt=\"\">"
}
```

**Go to line 144** in your HTML file and fix the empty `alt=""` attribute.

### Example: Fix Canonical URL

```json
{
  "audit_id": "canonical",
  "match_line_start": 41,
  "match_html": "<link rel=\"canonical\" href=\"/relative-canonical\">"
}
```

**Go to line 41** and fix the relative canonical URL.

## 🛠️ Customizing the Test

### Test Different HTML Files

Edit `test_lighthouse_parser.py`:

```python
# Change the HTML file path
html_file_path = "your_test_file.html"
```

### Test Different Lighthouse Service

```python
# Change the service URL
lighthouse_service_url = "http://localhost:3003"  # Different port
```

### Modify Output Format

The script saves reports with timestamps. You can modify the filename:

```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_filename = f"my_custom_report_{timestamp}.json"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "Connection refused" to Lighthouse

```bash
# Make sure Lighthouse service is running
cd ../../lighthouse-service
node server.js
```

#### 2. "No issues found" or "0 issues matched"

- Check if your HTML has actual SEO problems
- Verify Lighthouse service is working
- Look at the raw JSON for error messages

#### 3. "Issues found but not matched"

- Check the `match_status` field in the report
- Some issues might be impossible to match (e.g., missing elements)
- Look at the `match_html` field for clues

### Debug Mode

Add print statements to see what's happening:

```python
# In test_lighthouse_parser.py
print(f"Raw Lighthouse response: {lighthouse_response}")
print(f"Parsed issues: {normalized_issues}")
```

## 📈 Understanding Match Status

### `matched`

✅ **Successfully located** in HTML

- Has exact line numbers
- Shows the problematic code
- Ready for fixing

### `unmatched`

❌ **Could not locate** in HTML

- Missing from the page
- Impossible to match
- May need manual investigation

## 🎯 Best Practices

### 1. Start Small

- Test with simple HTML first
- Gradually add complexity
- Verify each issue type works

### 2. Check the Report

- Always review the JSON output
- Look for unexpected results
- Use line numbers to navigate

### 3. Iterate

- Fix issues in your HTML
- Re-run the test
- Verify improvements

## 🔄 Workflow Example

```bash
# 1. Run initial test
python3 test_lighthouse_parser.py

# 2. Check results in console
# 3. Open JSON report for details
# 4. Fix issues in your HTML file
# 5. Re-run test to verify fixes
python3 test_lighthouse_parser.py

# 6. Compare scores and issue counts
```

---

**Happy Testing! 🧪**

This tool helps you understand exactly where SEO problems are in your HTML code, making it easy to fix them systematically.
