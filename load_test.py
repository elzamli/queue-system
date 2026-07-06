#!/usr/bin/env python3
"""
Queue System Load Test
בודק 20 בקשות במקביל על Render Server
"""

import requests
import threading
import time
import json
from collections import defaultdict
from datetime import datetime

# ===== הגדרות =====
BASE_URL = "https://queue-system-qw88.onrender.com"
BASE_URL = "http://127.0.0.1:5000/"
CONCURRENT_REQUESTS = 20
ITERATIONS = 5  # כמה rounds של 20 בקשות

# ===== נתונים גלובליים לתוצאות =====
results = []
errors = []
lock = threading.Lock()

# ===== סוגי בקשות לבדיקה =====
test_scenarios = [
    {
        "name": "Add Customer",
        "method": "POST",
        "url": "/api/add-entry",
        "data": lambda i: {
            "station_id": (i % 10) + 1,
            "customer_number": 10000 + i,
            "transfer": False
        }
    },
    {
        "name": "Search Customer",
        "method": "GET",
        "url": "/api/search-customer?number=100",
        "data": None
    },
    {
        "name": "Center Data",
        "method": "GET",
        "url": "/api/center-data",
        "data": None
    },
    {
        "name": "Call Next",
        "method": "POST",
        "url": "/api/call-next/1",
        "data": lambda i: {
            "operator_code": "1001"
        }
    }
]

