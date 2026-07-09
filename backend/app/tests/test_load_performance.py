import time
import concurrent.futures
from fastapi.testclient import TestClient
from app.main import app

def simulate_user_request(user_id):
    client = TestClient(app)
    # 1. Register
    email = f"load_user_{user_id}@example.com"
    client.post(
        "/api/auth/register",
        json={"email": email, "password": "loadpassword", "full_name": f"Load User {user_id}", "role": "Site Engineer"}
    )
    
    # 2. Login & record response time
    start_time = time.time()
    resp = client.post("/api/auth/login", data={"username": email, "password": "loadpassword"})
    duration = time.time() - start_time
    
    status_code = resp.status_code
    success = (status_code == 200)
    
    return duration, success, status_code

def main():
    concurrency_level = 50
    print(f"Starting load performance test with {concurrency_level} concurrent requests...")

    durations = []
    successes = 0
    errors = 0
    status_codes = {}

    start_perf = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(simulate_user_request, i) for i in range(concurrency_level)]
        for fut in concurrent.futures.as_completed(futures):
            try:
                dur, ok, code = fut.result()
                durations.append(dur)
                if ok:
                    successes += 1
                else:
                    errors += 1
                status_codes[code] = status_codes.get(code, 0) + 1
            except Exception as e:
                errors += 1
                print(f"Thread execution failed: {e}")

    total_time = time.time() - start_perf
    throughput = concurrency_level / total_time if total_time > 0 else 0

    avg_latency = sum(durations) / len(durations) if durations else 0
    max_latency = max(durations) if durations else 0
    min_latency = min(durations) if durations else 0

    print("\n==================================================")
    print("           LOAD TESTING RESULTS SUMMARY           ")
    print("==================================================")
    print(f"Total Requests Executed:  {concurrency_level}")
    print(f"Successful Requests:      {successes}")
    print(f"Failed / Error Requests:  {errors}")
    print(f"Total Duration (Seconds): {total_time:.3f} s")
    print(f"Throughput:               {throughput:.2f} req/sec")
    print(f"Average Latency:          {avg_latency * 1000:.1f} ms")
    print(f"Min Latency:              {min_latency * 1000:.1f} ms")
    print(f"Max Latency:              {max_latency * 1000:.1f} ms")
    print(f"Status Code Breakdown:    {status_codes}")
    print("==================================================\n")

if __name__ == "__main__":
    main()
