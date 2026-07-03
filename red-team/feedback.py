import os
import time
import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ML_ENGINE_URL = os.environ.get('ML_ENGINE_URL', 'http://ml-engine:8001')

def process_feedback(attack_results):
    for res in attack_results:
        if not res.get('detected'):
            logging.warning(f"Attack NOT detected: {res['template']}. Sending to feedback loop.")
            
            # Send the sequence back to ML engine as a missed attack
            # Note: In a real system, we'd send the actual captured traffic sequence
            try:
                requests.post(f"{ML_ENGINE_URL}/feedback/missed", json={
                    "events": [[0.0]*6]*30 # Placeholder for real sequence
                })
            except Exception as e:
                logging.error(f"Feedback error: {e}")

    # Trigger retrain if we have enough missed attacks or once a day
    try:
        requests.post(f"{ML_ENGINE_URL}/retrain")
    except Exception as e:
        logging.error(f"Retrain trigger error: {e}")

if __name__ == "__main__":
    # This would be called by generator.py or a scheduler
    pass
