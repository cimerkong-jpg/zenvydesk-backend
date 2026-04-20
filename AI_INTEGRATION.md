# AI Content Generation Integration

**Version:** 1.0  
**Date:** April 20, 2026  
**Purpose:** Integration of BOT_PAPE AI content generation into backend

---

## Overview

Successfully integrated BOT_PAPE (AI content generation bot) into FastAPI backend using clean adapter pattern. Backend acts as orchestration layer between AI generation and Facebook posting.

---

## Architecture

### Clean Separation of Concerns

```
User Request
    ↓
Backend (Orchestration Layer)
    ├─→ AI Bot Adapter → BOT_PAPE (Content Generation)
    └─→ Facebook Service → Facebook API (Posting)
```

**Key Principles:**
- ✅ Backend orchestrates, doesn't mix logic
- ✅ AI adapter isolates BOT_PAPE integration
- ✅ Facebook service remains unchanged
- ✅ No tight coupling between components

---

## Files Created

### 1. `app/services/ai_bot_adapter.py`
**Purpose:** Bridge between backend and BOT_PAPE

**Key Features:**
- Automatic BOT_PAPE path resolution
- Dynamic module loading
- Error handling and fallback
- Singleton pattern for efficiency

**Methods:**
- `initialize()` - Find and load BOT_PAPE
- `generate_content()` - Generate AI content
- `is_available()` - Check BOT_PAPE status

### 2. `app/schemas/ai_content.py`
**Purpose:** Pydantic schemas for AI endpoints

**Schemas:**
- `AIGenerateRequest` - Input validation
- `AIGenerateResponse` - Output format

### 3. `app/routes/ai_content.py`
**Purpose:** API endpoints for AI content generation

**Endpoints:**
- `POST /ai/generate` - Generate content
- `GET /ai/status` - Check AI availability

---

## BOT_PAPE Integration Details

### BOT_PAPE Structure
**Location:** `C:/Users/Admin/Desktop/BOT_PAPE/fb-bot/`

**Key File:** `content_engine.py`

**Main Method:** `ContentEngine.generate_caption()`

**Input:**
- `content_type` - Type: morning/sale/evening
- `product` - Optional product context dict

**Output:**
- `caption` - Generated content text
- `topic` - Selected topic

**Dependencies:**
- OpenAI API (GPT-4)
- config_loader
- state_manager
- logger_setup

---

## Complete Flow

### Flow 1: AI-Assisted Posting

```
1. User Login
   POST /auth/facebook/login?session_id=xxx
   → User authenticates
   → Pages fetched automatically

2. Generate Content
   POST /ai/generate?session_id=xxx
   Body: {
     "prompt": "Promote smart home device",
     "content_type": "sale",
     "product_name": "Smart LED Bulb"
   }
   → Backend validates session
   → AI Adapter calls BOT_PAPE
   → BOT_PAPE generates content via OpenAI
   → Returns generated content to user

3. User Reviews/Edits
   (Frontend shows generated content)
   (User can edit before posting)

4. Post to Facebook
   POST /facebook/pages/post?session_id=xxx
   Body: {
     "message": "<edited_content>"
   }
   → Backend creates post_history (pending)
   → Calls Facebook API
   → Updates post_history (success/failed)
   → Returns result
```

### Flow 2: Manual Posting (Still Works)

```
User can skip AI generation and post directly:

POST /facebook/pages/post?session_id=xxx
Body: {
  "message": "Manual content"
}
```

---

## API Endpoints

### POST /ai/generate

Generate AI content using BOT_PAPE.

**Query Parameters:**
- `session_id` (required) - Session ID from login

**Request Body:**
```json
{
  "prompt": "Create post about smart home products",
  "content_type": "sale",
  "product_name": "Smart LED Bulb",
  "product_category": "Home Electronics",
  "product_description": "Energy-efficient smart bulb"
}
```

