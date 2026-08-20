# event_checkin_kiosk.py – Asynchronous Event Check-in Kiosk
# Day 4: The Pivot — Message Queue + Webhook Callback

import json
import time
import threading
import uuid
import random
import urllib.request
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8081

# ==================== IN-MEMORY DATABASE ====================
class AttendeeDatabase:
    """Stores attendee check-in status."""
    def __init__(self):
        self.attendees = {}
    
    def add_attendee(self, attendee_id, name, email):
        """Add a new attendee to the system."""
        self.attendees[attendee_id] = {
            "id": attendee_id,
            "name": name,
            "email": email,
            "checked_in": False,
            "print_requested": False,
            "print_status": "pending",
            "last_updated": datetime.now().isoformat()
        }
        print(f"[DB] Added attendee: {name} ({attendee_id})")
        return self.attendees[attendee_id]
    
    def get_attendee(self, attendee_id):
        """Get attendee by ID."""
        return self.attendees.get(attendee_id)
    
    def mark_print_requested(self, attendee_id):
        """Mark that a print request has been sent."""
        if attendee_id in self.attendees:
            self.attendees[attendee_id]["print_requested"] = True
            self.attendees[attendee_id]["print_status"] = "pending"
            self.attendees[attendee_id]["last_updated"] = datetime.now().isoformat()
            print(f"[DB] Print requested for: {self.attendees[attendee_id]['name']}")
            return True
        return False
    
    def mark_checked_in(self, attendee_id):
        """Mark attendee as checked in (called by webhook)."""
        if attendee_id in self.attendees:
            self.attendees[attendee_id]["checked_in"] = True
            self.attendees[attendee_id]["print_status"] = "completed"
            self.attendees[attendee_id]["last_updated"] = datetime.now().isoformat()
            print(f"[DB] ✅ Checked in: {self.attendees[attendee_id]['name']}")
            return True
        return False
    
    def is_checked_in(self, attendee_id):
        """Check if attendee is already checked in."""
        if attendee_id in self.attendees:
            return self.attendees[attendee_id]["checked_in"]
        return False

    def is_print_requested(self, attendee_id):
        """Check if printing is currently pending or processing."""
        if attendee_id in self.attendees:
            return self.attendees[attendee_id]["print_requested"]
        return False
    
    def get_all(self):
        """Get all attendees."""
        return self.attendees


# ==================== MESSAGE QUEUE (SIMULATED) ====================
class MessageQueue:
    """Simulated message queue for print requests."""
    def __init__(self):
        self.queue = []
        self.processed = []
    
    def publish(self, message):
        """Publish a message to the queue."""
        message_id = str(uuid.uuid4())
        message["message_id"] = message_id
        message["timestamp"] = datetime.now().isoformat()
        self.queue.append(message)
        print(f"[QUEUE] Published message {message_id} for {message.get('attendee_id')}")
        return message_id
    
    def process_next(self):
        """Process the next message in the queue (simulates vendor processing)."""
        if not self.queue:
            return None
        
        message = self.queue.pop(0)
        self.processed.append(message)
        print(f"[QUEUE] Processing message for {message.get('attendee_id')}")
        return message
    
    def get_pending_count(self):
        """Get number of pending messages."""
        return len(self.queue)


# ==================== GLOBAL INITIALIZATION ====================
db = AttendeeDatabase()
message_queue = MessageQueue()


