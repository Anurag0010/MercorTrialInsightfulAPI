import unittest
import json
from app import create_app, db

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_health_endpoint(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'OK')

    def test_employee_endpoints(self):
        # Test creating an employee
        employee_data = {
            'name': 'Test Employee',
            'email': 'test@example.com'
        }
        response = self.client.post('/api/employees', 
                                 data=json.dumps(employee_data), 
                                 content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        # Parse the response and check employee details
        created_employee = json.loads(response.data)
        self.assertEqual(created_employee['name'], 'Test Employee')
        self.assertEqual(created_employee['email'], 'test@example.com')

if __name__ == '__main__':
    unittest.main()