**Response (Success):**
```json
{
  "success": true,
  "content": "🏠 อยากให้บ้านของคุณฉลาดขึ้นไหม?\n\nหลอดไฟ LED อัจฉริยะ ควบคุมผ่านมือถือได้ทุกที่ทุกเวลา ปรับแสงได้ตามอารมณ์ ประหยัดไฟถึง 80%\n\nสนใจคอมเมนต์ หรือส่งข้อความมาได้เลยค่ะ 💡",
  "error": null,
  "metadata": {
    "content_type": "sale",
    "topic": "Smart Home Devices",
    "length": 156,
    "has_product_context": true,
    "generator": "BOT_PAPE/ContentEngine"
  }
}
```

**Response (Failure):**
```json
{
  "success": false,
  "content": null,
  "error": "AI Bot not available. Please check BOT_PAPE installation.",
  "metadata": null
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/ai/generate?session_id=test_123" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Promote smart LED bulb",
    "content_type": "sale",
    "product_name": "Smart LED Bulb"
  }'
```

---

### GET /ai/status

Check if AI service is available.

**Query Parameters:**
- `session_id` (required) - Session ID from login

**Response:**
```json
{
  "available": true,
  "service": "BOT_PAPE/ContentEngine",
  "status": "ready"
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/ai/status?session_id=test_123"
```

---

## Adapter Pattern Details

### Path Resolution

Adapter tries multiple locations to find BOT_PAPE:

1. Sibling folder: `../BOT_PAPE/fb-bot/`
2. Absolute path: `C:/Users/Admin/Desktop/BOT_PAPE/fb-bot/`
3. Alternative: `../../BOT_PAPE/fb-bot/`

### Module Loading

```python
# Add BOT_PAPE to Python path
sys.path.insert(0, str(bot_path))

# Import ContentEngine
from content_engine import ContentEngine

# Initialize
self.content_engine = ContentEngine()
```

### Error Handling

- ✅ BOT_PAPE not found → Returns error, doesn't crash
- ✅ Import fails → Logs error, returns unavailable
- ✅ Generation fails → Returns error message
- ✅ OpenAI API fails → BOT_PAPE handles internally

---

## Content Types

BOT_PAPE supports 3 content types:

### 1. Morning (morning)
- **Purpose:** Engagement, lifestyle tips
- **Tone:** Warm, friendly
- **Length:** 3-5 lines
- **No sales pitch**

### 2. Sale (sale)
- **Purpose:** Soft sell product promotion
- **Tone:** Friendly, not pushy
- **Length:** 4-6 lines
- **Highlights benefits**

### 3. Evening (evening)
- **Purpose:** Inspiration, relaxation
- **Tone:** Calm, cozy
- **Length:** 3-5 lines
- **No sales pitch**

---

## Product Context

Optional product information to make content more specific:

```json
{
  "product_name": "Smart LED Bulb",
  "product_category": "Home Electronics",
  "product_description": "Energy-efficient WiFi-enabled bulb",
  "product_selling_points": ["80% energy saving", "App control", "16M colors"]
}
```

BOT_PAPE uses this to:
- Mention product naturally
- Highlight specific benefits
- Create relevant content

---

## Logging

### AI Adapter Logs

```
INFO [AIBotAdapter] Found BOT_PAPE at: C:/Users/Admin/Desktop/BOT_PAPE/fb-bot
INFO [AIBotAdapter] Successfully initialized BOT_PAPE integration
INFO [AIBotAdapter] Generating content - type: sale, prompt_length: 35
INFO [AIBotAdapter] Successfully generated 156 characters
```

### Route Logs

```
INFO [AI Generate] User 1 requesting content - type: sale
INFO [AI Generate] Using product context: Smart LED Bulb
INFO [AI Generate] Success for user 1 - 156 chars
```

---

## Testing

### 1. Check AI Status

```bash
curl "http://localhost:8000/ai/status?session_id=test_123"
```

**Expected:** `"available": true`