# ==================== WEBHOOK HANDLER ====================
class WebhookHandler(BaseHTTPRequestHandler):
    """Handles webhook callbacks from the printer vendor."""
    
    def do_POST(self):
        """Receive webhook callback when print is complete."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            print(f"\n[WEBHOOK] Received callback: {data}")
            
            attendee_id = data.get('attendee_id')
            status = data.get('status')
            
            if not attendee_id or not status:
                self._send_response(400, {"error": "Missing attendee_id or status"})
                return
            
            if status == "completed":
                db.mark_checked_in(attendee_id)
                self._send_response(200, {"status": "success", "message": f"Checked in {attendee_id}"})
            elif status == "failed":
                print(f"[WEBHOOK] ❌ Print failed for {attendee_id}")
                self._send_response(200, {"status": "success", "message": "Failure recorded"})
            else:
                self._send_response(400, {"error": "Invalid status"})
                
        except json.JSONDecodeError:
            self._send_response(400, {"error": "Invalid JSON payload"})
        except Exception as e:
            print(f"[WEBHOOK] Error: {e}")
            self._send_response(500, {"error": "Internal server error"})
    
    def do_GET(self):
        """Health check endpoint."""
        if self.path == '/health':
            self._send_response(200, {"status": "healthy", "pending_count": message_queue.get_pending_count()})
        else:
            self._send_response(404, {"error": "Not found"})
    
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass


# ==================== CHECK-IN FUNCTION ====================
def process_check_in(attendee_id):
    """Process a check-in request."""
    attendee = db.get_attendee(attendee_id)
    
    if not attendee:
        print(f"[KIOSK] ❌ Attendee {attendee_id} not found")
        return {"success": False, "message": "Attendee not found"}
    
    if db.is_checked_in(attendee_id):
        print(f"[KIOSK] ⚠️ Attendee {attendee_id} already checked in.")
        return {"success": False, "message": "Already checked in"}
        
    if db.is_print_requested(attendee_id):
        print(f"[KIOSK] ⚠️ Print task processing for {attendee_id}. Request ignored.")
        return {"success": False, "message": "Print job already routing through queue."}
    
    db.mark_print_requested(attendee_id)
    
    message = {
        "attendee_id": attendee_id,
        "name": attendee["name"],
        "email": attendee["email"],
        "event": "print_request"
    }
    message_queue.publish(message)
    
    print(f"[KIOSK]  Print request sent for {attendee['name']}")
    return {
        "success": True,
        "status": "pending",
        "message": f"Print request sent for {attendee['name']}. Waiting for confirmation..."
    }


# ==================== MESSAGE QUEUE WORKER WITH RETRY / BACKOFF ====================
def execute_webhook_with_backoff(url, payload, max_retries=4):
    """Dispatches webhook callback using an exponential backoff with full jitter loop."""
    base_delay = 0.5
    max_delay = 4.0
    data = json.dumps(payload).encode('utf-8')
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url, data=data, 
                headers={'Content-Type': 'application/json'}, method='POST'
            )
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    print(f"[WEBHOOK CALLER] Successfully confirmed payload delivery for {payload['attendee_id']}.")
                    return True
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[WEBHOOK CALLER] ❌ Ultimate Delivery failure after {max_retries} attempts: {e}")
                return False
            
            calculated_delay = min(max_delay, base_delay * (2 ** attempt))
            sleep_time = random.uniform(0, calculated_delay)
            print(f"[WEBHOOK CALLER] Delivery failed. Retrying attempt #{attempt+2} in {sleep_time:.2f}s...")
            time.sleep(sleep_time)

def queue_worker():
    """
    Background worker that processes messages from the queue.
    Simulates the vendor processing print jobs and sending webhooks over HTTP.
    """
    print("[WORKER] Starting queue worker...")
    while True:
        message = message_queue.process_next()
        if message:
            print(f"[WORKER] 🖨️ Printing badge for {message.get('name')}...")
            time.sleep(1.5)
            
            success = True 
            
            callback_data = {
                "attendee_id": message.get('attendee_id'),
                "status": "completed" if success else "failed",
                "message": "Print job completed" if success else "Print job failed"
            }
            
            print(f"[WORKER] 📡 Sending webhook callback for {message.get('attendee_id')}: {callback_data['status']}")
            
            webhook_url = f"http://localhost:{PORT}/"
            execute_webhook_with_backoff(webhook_url, callback_data)


# ==================== QUERY INTERFACE ====================
def query_interface():
    """CLI for testing check-in."""
    print("\n  Event Check-in Kiosk")
    print("="*50)
    print("Commands:")
    print("  checkin <id>  - Process check-in for attendee")
    print("  status <id>   - Check attendee status")
    print("  all           - Show all attendees")
    print("  pending       - Show pending print jobs")
    print("  stats         - Show system statistics")
    print("  exit          - Quit\n")
    
    while True:
        try:
            cmd = input("Enter command: ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split()
            action = parts[0].lower()
            
            if action == "exit":
                print("Goodbye!")
                break
            
            elif action == "checkin" and len(parts) == 2:
                attendee_id = parts[1].upper()
                result = process_check_in(attendee_id)
                print(f"\nResult: {result}")
            
            elif action == "status" and len(parts) == 2:
                attendee_id = parts[1].upper()
                attendee = db.get_attendee(attendee_id)
                if attendee:
                    status = "✅ Checked In" if attendee.get('checked_in') else " Pending" if attendee.get('print_requested') else "  Not Checked In"
                    print(f"\n{attendee_id}: {attendee['name']}")
                    print(f"  Status: {status}")
                    print(f"  Print Status: {attendee.get('print_status', 'N/A')}")
                else:
                    print(f"Attendee {attendee_id} not found")
            
            elif action == "all":
                attendees = db.get_all()
                if attendees:
                    print("\n--- All Attendees ---")
                    for pid, info in attendees.items():
                        status = "✅ Checked In" if info.get('checked_in') else "  Pending" if info.get('print_requested') else "  Not Checked In"
                        print(f"{pid}: {info['name']} - {status}")
                else:
                    print("No attendees in system")
            
            elif action == "pending":
                count = message_queue.get_pending_count()
                print(f"\nPending print jobs: {count}")
            
            elif action == "stats":
                attendees = db.get_all()
                total = len(attendees)
                checked_in = sum(1 for a in attendees.values() if a.get('checked_in'))
                pending = sum(1 for a in attendees.values() if a.get('print_requested') and not a.get('checked_in'))
                print(f"\n📊 System Statistics")
                print(f"  Total attendees: {total}")
                print(f"  Checked in: {checked_in}")
                print(f"  Pending: {pending}")
                print(f"  Queue size: {message_queue.get_pending_count()}")
            
            else:
                print("Unknown command. Available: checkin <id>, status <id>, all, pending, stats, exit")
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

# ==================== MAIN ====================
if __name__ == "__main__":
    print("🚀 Starting Event Check-in Kiosk (Asynchronous Mode)")
    print("="*50)
    
    # Add sample attendees
    db.add_attendee("A001", "Alice Johnson", "alice@example.com")
    db.add_attendee("A002", "Bob Smith", "bob@example.com")
    db.add_attendee("A003", "Carol White", "carol@example.com")
    
    print("\n📋 Sample attendees loaded:")
    for pid, info in db.get_all().items():
        print(f"  {pid}: {info['name']} ({info['email']})")
    
    # Start queue worker in background thread
    worker_thread = threading.Thread(target=queue_worker, daemon=True)
    worker_thread.start()
    
    # Start webhook server in background thread
    server_thread = threading.Thread(
        target=lambda: HTTPServer(('', PORT), WebhookHandler).serve_forever(),
        daemon=True
    )
    server_thread.start()
    print(f"\n[WEBHOOK] Webhook receiver running on port {PORT}")
    print(f"[WEBHOOK] Endpoint: http://localhost:{PORT}/")
    
    # Run query interface
    query_interface()
