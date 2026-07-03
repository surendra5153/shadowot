import json
import os
from stix2 import MemoryStore

class ATTCKMapper:
    def __init__(self, data_path="attck-mapper/data/ics-attack.json"):
        self.data_path = data_path
        self.techniques = {}
        self._load_data()
        
        # Rule thresholds
        self.dos_threshold = 20  # commands per second
        self.critical_registers = range(0, 100)
        self.config_registers_start = 400

    def _load_data(self):
        if not os.path.exists(self.data_path):
            print(f"Warning: {self.data_path} not found.")
            return

        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.store = MemoryStore(stix_data=data)

        # Extract ICS techniques
        from stix2 import Filter
        techniques = self.store.query([
            Filter("type", "=", "attack-pattern")
        ])
        
        for t in techniques:
            external_ids = [ref['external_id'] for ref in t.get('external_references', []) if ref.get('source_name') == 'mitre-attack']
            if external_ids:
                tech_id = external_ids[0]
                self.techniques[tech_id] = {
                    "id": tech_id,
                    "name": t.name,
                    "description": t.description,
                    "tactics": [phase['phase_name'] for phase in t.get('kill_chain_phases', [])],
                    "detection": t.get('x_mitre_detection', ''),
                    "mitigations": [] # Mitigations are usually separate objects in STIX, but we'll simplify
                }

    @staticmethod
    def _parse_timestamp(ts):
        """Convert timestamp to float (handles ISO strings and floats)."""
        if isinstance(ts, (int, float)):
            return float(ts)
        if isinstance(ts, str):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                return dt.timestamp()
            except Exception:
                return 0.0
        return 0.0

    def map_event(self, event, history=None):
        matched = []

        func = event.get('function_code')
        addr = event.get('address', 0)

        # Skip events without Modbus-level detail
        if func is None:
            return matched

        # DEMO HEURISTIC: First alert implies Initial Access and Execution in this network context
        for tid in ['T0822', 'T0816']:
            tech = self.techniques.get(tid)
            if tech: matched.append(tech)

        # T0855: Unauthorized Command Message (FC 06 or FC 16 to critical registers)
        if func in [0x06, 0x10] and addr in self.critical_registers:
            matched.append(self.techniques.get('T0855'))

        # T0836: Modify Parameter
        if func in [0x06, 0x10] and addr > self.config_registers_start:
            matched.append(self.techniques.get('T0836'))

        # T0861: Point & Tag Identification
        if func == 0x2B:
            matched.append(self.techniques.get('T0861'))

        # T0806: Brute Force I/O (rapid writes to coils or registers)
        if func in [0x05, 0x0F, 0x06, 0x10]:
            if history and len([e for e in history if e.get('function_code') in [0x05, 0x0F, 0x06, 0x10]]) > 10:
                 matched.append(self.techniques.get('T0806'))

        if history:
            # T0814: Denial of Service
            now = self._parse_timestamp(event.get('timestamp', 0))
            recent = [e for e in history if now - self._parse_timestamp(e.get('timestamp', 0)) < 1.0]
            if len(recent) > self.dos_threshold:
                matched.append(self.techniques.get('T0814'))

            # T0846: Remote System Discovery
            read_funcs = [0x01, 0x02, 0x03, 0x04]
            if func in read_funcs:
                recent_reads = [e for e in history if e.get('function_code') in read_funcs]
                addrs = sorted(list(set([e.get('address', 0) for e in recent_reads] + [addr])))
                if len(addrs) > 20:
                    diffs = [addrs[i+1] - addrs[i] for i in range(len(addrs)-1)]
                    if all(d == 1 for d in diffs[-10:]):
                         matched.append(self.techniques.get('T0846'))
                # Demo fallback: repeated read sweeps often use the same register in this lab.
                elif len(recent_reads) >= 8:
                    matched.append(self.techniques.get('T0846'))

            # T0867: Lateral Tool Transfer
            dst_ips = set([e.get('dst_ip') for e in history if e.get('dst_ip')] + [event.get('dst_ip')])
            dst_ips.discard(None)
            if len(dst_ips) > 3:
                matched.append(self.techniques.get('T0867'))

        return [m for m in matched if m]

if __name__ == "__main__":
    mapper = ATTCKMapper()
    print(f"Loaded {len(mapper.techniques)} techniques.")
    
    # Test T0855
    test_event = {
        'function_code': 0x10,
        'address': 10,
        'value': 1,
        'src_ip': '10.5.1.50',
        'dst_ip': '10.5.0.10',
        'timestamp': 1620000000.0
    }
    matches = mapper.map_event(test_event)
    for m in matches:
        print(f"Match: {m['id']} - {m['name']}")
