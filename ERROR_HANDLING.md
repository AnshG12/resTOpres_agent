# NVIDIA API Error Handling & Retry Logic

## ✅ Implemented Features

### 1. **Exponential Backoff for Rate Limiting (429)**
When the API returns "Too Many Requests" (429), the system automatically:
- **Attempt 1:** Wait 5 seconds
- **Attempt 2:** Wait 10 seconds
- **Attempt 3:** Wait 20 seconds
- **Attempt 4:** Wait 40 seconds
- **Attempt 5:** Wait 80 seconds

This prevents hammering the API and respects rate limits.

### 2. **Timeout Handling (DeepSeek Thinking Time)**
- **Default timeout:** 300 seconds (5 minutes)
- DeepSeek-V3.2 has long "thinking time" for complex queries
- Previously: 120s timeout (2 minutes) - **too short**
- Now: 300s timeout with automatic retry if still times out

### 3. **Connection Error Recovery**
Handles network issues:
- `httpx.ConnectError` - Network connection failures
- `httpx.RemoteProtocolError` - Protocol errors
- `httpx.TimeoutException` - Read operation timeouts

Each automatically retries with 10s delay.

### 4. **Polite Request Delay**
- **2 second delay** between successful requests
- Prevents hitting rate limits in the first place
- Only delays if requests are made faster than 2s apart

### 5. **Server Error Handling (5xx)**
- Retries on 500, 502, 503, 504 errors
- Waits 5s before retry
- Common during API maintenance or overload

---

## 📊 Error Handling Flow

```
User Request
    ↓
Check last request time
    ↓ (wait if < 2s)
Polite Delay (2s)
    ↓
Attempt 1
    ↓
[Success] → Return Result
[429 Rate Limit] → Wait 5s → Attempt 2
[Timeout] → Wait 10s → Attempt 2
[Connection Error] → Wait 10s → Attempt 2
[5xx Server Error] → Wait 5s → Attempt 2
    ↓
Attempt 2
    ↓
[Success] → Return Result
[429] → Wait 10s → Attempt 3
[Timeout] → Wait 10s → Attempt 3
    ↓
...continues up to 5 attempts...
    ↓
[All failed] → Raise RuntimeError
```

---

## 🛠️ Configuration Options

In `src/agent/nvidia_client.py`:

```python
client = NvidiaClient(
    api_key="your_key",
    timeout_s=300.0,        # 5 min timeout for DeepSeek thinking
    max_retries=5,          # Max retry attempts
    base_retry_delay=5.0,   # Base exponential backoff delay
    request_delay=2.0,      # Polite delay between requests
)
```

**Adjust these if needed:**
- **Faster presentation generation:** `request_delay=1.0` (1 second delay)
- **More patient with timeouts:** `timeout_s=600.0` (10 minutes)
- **More aggressive retries:** `max_retries=10`

---

## 📝 Example Error Logs

### Rate Limit (429):
```
📡 Sending chat completion (Attempt 1/5)...
⚠️  Rate limit hit (429). Waiting 5.0s before retry...
📡 Sending chat completion (Attempt 2/5)...
✓ Success!
```

### Timeout Recovery:
```
📡 Sending multimodal generation (Attempt 1/5)...
⚠️  Timeout error. Retrying in 10.0s...
📡 Sending multimodal generation (Attempt 2/5)...
✓ Success!
```

### Connection Error:
```
📡 Sending chat completion (Attempt 1/5)...
⚠️  Connection error: [Errno 61] Connection refused. Retrying in 10.0s...
📡 Sending chat completion (Attempt 2/5)...
✓ Success!
```

---

## 🔧 How It Works in Your Code

**Before (no error handling):**
```python
response = client.chat(model=model, messages=messages)
# ❌ Crashes on timeout or rate limit
```

**After (automatic retry):**
```python
response = client.chat(model=model, messages=messages)
# ✅ Automatically retries with exponential backoff
# ✅ Polite delays between requests
# ✅ Handles timeouts gracefully
```

**No code changes needed!** All retry logic is handled internally by `NvidiaClient`.

---

## 🎯 What This Fixes

### Problem 1: "Read operation timed out"
- **Before:** Crash after 120s
- **After:** 300s timeout + automatic retry

### Problem 2: "429 Too Many Requests"
- **Before:** Crash immediately
- **After:** Exponential backoff (5s, 10s, 20s, 40s, 80s)

### Problem 3: Network hiccups
- **Before:** Crash on connection error
- **After:** Retry with 10s delay

### Problem 4: Hitting rate limits
- **Before:** No delay between requests → instant 429
- **After:** 2s polite delay → smooth operation

---

## 📌 Default Behavior

With NVIDIA API configured, your presentations now:
1. ✅ Wait 2 seconds between API calls (polite)
2. ✅ Automatically retry on rate limits (exponential backoff)
3. ✅ Handle 5-minute thinking time (DeepSeek)
4. ✅ Recover from network errors (3 attempts)
5. ✅ Provide clear error messages in logs

**You don't need to change anything!** Just run:
```bash
uv run python -m src.agent.cli make-presentation arXiv-2602.04843v1 --yes
```

The system now handles errors gracefully instead of crashing.

---

## 🚀 Performance Impact

**Generation time:**
- Text-only: ~30-60s (unchanged)
- With figures (multimodal): ~60-120s (unchanged)
- With retries: +10-80s (only if errors occur)
- Polite delay: +2s per section (prevents rate limits)

**Trade-off:**
- Slightly slower (2s per section)
- But MUCH more reliable (no crashes)

---

## ⚙️ Advanced: Disable Polite Delay

If you want faster generation and are confident about rate limits:

Edit `src/agent/presentation_agent.py`:

```python
self.nvidia_client = NvidiaClient(
    settings.nvidia_api_key,
    base_url=settings.nvidia_base_url,
    request_delay=0.0,  # No delay (risky!)
)
```

**Not recommended** unless you have high API limits.
