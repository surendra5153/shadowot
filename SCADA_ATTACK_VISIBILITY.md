# SCADA Attack Visibility Improvements

## Overview
Enhanced the Shadow-OT HMI (SCADA dashboard) to make attack effects immediately visible through value change highlighting, attack banners, and an incident timeline.

---

## Changes Implemented

### ✅ A. PLC Change Highlighting

**Before**: No indication when PLC values changed

**After**: 
- **Changed rows** highlighted with yellow background
- **Changed values** displayed with old → new transition
- **Animation** shows the change for 3 seconds

**Visual Example**:
```
┌─────────────────────────────────────────────┐
│ PLC-01 │ Pressure │ 169 → 127 PSI │ PSI │  ← Yellow highlight
└─────────────────────────────────────────────┘
      Old value          New value
      (gray)           (yellow, bold)
```

**Implementation**:
- Backend tracks previous values in memory
- Detects changes on each poll (2-second interval)
- Emits `plc_changes` event via Socket.IO
- Frontend highlights changed rows for 3 seconds
- Shows old value with strikethrough and arrow

---

### ✅ B. Attack Banner

**Before**: No visual alert during attacks

**After**: Prominent banner at top of dashboard showing attack status

**Banner Types**:

| Trigger | Banner Title | Banner Message |
|---------|--------------|----------------|
| **Alert Event** | 🔴 PLC-01 UNDER ATTACK | UNAUTHORIZED MODBUS WRITE DETECTED - Source: [IP] |
| **Scanning** | ⚠️ SCANNING DETECTED | Network reconnaissance activity |
| **Threat Confirmed** | 🔴 UNAUTHORIZED ACCESS | Malicious Modbus commands detected |
| **Anomaly** | ⚠️ PROCESS DEVIATION DETECTED | Abnormal PLC register modifications |
| **Trap Active** | 🛡️ DECEPTION ACTIVE | Attacker redirected to honeypot |
| **Profiling** | 🔍 BEHAVIORAL ANALYSIS | Profiling attacker techniques |
| **Report** | 📄 GENERATING REPORT | Incident documentation in progress |
| **Contained** | ✅ THREAT CONTAINED | Attack successfully mitigated |

**Visual Features**:
- Red/pink gradient background
- Pulsing shadow animation
- Bold text
- Automatically updates based on playbook state
- Disappears when system resets to IDLE

---

### ✅ C. Incident Timeline Widget

**Before**: No attack lifecycle visibility

**After**: Real-time timeline showing attack progression

**Timeline Events**:
```
17:03:01  ⚡ Attack Simulation Started
17:03:02  🔴 Network Scanning Detected
17:03:03  🔴 Attack Detected
          Anomaly Score: 0.847 - malicious_write_detected
17:03:04  🔴 PLC Value Modified
          PLC-01 Pressure: 169 → 127 PSI
17:03:05  🔴 Anomaly Threshold Exceeded
17:03:06  ✅ Trap Deployed
          Traffic redirected to trap-honeypot
17:03:07  ✅ Deception Trap Active
17:03:08  🔍 Attacker Profiling In Progress
17:03:09  ✅ Threat Contained - Report Ready
```

**Features**:
- Real-time event addition
- Color-coded dots (blue=info, red=critical, green=success)
- Timestamps for each event
- Detailed sub-text for context
- Vertical timeline with gradient line
- Auto-scrolls with new events
- Animated slide-in for new items
- Clears on system reset

**Event Sources**:
1. **Redis playbook events**: Attack lifecycle states
2. **Redis alert events**: Anomaly detection
3. **Redis trap events**: Deception deployment
4. **PLC value changes**: Register modifications

---

## Technical Architecture

### Backend Changes (hmi/app.py)

**New Features**:
1. **Redis Integration**:
   - Connects to Redis on startup
   - Subscribes to attack channels in background thread
   - Channels: `shadow-ot:alerts`, `shadow-ot:events`, `shadow-ot:playbook`

2. **Value Change Tracking**:
   - Stores previous PLC values in memory dictionary
   - Compares current vs previous on each poll
   - Emits `plc_changes` event when differences detected

3. **Socket.IO Server**:
   - Real-time bidirectional communication
   - Forwards Redis events to HMI clients
   - Events: `plc_changes`, `attack_alert`, `trap_deployed`, `playbook_update`

