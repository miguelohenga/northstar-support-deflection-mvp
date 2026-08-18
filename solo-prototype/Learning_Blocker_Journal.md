
 Day 1–2: Learning & Blocker Journal

Tool Assigned:[Retry/Backoff Logic]
 Date: [17th Aug]]


Hour 1 – Initial Research
- Key concepts discovered:*Retry logic repeats a failed opertion until it suceeds
                          *Exponetial backoff-Doubkes waiting time after each failure
                          *Jitter Adds randomness to prevent everyone retrying at the sametime
- Questions I have:What's the best way to add jitter?
- Resources I found useful:https://youtu.be/WhcBBdKjyIY?si=4RGNtVekjBJnM-Hq
                                 https://tenacity.readthedocs.io/en/latest/


 Mini-Prototype Status (End of Day 2)
Assignment 1 – Final Submission
  What I Built

A retry/backoff logic prototype for a stock syncing service.

  How It Works
1. **Simulated API**: The `WarehouseAPI` class mimics a real warehouse API that fails the first 3 times.
2. **Exponential Backoff**: Each retry waits longer than the previous one.
3. **Capped Backoff**: Max wait time is capped at 30 seconds.
4. **Jitter**: Random delay is added to prevent collisions.

   Code Features
- ✅ Simulated warehouse API (fails first 3 times, succeeds on 4th)
- ✅ Exponential backoff (doubles wait time each attempt)
- ✅ Capped backoff (max 30 seconds)
- ✅ Jitter (random delay to spread out retries)
- ✅ Clear logging (shows each step)

  What I Learned
- Retry/backoff is a critical pattern for building reliable systems.
- Jitter prevents the "thundering herd" problem.
- Exponential backoff helps services recover from failures gracefully.

  Files Submitted
- `solo-prototype/retry_backoff.py` – Python script
- `solo-prototype/Learning_Blocker_Journal.md` – This journal

 GitHub Link
https://github.com/miguelohenga/northstar-support-deflection-mvp/tree/feature/solo-recon/solo-prototype

  Status
✅ Assignment 1 Complete

  Day 3 – Original Build Complete

  What I Built
A stock syncing service that:
- ✅ Polls a warehouse API every 5 seconds (simulated)
- ✅ Caches stock data in memory
- ✅ Exposes a query interface for users
- ✅ Uses exponential backoff + jitter for retries
- ✅ Runs polling in a background thread

 Testing Results
- ✅ Polling loop runs every 5 seconds
- ✅ API fails first 3 times, succeeds on 4th
- ✅ Cache updates correctly
- ✅ Query interface returns correct data
- ✅ All commands work as expected

 Status
✅ Day 3 Complete — Ready for Day 4 (The Pivot)
