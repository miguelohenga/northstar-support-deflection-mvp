# sync_service_simple.py – Clean assignment submission format
# Implements: Threaded polling, exponential backoff with jitter, and an in-memory cache.

import time
import random
from datetime import datetime
import threading

# ==================== 1. SIMULATED WAREHOUSE API ====================
class WarehouseAPI:
    """
    Simulated warehouse API provided by the assignment specification.
    Maintains a sequential counter to simulate transient network errors.
    """
    def __init__(self):
        self.attempt = 0

    def get_stock(self, product_id):
        self.attempt += 1
        if self.attempt <= 3:
            print(f"[API] Attempt {self.attempt}: Failed (Simulated transient error)")
            return None
        return {
            "product_id": product_id,
            "in_stock": random.choice([True, False]),
            "quantity": random.randint(0, 100),
            "last_updated": datetime.now().isoformat()
        }

# ==================== 2. CACHE LAYER ====================
class StockCache:
    """
    Thread-safe memory store for holding the latest synchronized warehouse records.
    """
    def __init__(self):
        self.data = {}

    def update(self, product_id, stock_info):
        self.data[product_id.upper()] = stock_info
        print(f"[CACHE] Updated record for item: {product_id.upper()}")

    def get(self, product_id):
        return self.data.get(product_id.upper())

    def get_all(self):
        return self.data

# ==================== 3. RETRY / EXPONENTIAL BACKOFF LOGIC ====================
def fetch_with_retry(api_client, product_id, max_retries=5):
    """
    Executes API calls using an Exponential Backoff + Jitter algorithm.
    """
    for attempt in range(1, max_retries + 1):
        print(f"[SYNC] Execution attempt {attempt}/{max_retries} for {product_id}...")
        result = api_client.get_stock(product_id)
        
        if result is not None:
            print(f"[SYNC] Success achieved for {product_id}!")
            return result
            
        if attempt < max_retries:
            base_delay = 2 ** (attempt - 1)
            jitter = random.uniform(0, 1)
            total_delay = base_delay + jitter
            
            print(f"[SYNC] Request failed. Backing off for {total_delay:.2f} seconds...")
            time.sleep(total_delay)
            
    print(f"[SYNC] Critical failure: Max retries ({max_retries}) exhausted for {product_id}.")
    return None

# ==================== 4. POLLING LOOP PROCESS ====================
def polling_loop(api_client, cache, products, poll_interval=5):
    """
    Infinite worker loop designed to run inside a background thread.
    Periodically refreshes the memory cache based on the designated interval.
    """
    print(f"[POLL] Background worker initialized. Running every {poll_interval}s.")
    cycle = 0
    while True:
        cycle += 1
        print(f"\n[POLL] === Starting Synchronization Cycle #{cycle} ===")
        
        for pid in products:
            print(f"[POLL] Processing updates for: {pid}")
            data = fetch_with_retry(api_client, pid)
            
            if data:
                cache.update(pid, data)
            else:
                print(f"[POLL] Sync error on {pid}. Retaining existing cache snapshot.")
                
        print(f"[POLL] === Cycle #{cycle} complete. Worker sleeping for {poll_interval}s ===")
        time.sleep(poll_interval)

# ==================== 5. USER QUERY INTERFACE ====================
def query_interface(cache):
    """
    Command-line query interface tracking user request commands.
    """
    print("\n📊 Warehouse Inventory Query Interface Active")
    print("Available Commands: <product_id> (e.g., P001) | 'all' | 'exit'")
    
    while True:
        cmd = input("\nEnter your query command: ").strip()
        
        if not cmd:
            continue
            
        if cmd.lower() == "exit":
            print("Shutting down user query interface. Goodbye!")
            break
        elif cmd.lower() == "all":
            all_records = cache.get_all()
            if all_records:
                print("\n--- Current Cache Manifest ---")
                for pid, info in all_records.items():
                    print(f" {pid}: In-Stock={info['in_stock']}, Qty={info['quantity']} (Updated: {info['last_updated']})")
            else:
                print("[QUERY] Cache registry is currently empty. Waiting for background thread sync...")
        else:
            result = cache.get(cmd)
            if result:
                print(f"\n[QUERY] Found Match for {cmd.upper()}:")
                print(f" -> Stock Availability: {result['in_stock']}")
                print(f" -> Current Quantity  : {result['quantity']}")
                print(f" -> Timestamp Captured : {result['last_updated']}")
            else:
                print(f"[QUERY] Record error: Product '{cmd.upper()}' does not exist or hasn't cached yet.")

# ==================== 6. EXECUTION ENTRY POINT ====================
if __name__ == "__main__":
    print("🚀 Starting Stock Sync Service Framework (Assignment Distribution Spec)\n")
    
    # Initialize shared components
    assignment_api_client = WarehouseAPI()
    memory_cache = StockCache()
    
    # Configuration arrays
    assigned_products = ["P001", "P002", "P003", "P004", "P005"]
    POLL_FREQUENCY_SECONDS = 5

    # Spin up background thread for handling network syncs without blocking user CLI inputs
    poll_thread = threading.Thread(
        target=polling_loop,
        args=(assignment_api_client, memory_cache, assigned_products, POLL_FREQUENCY_SECONDS),
        daemon=True
    )
    poll_thread.start()

    # Launch user interactions
    query_interface(memory_cache)
