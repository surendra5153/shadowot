class KillChainTracker:
    TACTICS_ORDER = [
        "initial-access",
        "execution",
        "persistence",
        "privilege-escalation",
        "defense-evasion",
        "lateral-movement",
        "collection",
        "command-and-control",
        "inhibit-response-function",
        "impair-process-control",
        "impact"
    ]

    def __init__(self):
        self.confirmed_techniques = []
        self.current_stage_idx = 0
        self.session_id = None

    def add_technique(self, technique):
        if technique not in self.confirmed_techniques:
            self.confirmed_techniques.append(technique)
            self._update_stage(technique)

    def _update_stage(self, technique):
        tactics = technique.get('tactics', [])
        for tactic in tactics:
            if tactic in self.TACTICS_ORDER:
                idx = self.TACTICS_ORDER.index(tactic)
                if idx > self.current_stage_idx:
                    self.current_stage_idx = idx

    def get_current_stage(self):
        return self.TACTICS_ORDER[self.current_stage_idx]

    def get_confirmed_techniques(self):
        return self.confirmed_techniques

    def get_kill_chain_progress(self):
        return (self.current_stage_idx + 1) / len(self.TACTICS_ORDER) * 100

    def get_summary(self):
        return {
            "current_stage": self.get_current_stage(),
            "progress": self.get_kill_chain_progress(),
            "confirmed_techniques": [t['id'] for t in self.confirmed_techniques],
            "confirmed_details": self.confirmed_techniques
        }