### 2. Generate Content

```bash
curl -X POST "http://localhost:8000/ai/generate?session_id=test_123" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test prompt",
    "content_type": "sale"
  }'
```

**Expected:** Generated Thai content

### 3. Post Generated Content

```bash
# Copy generated content from step 2
curl -X POST "http://localhost:8000/facebook/pages/post?session_id=test_123" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "<paste_generated_content>"
  }'
```

**Expected:** Post published to Facebook

---

## Dependencies

### Backend Requirements
- FastAPI
- Pydantic
- SQLAlchemy
- (existing dependencies)

### BOT_PAPE Requirements
- OpenAI Python SDK
- config_loader
- state_manager
- logger_setup

**Note:** BOT_PAPE must have its own dependencies installed in its environment.

---

## Error Scenarios

### 1. BOT_PAPE Not Found

**Cause:** BOT_PAPE folder not at expected location

**Response:**
```json
{
  "success": false,
  "error": "AI Bot not available. Please check BOT_PAPE installation."
}
```

**Solution:** Verify BOT_PAPE location

### 2. Import Error

**Cause:** BOT_PAPE dependencies not installed

**Log:**
```
ERROR [AIBotAdapter] Failed to import BOT_PAPE modules: No module named 'openai'
```

**Solution:** Install BOT_PAPE dependencies

### 3. OpenAI API Error

**Cause:** Invalid API key or quota exceeded

**Handled by:** BOT_PAPE internally

**Response:**
```json
{
  "success": false,
  "error": "Failed to generate content. Please try again."
}
```

### 4. Session Expired

**Response:**
```json
{
  "detail": "Session has expired. Please login again"
}
```

**Solution:** Re-login

---

## Advantages of This Architecture

### 1. Clean Separation
- AI logic in BOT_PAPE
- Facebook logic in backend
- No mixing of concerns

### 2. Easy to Replace
- Can swap BOT_PAPE with another AI service
- Just update adapter
- Routes remain unchanged

### 3. Testable
- Can mock adapter for testing
- Can test Facebook posting independently
- Can test AI generation independently

### 4. Maintainable
- Each component has single responsibility
- Clear interfaces between components
- Easy to debug

### 5. Flexible
- User can use AI or manual content
- Can add more AI providers
- Can extend product context

---

## Future Enhancements

### Phase 6 (Potential)
1. **Multiple AI Providers**
   - Add Claude adapter
   - Add local model adapter
   - User chooses provider

2. **Content Templates**
   - Save successful prompts
   - Reuse templates
   - Template library

3. **A/B Testing**
   - Generate multiple versions
   - User picks best
   - Track performance

4. **Scheduled AI Posts**
   - Generate content in advance
   - Schedule for optimal times
   - Auto-post with approval

5. **Content Analytics**
   - Track AI vs manual performance
   - Optimize prompts
   - Learn from successful posts

---

## Risks & Mitigations

### Risk 1: BOT_PAPE Path Changes
**Mitigation:** Multiple path resolution strategies

### Risk 2: BOT_PAPE API Changes
**Mitigation:** Adapter isolates changes, easy to update

### Risk 3: OpenAI API Costs
**Mitigation:** User controls when to generate, no auto-generation

### Risk 4: Generated Content Quality
**Mitigation:** User reviews before posting, can edit

### Risk 5: BOT_PAPE Dependencies
**Mitigation:** Graceful degradation, manual posting still works

---

## Summary

**Status:** ✅ Complete and Operational

**Integration Points:**
- Backend ← Adapter → BOT_PAPE
- Backend → Facebook API (unchanged)
- Backend → Database (unchanged)

**New Endpoints:**
- POST /ai/generate
- GET /ai/status

**Reused Components:**
- Session handling
- Facebook posting
- Post history
- Logging

**Architecture:** Clean, maintainable, extensible

---

**Integration Complete:** April 20, 2026  
**Ready for:** Testing and production use
