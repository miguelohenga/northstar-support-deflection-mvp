  Scope Delta Analysis – The Meridian Pivot

 Client: Solstice Events Co. 
 Date: 2026-08-20 
 Prepared by: Miguel Ohenga 
 Sprint:  Week 2 – The Meridian Pivot 



  1. Executive Summary

This document captures the impact of the Day 4 pivot, where the synchronous check-in system was refactored to an asynchronous message queue + webhook model.

 Original Spec: Synchronous printer API call → wait for response → show "Checked In" 
 New Spec: Publish print request to queue → show "Pending" → webhook confirms → show "Checked In"



 2. What Changed

| Aspect | Original Spec (Synchronous) | New Spec (Asynchronous) |
|--------|----------------------------|-------------------------|
| Print request | Direct API call | Published to message queue |
| Response | Immediate | Delayed (webhook callback) |
| UI status | "Checked In" instantly | "Pending" → "Checked In" |
| Error handling | Immediate failure | Retry with backoff |
| Duplicate protection | Simple check | Idempotency checks |



 3. What Was Dropped, Modified, or Added

| Type | Item | Details |
|------|------|---------|
| Dropped | Synchronous printer API call | No longer used |
| Modified | Check-in logic | Now publishes to queue instead of calling API |
| Modified | UI status | Added "Pending" state |
| Added | Message queue | Handles print request queuing |
| Added | Webhook receiver | Listens for print completion callbacks |
| Added | Webhook retry with backoff | Ensures reliable delivery 
| Added | `is_print_requested()` check | Prevents duplicate queue entries |



  4. The Cost of the Pivot

| Cost Type | Impact |
|-----------|--------|
| Time lost | 2 hours (refactoring + testing) |
| Code rewritten | ~50 lines removed, ~250 lines added |
| Risk introduced | Webhook receiver must be running; pending states must be handled |
| Scope reduction | None — all original features retained |



  5. Regression Check

| Test Case | Before Pivot (Sync) | After Pivot (Async) | Status |
|-----------|---------------------|---------------------|--------|
| Check-in for valid attendee |  Passed |  Passed | No regression |
| Duplicate scan prevention |  Passed |  Passed | No regression |
| Error handling |  Passed |  Passed | No regression |
| Attendee status tracking |  Passed |  Passed | No regression |



  6. What Was Deprioritised

| Item | Reason |
|------|--------|
| Persistent storage | In-memory database used for simplicity — acceptable for MVP |
| Authentication | Not required for MVP scope |
| Real printer integration | Simulated for prototype |

 

   7. Lessons Learned

 What worked well:**
- The modular design (database, queue, webhook, UI) made the pivot manageable
- Retry/backoff logic from Assignment 1 was reusable
- Webhooks enable real-time updates without polling

 What was challenging:**
- Understanding the asynchronous flow (pending states, callbacks)
- Testing webhooks locally required multiple windows

 What I would do differently:**
- Start with an async design from Day 1
- Add persistent storage for the database



  8. Final Status

| Criterion | Status |
|-----------|--------|
| New spec implemented |  Complete |
| Obsolete code deprecated |  Marked in `sync_service_simple.py` |
| Regression tests passed |  All tests pass |
| Scope Delta Analysis |  Complete |

 Ready for submission
 