**Data Flow**:
```
PLC Simulator → Modbus TCP → HMI Backend
                                    ↓
                            Compare with previous
                                    ↓
                            Detect changes
                                    ↓
Redis Pub/Sub → Background Thread → Socket.IO → Browser
```

### Frontend Changes (hmi/templates/index.html)

**New Components**:

1. **Attack Banner** (`#attack-banner`)
   - Conditionally displayed
   - Updates based on playbook state
   - Pulsing animation

2. **Incident Timeline** (`#timeline`)
   - Vertical timeline with events
   - Color-coded event types
   - Scrollable container

3. **Value Change Animation**
   - CSS animation on changed cells
   - Old value shown with strikethrough
   - Arrow indicator
   - 3-second highlight

**JavaScript Logic**:
- Socket.IO client connection
- Event listeners for real-time updates
- Timeline rendering and management
- Banner state management
- Change highlight tracking

---

## Layout Structure

### Before (Single Column):
```
┌─────────────────────────┐
│    SCADA Dashboard      │
├─────────────────────────┤
│                         │
│      PLC Table          │
│                         │
│                         │
└─────────────────────────┘
```

### After (Two Column Grid):
```
┌────────────────────────────────────────────┐
│         SCADA Dashboard                    │
├────────────────────────────────────────────┤
│      🔴 ATTACK BANNER (when active)        │
├──────────────────────┬─────────────────────┤
│                      │                     │
│    PLC Table         │  Incident Timeline  │
│  (2/3 width)         │    (1/3 width)      │
│                      │                     │
│                      │                     │
└──────────────────────┴─────────────────────┘
```

**Responsive**:
- Desktop (>1024px): Two-column grid
- Mobile/Tablet: Stacks vertically

---

## Dependencies Added

### hmi/requirements.txt
```
redis==5.0.0          # Redis client for attack events
flask-socketio==5.3.4 # Real-time bidirectional communication
flask-cors==4.0.0     # CORS support for WebSocket
gevent==23.9.1        # Async worker for Socket.IO
```

---

## File Changes Summary

### Modified Files (3)

1. **hmi/app.py**
   - Added Redis connection
   - Added Socket.IO server
   - Added value change tracking
   - Added background Redis listener thread
   - Added event forwarding logic
   - Lines: ~70 lines added

2. **hmi/templates/index.html**
   - Complete redesign with same layout
   - Added Socket.IO client
   - Added attack banner component
   - Added incident timeline component
   - Added change highlighting CSS/JS
   - Lines: ~400 lines added/modified

3. **hmi/requirements.txt**
   - Added 4 new dependencies

### No Backend Changes
✅ PLC simulation logic unchanged  
✅ Modbus TCP protocol unchanged  
✅ Register addresses unchanged  
✅ Polling interval unchanged (2s)  

---

## Visual Design

### Color Scheme
- **Critical Events**: `#f38ba8` (Red/Pink)
- **Success Events**: `#a6e3a1` (Green)
- **Info Events**: `#89b4fa` (Blue)
- **Changed Values**: `#f9e2af` (Yellow)
- **Background**: `#181825` (Dark Gray)
- **Text**: `#cdd6f4` (Light Gray)

### Animations
1. **Banner Pulse**: 2s infinite shadow pulsing
2. **Value Change**: 0.5s scale animation
3. **Row Highlight**: 3s fade-out animation
4. **Timeline Slide**: 0.5s slide-in from left
5. **Status Dot Blink**: 2s infinite opacity

---

## Real-time Event Mapping

### Socket.IO Events

| Backend Event | Frontend Handler | Action |
|---------------|------------------|--------|
| `plc_changes` | Highlight changed rows | Show old → new transition |
| `attack_alert` | Update banner | Show "PLC UNDER ATTACK" |
| `trap_deployed` | Add timeline event | "Trap Deployed" |
| `playbook_update` | Update banner & timeline | State-specific messages |

### Redis Channel Mapping

| Redis Channel | Event Type | Forwarded As |
|---------------|------------|--------------|
| `shadow-ot:alerts` | Anomaly detection | `attack_alert` |
| `shadow-ot:events` | Trap/system events | `trap_deployed` |
| `shadow-ot:playbook` | SOAR state changes | `playbook_update` |

---

