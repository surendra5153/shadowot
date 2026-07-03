# Monitoring Page Improvements

## Summary
Enhanced the monitoring page to display realistic attack activity with live event streams, detailed packet information, and intelligent traffic patterns.

---

## Changes Made

### ✅ 1. Live Event Stream

**Before:**
```
No events to display
```

**After:**
Dynamic event stream showing attack lifecycle:

```
[17:03:01] • Attack simulation started
[17:03:02] ⚠️ Network scanning activity detected
[17:03:03] 🔴 Unauthorized Modbus write detected
[17:03:04] ⚠️ PLC register modification attempt
[17:03:05] ⚠️ Anomaly threshold exceeded
[17:03:06] ✓ Deception trap deployed
[17:03:07] ✓ Malicious traffic redirected to honeypot
[17:03:08] • Behavioral profiling in progress
[17:03:09] ✓ Threat contained - report generated
```

**Features:**
- Synthesized lifecycle events based on playbook state transitions
- Merged with real backend events from Redis
- Color-coded by severity:
  - 🔴 **Critical** (red): Unauthorized access, anomalies
  - ⚠️ **Warning** (yellow): Suspicious activity, scanning
  - ✓ **Success** (green): Trap deployment, containment
  - • **Info** (slate): General events
- Auto-scrolls to latest events
- Shows last 50 events
- Animated entry transitions
- Real-time status indicator

---

### ✅ 2. Packet Stream Widget

**Before:**
Generic event log with limited detail

**After:**
Detailed packet-level information:

```
┌─────────────────────────────────────┐
│ 17:03:03                   ANOMALY  │
│                                     │
│ Src: 10.5.0.100                    │
│ Dst: PLC-01                        │
│ Protocol: Modbus TCP               │
│ Function: Write Multiple Registers │
│ Register: Pressure                 │
│ Score: 0.847                       │
└─────────────────────────────────────┘
```

**Features:**
- Shows source/destination IPs
- Protocol identification (Modbus TCP)
- Function code decoded to human-readable names:
  - Read Coils, Read Holding Registers
  - Write Single Register, Write Multiple Registers
  - Read/Write Multiple Registers
- Register address mapped to process variables:
  - 1000-1100: Pressure
  - 2000-2100: Temperature
  - 3000-3100: Flow Rate
  - 4000-4100: Valve Control
- Anomaly score displayed for suspicious packets
- Color-coded by packet type:
  - Red border: Anomalous packets (score > 0.5)
  - Yellow border: Write operations
  - Gray border: Normal reads
- Last 20 packets displayed
- Smooth animations on new packets

---

### ✅ 3. Traffic Graph Behavior

**Before:**
Random walk with no attack pattern

**After:**
Realistic traffic patterns:

| Phase | Behavior | Rate (pps) | Description |
|-------|----------|------------|-------------|
| **Baseline** | Stable | 50-55 | Normal industrial operations |
| **Attack** | Spike | 80-100 | Increased scanning and write attempts |
| **Post-Trap** | Elevated | 55-60 | Slightly elevated but stabilized |

**Algorithm:**
```javascript
// Smooth drift toward target rate
const drift = (targetRate - lastRate) * 0.15;
const randomWalk = (Math.random() - 0.5) * variance;
const newRate = lastRate + drift + randomWalk;
```

**Features:**
- Gradual transitions (no sudden jumps)
- State-aware target rates
- Realistic variance for each phase
- Bounds checking (30-120 pps)
- Color changes with alert state (cyan → red)

---

## Technical Implementation

### New Files Created

1. **dashboard/src/pages/MonitorPage.jsx** (new)
   - Comprehensive monitoring page component
   - Three sub-components:
     - `LiveEventStream`: Synthesized + real events
     - `PacketStream`: Detailed packet information
     - Layout integration with metrics

### Files Modified

1. **dashboard/src/App.jsx**
   - Added `MonitorPage` import
   - Updated `/monitor` route to use new component
   - Enhanced traffic data simulation algorithm
   - State-aware traffic generation (baseline/attack/trap)

### Data Flow

```
Backend (Redis) → Socket.IO → App.jsx State → MonitorPage Props
                                              ↓
                    Lifecycle Events ← PlaybookState
                    Real Events      ← events[]
                    Traffic Pattern  ← alertActive, trapActive
```

---

## Component Architecture

### MonitorPage
```
MonitorPage (container)
├── Header with status indicator
├── Metrics Row
│   ├── AnomalyGauge (existing)
│   └── TrafficSparkline (enhanced)
└── Monitoring Streams
    ├── LiveEventStream (new)
    │   ├── Synthesized lifecycle events
    │   └── Real backend events
    └── PacketStream (new)
        └── Detailed packet information
```

### Event Synthesis Logic

Monitors `playbookState` and generates contextual events:

| State | Generated Event |
|-------|----------------|
| DEMO_LAUNCHING | "Attack simulation started" |
| SCANNING_DETECTED | "Network scanning activity detected" |
| THREAT_CONFIRMED | "Unauthorized Modbus write detected" |
| TRAP_DEPLOYING | "PLC register modification attempt" |
| TRAP_ACTIVE | "Anomaly threshold exceeded"<br>"Deception trap deployed"<br>"Malicious traffic redirected" |
| PROFILING | "Behavioral profiling in progress" |
| CONTAINED | "Threat contained - report generated" |

