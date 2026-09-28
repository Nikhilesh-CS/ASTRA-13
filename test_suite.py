"""
Comprehensive Regression & Security Test Suite for QDS Simulation
Tests:
1. Web server route '/' loads valid HTML with accessible elements
2. '/api/simulate' with NONE attack -> ACCEPT
3. '/api/simulate' with MITM attack -> REJECT & ALERT (QBER violation)
4. '/api/simulate' with FORGERY attack -> REJECT & ALERT (Hash/state violation)
5. '/api/simulate' with IMPERSONATION attack -> REJECT & ALERT (Pauli/state violation)
6. '/api/simulate' with REPLAY attack -> REJECT & ALERT (Nonce/timestamp violation)
7. Input Validation:
   - qubit_count out of range -> 400
   - ambient_noise out of range -> 400
   - threshold out of range -> 400
   - invalid attack_type -> 400
   - message > 5000 chars -> 400
8. Session Isolation & Nonce Reset endpoint
"""

import unittest
import json
from app import app

class TestQDSSimulation(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'QUANTUM ASTRA', response.data)
        self.assertIn(b'SIH26141', response.data)
        self.assertIn(b'role="radiogroup"', response.data)
        self.assertIn(b'advSettingsSection', response.data)
        self.assertIn(b'conceptGuideDrawer', response.data)

    def test_legitimate_transmission(self):
        payload = {
            "message": "Valid Wire Transfer $5,000",
            "qubit_count": 16,
            "ambient_noise": 1.0,
            "threshold": 11.0,
            "attack_type": "NONE"
        }
        res = self.client.post('/api/simulate', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        verdict = data['verification']['verdict']
        self.assertEqual(verdict, 'ACCEPT')
        self.assertFalse(data['verification']['threat_detected'])
        self.assertLessEqual(data['verification']['metrics']['qber_percent'], 11.0)

    def test_mitm_eavesdropping_attack(self):
        payload = {
            "message": "Valid Wire Transfer $5,000",
            "qubit_count": 16,
            "ambient_noise": 2.0,
            "threshold": 11.0,
            "attack_type": "MITM"
        }
        res = self.client.post('/api/simulate', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        verdict = data['verification']['verdict']
        self.assertEqual(verdict, 'REJECT & ALERT')
        self.assertTrue(data['verification']['threat_detected'])
        self.assertGreater(data['verification']['metrics']['qber_percent'], 11.0)

    def test_forgery_attack(self):
        payload = {
            "message": "Original Message",
            "qubit_count": 16,
            "ambient_noise": 2.0,
            "threshold": 11.0,
            "attack_type": "FORGERY"
        }
        res = self.client.post('/api/simulate', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        verdict = data['verification']['verdict']
        self.assertEqual(verdict, 'REJECT & ALERT')
        self.assertTrue(data['verification']['threat_detected'])

    def test_impersonation_attack(self):
        payload = {
            "message": "Original Message",
            "qubit_count": 16,
            "ambient_noise": 2.0,
            "threshold": 11.0,
            "attack_type": "IMPERSONATION"
        }
        res = self.client.post('/api/simulate', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        verdict = data['verification']['verdict']
        self.assertEqual(verdict, 'REJECT & ALERT')
        self.assertTrue(data['verification']['threat_detected'])

    def test_replay_attack(self):
        # 1. Send legitimate
        payload_legit = {
            "message": "Original Transaction",
            "qubit_count": 16,
            "ambient_noise": 1.0,
            "threshold": 11.0,
            "attack_type": "NONE"
        }
        self.client.post('/api/simulate', data=json.dumps(payload_legit), content_type='application/json')

        # 2. Replay it
        payload_replay = {
            "message": "Original Transaction",
            "qubit_count": 16,
            "ambient_noise": 1.0,
            "threshold": 11.0,
            "attack_type": "REPLAY"
        }
        res = self.client.post('/api/simulate', data=json.dumps(payload_replay), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        verdict = data['verification']['verdict']
        self.assertEqual(verdict, 'REJECT & ALERT')
        self.assertTrue(data['verification']['threat_detected'])
        self.assertEqual(data['verification']['threat_type'], 'REPLAY_ATTACK')

    def test_input_validation_qubits(self):
        # Too low
        res = self.client.post('/api/simulate', data=json.dumps({"qubit_count": 4}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("qubit_count", res.get_json()["error"])

        # Too high
        res = self.client.post('/api/simulate', data=json.dumps({"qubit_count": 64}), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_input_validation_noise(self):
        res = self.client.post('/api/simulate', data=json.dumps({"ambient_noise": 25}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("ambient_noise", res.get_json()["error"])

    def test_input_validation_threshold(self):
        res = self.client.post('/api/simulate', data=json.dumps({"threshold": 45}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("threshold", res.get_json()["error"])

    def test_input_validation_attack_type(self):
        res = self.client.post('/api/simulate', data=json.dumps({"attack_type": "HACK_THE_PLANET"}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("attack_type", res.get_json()["error"])

    def test_input_validation_message_length(self):
        huge_message = "A" * 6000
        res = self.client.post('/api/simulate', data=json.dumps({"message": huge_message}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertIn("maximum length", res.get_json()["error"])

    def test_reset_nonce_endpoint(self):
        res = self.client.post('/api/reset-nonce')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["status"], "success")

if __name__ == '__main__':
    unittest.main()
