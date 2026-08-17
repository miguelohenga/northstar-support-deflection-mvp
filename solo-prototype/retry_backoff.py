import time
import random

class WarehouseAPI:
    def __init__(self):
        self.attempt = 0

    def get_stock(self, product_id):
        self.attempt += 1
        if self.attempt <= 3:
            print(f"Attempt {self.attempt}: API failed (simulated error)")
            return None
        
        return {
            "product_id": product_id,
            "in_stock": True,
            "quantity": random.randint(5, 50)
        }

def sync_stock_with_retry(api_client, product_id, max_retries=5, base_delay=1, max_delay=30):
    for attempt in range(1, max_retries + 1):
        print(f"\nSync attempt {attempt} of {max_retries}...")

        result = api_client.get_stock(product_id)

        if result is not None:
            print(f"Stock synced successfully: {result}")
            return result

        if attempt < max_retries:
            raw_backoff = base_delay * (2 ** (attempt - 1))
            capped_backoff = min(raw_backoff, max_delay)
            delay = random.uniform(0, capped_backoff)
            
            print(f"Waiting {delay:.2f} seconds before retry (Capped Max Window: {capped_backoff}s)...")
            time.sleep(delay)

    print(f"\nFailed to sync stock after {max_retries} attempts.")
    return None

if __name__ == "__main__":
    print("Starting production-grade stock sync...\n")
    
    shared_api_client = WarehouseAPI()
    
    sync_stock_with_retry(api_client=shared_api_client, product_id="P001")
    print("\nSync process complete.")