---

## Success Criteria Met

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| ✅ Fix "No events to display" | Done | Synthesized lifecycle events + real events |
| ✅ Show packet activity | Done | Detailed packet stream widget |
| ✅ Realistic traffic graph | Done | State-aware traffic simulation |
| ✅ Preserve anomaly logic | Done | Backend unchanged, frontend-only |
| ✅ Preserve attack engine | Done | No backend modifications |

---

## Visual Design

### Color Scheme
- **Critical** (🔴): `#ef4444` - Unauthorized access, high anomalies
- **Warning** (⚠️): `#eab308` - Suspicious activity, threshold exceeded
- **Success** (✓): `#10b981` - Successful defense actions
- **Info** (•): `#64748b` - General telemetry

### Typography
- **Timestamps**: Monospace, slate-500
- **Event text**: Sans-serif, color-coded by severity
- **Packet details**: Monospace for IPs/registers, sans-serif for labels

### Animations
- Slide-in from left on new events (300ms)
- Auto-scroll to latest
- Pulsing status indicators
- Smooth color transitions

---

## Backend Compatibility

### No Breaking Changes
✅ All existing Redis event structures preserved  
✅ Socket.IO event listeners unchanged  
✅ Anomaly detection logic untouched  
✅ Attack simulation engine unchanged  
✅ Backend API unchanged  

### Data Sources Used
- `events[]`: Real events from Redis via Socket.IO
- `playbookState`: Current SOAR playbook state
- `alertActive`: Boolean flag for intrusion detection
- `trapActive`: Boolean flag for deception deployment
- `anomalyScore`: Real-time LSTM anomaly score
- `trafficData`: Time-series traffic rate

---

## Testing Guide

### Test Scenario 1: Normal Operations
1. Navigate to `/monitor` page
2. **Expected:**
   - Traffic graph stable around 50-55 pps
   - "Monitoring Network..." message
   - Anomaly gauge at 0%
   - Status: NOMINAL (green)

### Test Scenario 2: Attack Detection
1. Start demo attack
2. **Expected:**
   - Events appear: "Attack simulation started"
   - Traffic spikes to 80-100 pps
   - Packet stream shows Modbus packets
   - "Unauthorized Modbus write detected"
   - Status: INTRUSION DETECTED (red)
   - Anomaly gauge increases

### Test Scenario 3: Trap Deployment
1. Wait for trap deployment
2. **Expected:**
   - Events: "Deception trap deployed"
   - Events: "Malicious traffic redirected"
   - Traffic stabilizes to 55-60 pps
   - Packet stream continues showing activity
   - Status remains red until containment

### Test Scenario 4: Containment
1. Wait for profiling completion
2. **Expected:**
   - Events: "Behavioral profiling in progress"
   - Events: "Threat contained - report generated"
   - All lifecycle events visible in stream

### Test Scenario 5: System Reset
1. Click reset
2. **Expected:**
   - Event stream clears
   - Traffic returns to baseline (50-55 pps)
   - Status: NOMINAL
   - Ready for new attack

---

## Performance

- **Event rendering**: O(n) with virtual scrolling
- **Traffic updates**: 1Hz (1 second intervals)
- **Event synthesis**: Reactive to state changes only
- **Memory**: Capped at 50 events in stream
- **Animations**: Hardware-accelerated (transform, opacity)

---

## Future Enhancements (Optional)

- Export event logs to CSV/JSON
- Filter events by severity level
- Search/filter in event stream
- Historical playback of past attacks
- Packet capture download
- Real-time protocol statistics
- Network flow visualization
- GeoIP mapping for attacker source
- Correlation with external threat feeds

---

## Browser Compatibility

✅ Chrome/Edge 90+  
✅ Firefox 88+  
✅ Safari 14+  
✅ Modern mobile browsers  

---

## Dependencies

All existing (no new packages added):
- `react`: UI framework
- `framer-motion`: Animations
- `lucide-react`: Icons
- `recharts`: Traffic graph
- `socket.io-client`: Real-time events

---

## File Summary

### New Files (1)
- `dashboard/src/pages/MonitorPage.jsx` - Complete monitoring page with event stream and packet details

### Modified Files (1)
- `dashboard/src/App.jsx` - Import MonitorPage, update route, enhance traffic simulation

### Unchanged (Backend)
- `monitor/agent.py` - Anomaly detection logic preserved
- `api/server.py` - Event publishing unchanged
- `attacker/attack.py` - Attack simulation unchanged
- All backend Redis channels unchanged

---

## Quick Reference

### Event Severity Levels
```javascript
'critical' → 🔴 Red   (Anomalies, unauthorized access)
'warning'  → ⚠️ Yellow (Suspicious activity)
'success'  → ✓ Green  (Defense actions)
'info'     → • Gray   (Normal telemetry)
```

### Modbus Function Codes
```
1  - Read Coils
3  - Read Holding Registers
6  - Write Single Register
16 - Write Multiple Registers
```

### Traffic Rates
```
Baseline:  50-55 pps  (±2 variance)
Attack:    80-100 pps (±10 variance)
Post-Trap: 55-60 pps  (±3 variance)
```
