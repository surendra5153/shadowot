# Trap Management Center - Quick Start Guide

## Accessing the Page

1. Start the Shadow-OT platform: `docker-compose up -d`
2. Open browser: `http://localhost:3000`
3. Click the **⚡ Zap icon** in the left sidebar
4. You'll see the Trap Management Center

## What You'll See Initially

### Baseline State
- **1 Active Trap** (TRAP-01, PLC Twin mirroring PLC-01)
- **0 Live Sessions** (no attackers yet)
- **Empty Command Stream** (waiting for commands)
- **System Initialized** in timeline
- **Asset Inventory** showing available shadows
- **TRAP-01 Health** at moderate levels
- **0 Engagement Score**

## Triggering Activity

### Method 1: Use Demo Launcher
1. Click the **🚀 DEMO** button (bottom-right corner)
2. Select attack scenario
3. Click "Launch Demo"
4. Watch the Trap Management page update in real-time

### Method 2: Manual Trap Generation
1. Scroll to bottom-right section "Adaptive Trap Generation"
2. Click **"Generate Adaptive Trap"** button
3. New trap (TRAP-02, TRAP-03, etc.) appears immediately
4. Check Active Traps table and Asset Inventory

## Real-Time Updates During Attack

### You'll See:
1. **New Session** appears in "Live Attacker Sessions"
   - Shows attacker IP (usually 10.5.1.50)
   - Duration counter starts
   - Status: Capturing

2. **Commands Start Streaming**
   - MODBUS TCP commands appear
   - READ/WRITE operations visible
   - Registers and values shown

3. **Timeline Grows**
   - "Attacker Redirected" event
   - "Command Captured" events
   - "Profiling Started" event

4. **Metrics Update**
   - Attackers Redirected: +1
   - Commands Captured: increases
   - Avg Engagement Time: live counter
   - Engagement Score: climbs toward 100

5. **Network Map Animates**
   - Red line: attacker → trap
   - Cyan line: trap → shadow assets
   - Animated packet flow

## Key Sections Explained

### 1. Top Bar
- Shows total active traps and live sessions at a glance

### 2. KPI Cards (Row 1)
- Quick metrics: redirected attackers, captured commands, engagement time, detection rate

### 3. Active Traps Table (Row 2, Left)
- All deployed traps listed
- Status, type, mirrored asset, creation time

### 4. Live Attacker Sessions (Row 2, Right)
- Current active attack sessions
- Duration, command count, status

### 5. Captured Commands (Row 3, Left)
- Real-time command stream
- Protocol, command type, register, value

### 6. Timeline (Row 3, Right)
- Chronological events
- Color-coded by type

### 7. Asset Inventory (Row 4, Left)
- Count of shadow assets by type

### 8. Trap Health (Row 4, Middle)
- CPU, memory, connections per trap
- Health status indicators

### 9. Engagement Score (Row 4, Right)
- 0-100 score visualization
- Based on attacker interaction quality

### 10. Network Map (Row 5, Left)
- Visual topology with animated flows

### 11. Adaptive Generator (Row 5, Right)
- Manual trap creation
- Configuration preview

## Color Coding

- **🟢 Green**: Healthy, normal, active
- **🔵 Cyan**: Traps, deception assets
- **🟡 Yellow**: Standby, elevated
- **🔴 Red**: Attack, compromised, critical

## Troubleshooting

### No Updates During Attack?
- Check browser console for errors
- Verify WebSocket connection (should see socket events)
- Ensure API container is running: `docker ps | grep api`

### Traps Not Appearing?
- Check response-engine logs: `docker logs response-engine`
- Verify Redis is running: `docker ps | grep redis`

### Manual Trap Generation Not Working?
- This is client-side only - creates UI entries
- Real traps deployed by response-engine during attacks

## Integration with Other Pages

- **Dashboard**: Shows overall system status and trap count
- **Network Monitor**: Detailed packet analysis
- **DNA Profiler**: Attacker behavioral analysis from trap data
- **Reports**: Incident reports reference trap sessions
- **Threat Intel**: STIX bundles include trap IOCs

## Best Practices

1. **Monitor during attacks** to see real-time deception in action
2. **Check trap health** regularly to ensure traps are responsive
3. **Review command stream** to understand attacker behavior
4. **Use timeline** to reconstruct attack sequence
5. **Generate adaptive traps** proactively before attacks

## Performance Notes

- Page handles up to **10 simultaneous traps** efficiently
- Command stream limited to **last 20 commands** (auto-scrolls)
- Timeline maintains **last 15 events** (auto-scrolls)
- Session list shows **last 5 sessions** (auto-scrolls)

## Next Steps

After reviewing the Trap Management page:
1. Try launching multiple demo attacks
2. Generate several adaptive traps
3. Watch metrics accumulate
4. Review timeline to understand attack progression
5. Check DNA Profiler page for behavioral analysis
6. Download incident reports for full attack details

---

**Need Help?** Check the main documentation in `TRAP_MANAGEMENT_IMPLEMENTATION.md`
