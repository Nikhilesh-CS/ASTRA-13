"""
Automated End-to-End Test Suite for QDS Simulation
Tests:
1. Web server route '/' loads valid HTML
2. '/api/simulate' with NONE attack -> ACCEPT
3. '/api/simulate' with MITM attack -> REJECT & ALERT (QBER violation)
4. '/api/simulate' with FORGERY attack -> REJECT & ALERT (Hash/state violation)
5. '/api/simulate' with IMPERSONATION attack -> REJECT & ALERT (Pauli/state violation)
6. '/api/simulate' with REPLAY attack -> REJECT & ALERT (Nonce/timestamp violation)
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
        # First send legitimate
        payload_legit = {
            "message": "Original Transaction",
            "qubit_count": 16,
            "ambient_noise": 1.0,
            "threshold": 11.0,
            "attack_type": "NONE"
        }
        self.client.post('/api/simulate', data=json.dumps(payload_legit), content_type='application/json')

        # Now send replay
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

if __name__ == '__main__':
    unittest.main()
