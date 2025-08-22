#!/usr/bin/env python3
"""
Test script for the optimize_v2 endpoint
Tests the full SEO optimization pipeline via HTTP requests
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:3001"
ENDPOINT = "/optimize_v2"
OUTPUT_DIR = Path("endpoint_test_outputs")

def create_output_dir():
    """Create output directory for test results"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")

def test_optimize_v2_endpoint():
    """Test the optimize_v2 endpoint with sample HTML"""
    
    print("=" * 80)
    print("🧪 Testing optimize_v2 Endpoint")
    print("=" * 80)
    
    # Sample HTML with SEO issues
    test_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title></title>
    <meta name="description" content="">
</head>
<body>
    <h1>Sample Page for SEO Testing</h1>
    <p>This page has several SEO issues that need to be optimized:</p>
    
    <ul>
        <li>Empty title tag</li>
        <li>Empty meta description</li>
        <li>Images without alt attributes</li>
        <li>Missing structured data</li>
    </ul>
    
    <!-- Images with missing or empty alt attributes -->
    <img src="https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=400" alt="">
    <img src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400">
    <img src="https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=400" alt=" ">
    
    <h2>Content Section</h2>
    <p>More content here that could benefit from optimization.</p>
    
    <div>
        <img src="https://images.unsplash.com/photo-1592002785005-bf7fb3b8b89d?w=400">
    </div>
</body>
</html>"""
    
    # Prepare the request
    url = f"{BASE_URL}{ENDPOINT}"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "html": test_html
    }
    
    print(f"🌐 Sending request to: {url}")
    print(f"📄 HTML length: {len(test_html)} characters")
    print(f"🔍 Images in HTML: {test_html.count('<img')}")
    
    try:
        # Send the request
        print("\n⏳ Sending POST request...")
        start_time = time.time()
        
        response = requests.post(url, headers=headers, json=payload, timeout=300)  # 5 minute timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Request completed in {duration:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            
            # Save the full response
            with open(OUTPUT_DIR / "optimize_v2_response.json", "w") as f:
                json.dump(result, f, indent=2)
            print(f"💾 Full response saved to: optimize_v2_response.json")
            
            # Save the modified HTML if present
            if result.get("modified_html"):
                with open(OUTPUT_DIR / "optimized.html", "w") as f:
                    f.write(result["modified_html"])
                print(f"💾 Optimized HTML saved to: optimized.html")
            
            # Print summary
            print("\n" + "="*60)
            print("📋 OPTIMIZATION SUMMARY")
            print("="*60)
            
            if result.get("success"):
                print("✅ Status: SUCCESS")
                print(f"🔢 Original SEO Score: {result.get('original_seo_score', 'N/A')}")
                print(f"🔢 Optimized SEO Score: {result.get('optimized_seo_score', 'N/A')}")
                print(f"🔧 Issues Processed: {result.get('issues_processed', 'N/A')}")
                print(f"📏 Original HTML Length: {len(test_html)}")
                print(f"📏 Optimized HTML Length: {len(result.get('modified_html', ''))}")
                
                # Pipeline steps
                if result.get("pipeline_steps"):
                    print(f"\n🚀 Pipeline Steps Completed:")
                    for i, step in enumerate(result["pipeline_steps"], 1):
                        print(f"   {i}. {step}")
                
                # Issues found
                if result.get("optimization_result", {}).get("issues"):
                    issues = result["optimization_result"]["issues"]
                    print(f"\n🔍 Issues Found and Fixed: {len(issues)}")
                    for i, issue in enumerate(issues[:5], 1):  # Show first 5 issues
                        print(f"   {i}. {issue.get('issue', 'Unknown issue')}")
                    if len(issues) > 5:
                        print(f"   ... and {len(issues) - 5} more issues")
                
                return True
                
            else:
                print("❌ Status: FAILED")
                print(f"🚨 Error: {result.get('error', 'Unknown error')}")
                print(f"📍 Step: {result.get('step', 'Unknown step')}")
                return False
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"🚨 Error Details: {error_data}")
            except:
                print(f"🚨 Response Text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (5 minutes)")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - Is the server running?")
        print(f"💡 Make sure to start the server with: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"🚨 Unexpected error: {str(e)}")
        return False

def test_endpoint_with_minimal_html():
    """Test with minimal HTML to check basic functionality"""
    
    print("\n" + "=" * 80)
    print("🧪 Testing optimize_v2 with Minimal HTML")
    print("=" * 80)
    
    minimal_html = """<!DOCTYPE html>
<html>
<head><title></title></head>
<body><h1>Test</h1><img src="https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=300"></body>
</html>"""
    
    url = f"{BASE_URL}{ENDPOINT}"
    payload = {"html": minimal_html}
    
    try:
        print("⏳ Sending minimal HTML test...")
        response = requests.post(url, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            # Save minimal test result
            with open(OUTPUT_DIR / "minimal_test_response.json", "w") as f:
                json.dump(result, f, indent=2)
            
            if result.get("success"):
                print("✅ Minimal HTML test: SUCCESS")
                print(f"🔧 Issues found: {result.get('issues_processed', 0)}")
                return True
            else:
                print("❌ Minimal HTML test: FAILED")
                print(f"🚨 Error: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"🚨 Minimal test error: {str(e)}")
        return False

def test_server_connection():
    """Test if the server is running and accessible"""
    
    print("🔌 Testing server connection...")
    
    try:
        # Test a simple endpoint first
        response = requests.get(f"{BASE_URL}/test", timeout=10)
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"⚠️ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("💡 Start the server with: cd backend && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 Starting optimize_v2 Endpoint Tests")
    print(f"🎯 Target URL: {BASE_URL}{ENDPOINT}")
    print(f"⏰ Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create output directory
    create_output_dir()
    
    # Test server connection
    if not test_server_connection():
        print("\n❌ Cannot proceed - server is not accessible")
        return
    
    # Run tests
    test1_success = test_optimize_v2_endpoint()
    test2_success = test_endpoint_with_minimal_html()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    if test1_success and test2_success:
        print("🎉 All tests PASSED!")
        print("✅ optimize_v2 endpoint is working correctly")
    else:
        print("⚠️ Some tests FAILED")
        if not test1_success:
            print("❌ Main optimization test failed")
        if not test2_success:
            print("❌ Minimal HTML test failed")
    
    print(f"\n📁 Check '{OUTPUT_DIR}' folder for detailed results")

if __name__ == "__main__":
    main()
