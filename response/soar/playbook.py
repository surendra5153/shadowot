import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from transitions import Machine

ALERT_ENTRY_THRESHOLD = float(os.environ.get("SOAR_ALERT_ENTRY_THRESHOLD", "0.29"))
THREAT_CONFIRM_THRESHOLD = float(os.environ.get("SOAR_THREAT_CONFIRM_THRESHOLD", "0.29"))


class PlaybookEngine:
    states = [
        "IDLE",
        "SCANNING_DETECTED",
        "THREAT_CONFIRMED",
        "TRAP_DEPLOYING",
        "TRAP_ACTIVE",
        "PROFILING",
        "REPORT_GENERATING",
        "CONTAINED",
    ]

    def __init__(self, redis_client, response_engine, state_path="/app/soar/state.json", log_dir="/app/soar/logs"):
        self.redis = redis_client
        self.response_engine = response_engine
        self.state_path = state_path
        self.log_dir = log_dir
        self.current_session_id = None
        self._profile_started_at = None
        self._lock = threading.Lock()

        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        self.machine = Machine(model=self, states=self.states, initial="IDLE")
        self.machine.add_transition("detect_scanning", "IDLE", "SCANNING_DETECTED", after="on_scanning_detected")
        self.machine.add_transition("confirm_threat", "SCANNING_DETECTED", "THREAT_CONFIRMED", after="on_threat_confirmed")
        self.machine.add_transition("start_trap_deploy", "THREAT_CONFIRMED", "TRAP_DEPLOYING", after="on_trap_deploying")
        self.machine.add_transition("trap_healthy", "TRAP_DEPLOYING", "TRAP_ACTIVE", after="on_trap_active")
        self.machine.add_transition("start_profiling", "TRAP_ACTIVE", "PROFILING", after="on_profiling")
        self.machine.add_transition("start_report_generation", "PROFILING", "REPORT_GENERATING", after="on_report_generating")
        self.machine.add_transition("mark_contained", "REPORT_GENERATING", "CONTAINED", after="on_contained")

    def process_anomaly(self, session_id, anomaly_score, payload):
        with self._lock:
            self.current_session_id = session_id
            if self.state == "IDLE" and anomaly_score >= ALERT_ENTRY_THRESHOLD:
                self.detect_scanning(payload=payload)
            if self.state == "SCANNING_DETECTED" and anomaly_score >= THREAT_CONFIRM_THRESHOLD:
                self.confirm_threat(payload=payload)
                self.start_trap_deploy(payload=payload)

    def process_trap_health(self, session_id, trap_id, trap_ip, attacker_ip):
        with self._lock:
            self.current_session_id = session_id
            if self.state == "TRAP_DEPLOYING":
                self.trap_healthy(payload={"trap_id": trap_id, "trap_ip": trap_ip, "attacker_ip": attacker_ip})
                thread = threading.Thread(target=self._start_profiling_timer, args=(session_id,), daemon=True)
                thread.start()
                # Also start a watchdog that stops the trap after profiling window
                watchdog = threading.Thread(target=self._stop_trap_after_profiling, args=(session_id,), daemon=True)
                watchdog.start()

    def process_profile_complete(self, session_id, profile):
        with self._lock:
            self.current_session_id = session_id
            if self.state == "PROFILING":
                self.start_report_generation(payload={"profile": profile})

    def process_report_ready(self, session_id, report_path):
        with self._lock:
            self.current_session_id = session_id
            if self.state == "REPORT_GENERATING":
                self.mark_contained(payload={"report_path": report_path})

    def reset(self):
        with self._lock:
            if self.state != "IDLE":
                self.to_IDLE()
            self._persist_transition("RESET", {"reason": "session complete"})

    def _start_profiling_timer(self, session_id):
        time.sleep(30)
        with self._lock:
            if self.state == "TRAP_ACTIVE" and self.current_session_id == session_id:
                self.start_profiling(payload={"timer_seconds": 30})
                # Kick off timer to auto-advance from PROFILING
                timer = threading.Thread(target=self._auto_advance_profiling, args=(session_id,), daemon=True)
                timer.start()

    def _auto_advance_profiling(self, session_id):
        """After 60 seconds of profiling, trigger report generation."""
        time.sleep(60)
        with self._lock:
            if self.state == "PROFILING" and self.current_session_id == session_id:
                logging.info("[SOAR] Profiling timer expired — advancing to REPORT_GENERATING")
                self.start_report_generation(payload={"source": "profiling_timer"})
                timer = threading.Thread(target=self._auto_advance_report, args=(session_id,), daemon=True)
                timer.start()

    def _auto_advance_report(self, session_id):
        """After 30 seconds of report generation, advance to CONTAINED."""
        time.sleep(30)
        with self._lock:
            if self.state == "REPORT_GENERATING" and self.current_session_id == session_id:
                logging.info("[SOAR] Report timer expired — advancing to CONTAINED")
                self.mark_contained(payload={"source": "report_timer", "session_id": session_id})

    def _stop_trap_after_profiling(self, session_id):
        """Stop trap container after profiling window (30+60s)."""
        time.sleep(120)
        try:
            import docker
            dc = docker.from_env()
            trap_id = self.response_engine._session_traps.get(session_id)
            if trap_id:
                try:
                    c = dc.containers.get(trap_id)
                    c.stop(timeout=5)
                    logging.info("[SOAR] Stopped trap container %s after profiling window", trap_id)
                except Exception as e:
                    logging.warning("[SOAR] Could not stop trap %s: %s", trap_id, e)
        except Exception as e:
            logging.warning("[SOAR] Docker cleanup error: %s", e)

    def _session_log(self):
        sid = self.current_session_id or "global"
        return os.path.join(self.log_dir, f"playbook_{sid}.log")

    def _persist_transition(self, event, payload=None):
        payload = payload or {}
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "state": self.state,
            "session_id": self.current_session_id,
            "payload": payload,
        }
        try:
            if self.redis:
                self.redis.publish("shadow-ot:playbook", json.dumps(entry))
        except Exception as exc:
            logging.warning("Failed to publish playbook state: %s", exc)
        with open(self._session_log(), "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
        with open(self.state_path, "w", encoding="utf-8") as handle:
            json.dump(entry, handle, indent=2)

    def on_scanning_detected(self, payload=None):
        self._persist_transition("SCANNING_DETECTED", payload)

    def on_threat_confirmed(self, payload=None):
        self._profile_started_at = time.time()
        self._persist_transition("THREAT_CONFIRMED", payload)
        if self.redis:
            self.redis.publish("shadow-ot:alerts", json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": self.current_session_id,
                "severity": "CONFIRMED",
                "source": "soar-playbook",
            }))

    def on_trap_deploying(self, payload=None):
        self._persist_transition("TRAP_DEPLOYING", payload)
        try:
            self.response_engine.deploy_from_playbook(self.current_session_id, payload or {})
        except Exception as exc:
            logging.error("Trap deploy action failed: %s", exc)

    def on_trap_active(self, payload=None):
        self._persist_transition("TRAP_ACTIVE", payload)
        if self.redis:
            self.redis.publish("shadow-ot:events", json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": self.current_session_id,
                "trap_id": (payload or {}).get("trap_id"),
                "status": "trap_deployed",
                "event": "TRAP_DEPLOYED",
            }))

    def on_profiling(self, payload=None):
        self._persist_transition("PROFILING", payload)
        try:
            self.response_engine.start_profiling_actions(self.current_session_id)
        except Exception as exc:
            logging.error("Profiling action failed: %s", exc)

    def on_report_generating(self, payload=None):
        self._persist_transition("REPORT_GENERATING", payload)
        try:
            self.response_engine.trigger_report_generation(self.current_session_id)
        except Exception as exc:
            logging.error("Report generation action failed: %s", exc)

    def on_contained(self, payload=None):
        self._persist_transition("CONTAINED", payload)
        if self.redis:
            self.redis.publish("shadow-ot:events", json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": self.current_session_id,
                "status": "contained",
                "event": "CONTAINED",
                "report_path": (payload or {}).get("report_path"),
            }))