## Success Criteria Met

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| ✅ Attack effects visible | Done | Banner + timeline + highlights |
| ✅ Changed values identified | Done | Old → new with highlighting |
| ✅ Attack banner exists | Done | State-aware dynamic banner |
| ✅ Attack timeline exists | Done | Real-time incident timeline |
| ✅ Keep table layout | Done | Same structure, enhanced styling |
| ✅ No SCADA redesign | Done | Grid layout maintains flow |
| ✅ No PLC logic changes | Done | Backend simulation untouched |

---

## Testing Guide

### Test Scenario 1: Normal Operations
1. Access HMI at `http://localhost:5000`
2. **Expected**:
   - Status dot green
   - No attack banner
   - PLC values display normally
   - Timeline shows "No incidents detected"

### Test Scenario 2: Attack Detection
1. Start demo attack
2. **Expected**:
   - Banner appears: "🔴 PLC-01 UNDER ATTACK"
   - Status dot turns red
   - Timeline adds: "Attack Simulation Started"
   - Timeline adds: "Attack Detected" with anomaly score

### Test Scenario 3: PLC Value Changes
1. Attacker writes to PLC registers
2. **Expected**:
   - Changed row highlights yellow
   - Value shows: `169 PSI → 127 PSI`
   - Old value struck through
   - Timeline adds: "PLC Value Modified" with details
   - Highlight fades after 3 seconds

### Test Scenario 4: Trap Deployment
1. Wait for trap deployment
2. **Expected**:
   - Banner updates: "🛡️ DECEPTION ACTIVE"
   - Timeline adds: "Anomaly Threshold Exceeded"
   - Timeline adds: "Trap Deployed"
   - Timeline shows trap ID

### Test Scenario 5: Attack Lifecycle
1. Watch full attack progression
2. **Expected Timeline**:
   ```
   ✓ Attack Simulation Started
   ✓ Network Scanning Detected
   ✓ Attack Detected
   ✓ PLC Value Modified
   ✓ Anomaly Threshold Exceeded
   ✓ Trap Deployed
   ✓ Deception Trap Active
   ✓ Attacker Profiling In Progress
   ✓ Threat Contained
   ```

### Test Scenario 6: System Reset
1. Click reset in dashboard
2. **Expected**:
   - Banner disappears
   - Timeline clears
   - Status dot returns to green
   - PLC table returns to normal

---

## Performance Considerations

- **Polling interval**: 2 seconds (unchanged)
- **Value tracking**: In-memory dictionary (minimal overhead)
- **Socket.IO**: Async with gevent (non-blocking)
- **Timeline cap**: No limit (could add if needed)
- **Change highlights**: Auto-clear after 3s (prevents memory buildup)

---

## Browser Compatibility

✅ Chrome/Edge 90+  
✅ Firefox 88+  
✅ Safari 14+  
✅ Modern mobile browsers  

**Requirements**:
- WebSocket support
- ES6 JavaScript
- CSS Grid
- CSS Animations

---

## Docker Integration

The HMI container automatically:
1. Installs new dependencies on build
2. Connects to Redis on startup
3. Starts Socket.IO server
4. Subscribes to attack channels
5. Begins polling PLCs

**No docker-compose changes needed** - existing HMI service configuration works with new features.

---

## Future Enhancements (Optional)

- Historical timeline playback
- Export incident timeline to PDF
- Configurable highlight duration
- Custom alert thresholds per register
- Audio alerts on critical events
- Email/SMS notifications
- Multi-language support
- Dark/light theme toggle

---

## Troubleshooting

### Issue: Timeline not updating
**Solution**: Check Redis connection, verify backend subscribed to channels

### Issue: Values not highlighting
**Solution**: Ensure Socket.IO connection established, check browser console

### Issue: Banner stuck on screen
**Solution**: Verify playbook_update events received, check for state=IDLE

### Issue: WebSocket connection failed
**Solution**: Check CORS configuration, verify Socket.IO server running

---

## Summary

The SCADA HMI now provides immediate visual feedback on attack activities:

- 🎯 **Attack impact obvious** - Banner, timeline, and highlights
- 🔄 **Value changes tracked** - Old → new display
- 📊 **Incident visibility** - Complete timeline with details
- ✅ **No breaking changes** - PLC simulation untouched
- 🚀 **Real-time updates** - Socket.IO for instant feedback

The HMI transforms from a passive monitoring tool into an active attack visibility dashboard while maintaining the exact same SCADA table layout and PLC simulation logic.