# ===== פונקציות =====
def make_request(scenario, request_id, iteration):
    """עשה בקשה אחת"""
    try:
        start_time = time.time()
        
        url = BASE_URL + scenario["url"]
        
        if scenario["method"] == "GET":
            response = requests.get(url, timeout=30)
        else:
            # שנה את ה-data ל-include את iteration!
            if scenario["name"] == "Add Customer":
                data = {
                    "station_id": (request_id % 10) +1,
                    "customer_number": 10000 + (iteration * 100) + request_id,  # ← unique!
                    "transfer": False
                }
            else:
                data = scenario["data"](request_id) if scenario["data"] else {}
            
            response = requests.post(url, json=data, timeout=30)

        elapsed = time.time() - start_time
        
        result = {
            "scenario": scenario["name"],
            "request_id": request_id,
            "iteration": iteration,
            "status_code": response.status_code,
            "elapsed_time": elapsed,
            "timestamp": datetime.now().isoformat(),
            "success": 200 <= response.status_code < 300
        }
        
        with lock:
            results.append(result)
        
        return True
    
    except Exception as e:
        error = {
            "scenario": scenario["name"],
            "request_id": request_id,
            "iteration": iteration,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        with lock:
            errors.append(error)
        
        return False


def run_concurrent_requests(scenario, iteration):
    """הרץ 20 בקשות במקביל"""
    threads = []
    
    print(f"\n⏳ Starting iteration {iteration + 1}/{ITERATIONS} - {scenario['name']}")
    print(f"   Sending {CONCURRENT_REQUESTS} concurrent requests...")
    
    start_batch = time.time()
    
    for i in range(CONCURRENT_REQUESTS):
        thread = threading.Thread(
            target=make_request,
            args=(scenario, i, iteration)
        )
        threads.append(thread)
        thread.start()
    
    # חכה שכל ה-threads יסתיימו
    for thread in threads:
        thread.join()
    
    batch_time = time.time() - start_batch
    print(f"   ✅ Completed in {batch_time:.2f} seconds")


def print_results():
    """הדפס תוצאות סופיות"""
    
    print("\n" + "="*80)
    print("📊 LOAD TEST RESULTS - תוצאות בדיקת עומס")
    print("="*80)
    
    if not results:
        print("❌ No successful requests!")
        return
    
    # סטטיסטיקה כללית
    print(f"\n📈 סטטיסטיקה כללית:")
    print(f"   סה\"כ בקשות: {len(results)}")
    print(f"   בקשות בהצלחה: {sum(1 for r in results if r['success'])}")
    print(f"   בקשות בכישלון: {sum(1 for r in results if not r['success'])}")
    print(f"   שגיאות: {len(errors)}")
    
    # זמנים
    times = [r['elapsed_time'] for r in results]
    min_time = min(times)
    max_time = max(times)
    avg_time = sum(times) / len(times)
    
    print(f"\n⏱️  זמני תגובה:")
    print(f"   מהיר ביותר: {min_time:.3f}s")
    print(f"   איטי ביותר: {max_time:.3f}s")
    print(f"   ממוצע: {avg_time:.3f}s")
    
    # לפי סצנריו
    print(f"\n🎯 תוצאות לפי סצנריו:")
    scenarios_data = defaultdict(list)
    for r in results:
        scenarios_data[r['scenario']].append(r)
    
    for scenario_name, scenario_results in scenarios_data.items():
        times = [r['elapsed_time'] for r in scenario_results]
        success_count = sum(1 for r in scenario_results if r['success'])
        
        print(f"\n   {scenario_name}:")
        print(f"      סה\"כ: {len(scenario_results)}")
        print(f"      בהצלחה: {success_count}")
        print(f"      ממוצע זמן: {sum(times)/len(times):.3f}s")
        print(f"      טווח: {min(times):.3f}s - {max(times):.3f}s")
    
    # שגיאות
    if errors:
        print(f"\n❌ שגיאות ({len(errors)}):")
        for error in errors[:5]:  # הראה רק 5 ראשונים
            print(f"   {error['scenario']}: {error['error']}")
        if len(errors) > 5:
            print(f"   ... ו-{len(errors) - 5} שגיאות נוספות")
    
    # הערכה
    print(f"\n📋 הערכה:")
    avg_time_percent = (avg_time / 5.0) * 100
    
    if avg_time < 1:
        print(f"   ✅ EXCELLENT - avg {avg_time:.3f}s")
    elif avg_time < 3:
        print(f"   ✅ GOOD - avg {avg_time:.3f}s")
    elif avg_time < 5:
        print(f"   ⚠️  ACCEPTABLE - avg {avg_time:.3f}s")
    else:
        print(f"   ❌ SLOW - avg {avg_time:.3f}s")
    
    if len(errors) == 0:
        print(f"   ✅ No errors!")
    else:
        error_rate = (len(errors) / (len(results) + len(errors))) * 100
        print(f"   ❌ Error rate: {error_rate:.1f}%")
    
    print("\n" + "="*80)
    
    # שמור לקובץ
    save_results_to_file()


def save_results_to_file():
    """שמור תוצאות לקובץ JSON"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "concurrent_requests": CONCURRENT_REQUESTS,
        "iterations": ITERATIONS,
        "results": results,
        "errors": errors,
        "summary": {
            "total_requests": len(results),
            "successful": sum(1 for r in results if r['success']),
            "failed": sum(1 for r in results if not r['success']),
            "errors": len(errors),
            "avg_time": sum(r['elapsed_time'] for r in results) / len(results) if results else 0,
            "min_time": min((r['elapsed_time'] for r in results), default=0),
            "max_time": max((r['elapsed_time'] for r in results), default=0)
        }
    }
    
    filename = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")


def main():
    """הרץ את כל הטסטים"""
    
    print("\n" + "="*80)
    print("🚀 QUEUE SYSTEM LOAD TEST")
    print("="*80)
    print(f"🎯 Target: {BASE_URL}")
    print(f"👥 Concurrent Requests: {CONCURRENT_REQUESTS}")
    print(f"🔄 Iterations: {ITERATIONS}")
    print(f"⏱️  Start Time: {datetime.now().isoformat()}")
    
    try:
        # בדוק שהשרת accessible
        print("\n📡 Checking server connectivity...")
        response = requests.get(BASE_URL + "/center", timeout=10)
        if response.status_code == 200:
            print("   ✅ Server is reachable!")
        else:
            print(f"   ⚠️  Server responded with {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Cannot reach server: {e}")
        return
    
    # הרץ טסטים
    for iteration in range(ITERATIONS):
        for scenario in test_scenarios:
            run_concurrent_requests(scenario, iteration)
            time.sleep(1)  # pause בין scenarios
    
    # הדפס תוצאות
    print_results()


if __name__ == "__main__":
    main()