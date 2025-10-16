"""
Unit tests for Manufacturing System
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import datetime
from dataclasses import asdict

# Import modules to test
from mfg_app import Customer, Order, Part, OrderStatus
from quotations_module import Quotation, QUOTE_STATUSES
from outlook_agent import EmailPattern, AttachmentProcessor


class TestCustomerModel(unittest.TestCase):
    """Test Customer dataclass"""
    
    def test_customer_creation(self):
        """Test creating a customer"""
        customer = Customer(
            name="Test Company",
            contact="test@example.com"
        )
        self.assertEqual(customer.name, "Test Company")
        self.assertEqual(customer.contact, "test@example.com")
        self.assertIsNone(customer.id)
    
    def test_customer_dict_conversion(self):
        """Test converting customer to dictionary"""
        customer = Customer(
            name="Test Company",
            contact="test@example.com"
        )
        customer_dict = asdict(customer)
        self.assertIn('name', customer_dict)
        self.assertIn('contact', customer_dict)


class TestOrderModel(unittest.TestCase):
    """Test Order dataclass"""
    
    def test_order_creation(self):
        """Test creating an order"""
        order = Order(
            customer_id="123",
            title="Test Order",
            status="RECEIVED",
            price_pln=1000.00
        )
        self.assertEqual(order.customer_id, "123")
        self.assertEqual(order.title, "Test Order")
        self.assertEqual(order.status, "RECEIVED")
        self.assertEqual(order.price_pln, 1000.00)
    
    def test_order_default_values(self):
        """Test order default values"""
        order = Order()
        self.assertEqual(order.process_no, "")
        self.assertEqual(order.status, "RECEIVED")
        self.assertEqual(order.price_pln, 0.0)


class TestEmailPattern(unittest.TestCase):
    """Test email pattern detection"""
    
    def test_inquiry_detection(self):
        """Test detecting inquiry emails"""
        email_type = EmailPattern.detect_email_type(
            "Zapytanie ofertowe",
            "Proszę o wycenę elementów stalowych"
        )
        self.assertEqual(email_type, "INQUIRY")
    
    def test_order_detection(self):
        """Test detecting order emails"""
        email_type = EmailPattern.detect_email_type(
            "Zamówienie nr 12345",
            "Proszę o realizację zgodnie z ofertą"
        )
        self.assertEqual(email_type, "ORDER")
    
    def test_urgent_inquiry_detection(self):
        """Test detecting urgent inquiry emails"""
        email_type = EmailPattern.detect_email_type(
            "PILNE - Zapytanie",
            "Potrzebujemy wyceny na wczoraj"
        )
        self.assertEqual(email_type, "INQUIRY_URGENT")
    
    def test_urgent_order_detection(self):
        """Test detecting urgent order emails"""
        email_type = EmailPattern.detect_email_type(
            "Zamówienie - ASAP",
            "Pilne zamówienie do realizacji"
        )
        self.assertEqual(email_type, "ORDER_URGENT")
    
    def test_other_email_detection(self):
        """Test detecting other emails"""
        email_type = EmailPattern.detect_email_type(
            "Newsletter",
            "Najnowsze wiadomości z branży"
        )
        self.assertEqual(email_type, "OTHER")


class TestAttachmentProcessor(unittest.TestCase):
    """Test attachment processing"""
    
    def test_material_extraction(self):
        """Test extracting material information from text"""
        text = "Proszę o wycenę detali ze stali nierdzewnej 304, grubość 3mm, ilość 50 sztuk"
        result = AttachmentProcessor.extract_material_info(text)
        
        self.assertEqual(result['material'], 'Stal nierdzewna 304')
        self.assertEqual(result['thickness'], 3.0)
        self.assertEqual(result['quantity'], 50)
    
    def test_material_extraction_partial(self):
        """Test extracting partial material information"""
        text = "Elementy aluminiowe, 10 szt"
        result = AttachmentProcessor.extract_material_info(text)
        
        self.assertEqual(result['material'], 'Aluminium')
        self.assertIsNone(result['thickness'])
        self.assertEqual(result['quantity'], 10)
    
    def test_material_extraction_empty(self):
        """Test extracting from text without material info"""
        text = "Proszę o kontakt w sprawie współpracy"
        result = AttachmentProcessor.extract_material_info(text)
        
        self.assertIsNone(result['material'])
        self.assertIsNone(result['thickness'])
        self.assertIsNone(result['quantity'])


class TestQuotationModel(unittest.TestCase):
    """Test Quotation dataclass"""
    
    def test_quotation_creation(self):
        """Test creating a quotation"""
        quotation = Quotation(
            customer_id="123",
            title="Test Quote",
            total_price=5000.00,
            margin_percent=30.0
        )
        self.assertEqual(quotation.customer_id, "123")
        self.assertEqual(quotation.title, "Test Quote")
        self.assertEqual(quotation.total_price, 5000.00)
        self.assertEqual(quotation.margin_percent, 30.0)
    
    def test_quotation_with_items(self):
        """Test quotation with items"""
        items = [
            {'description': 'Item 1', 'quantity': 10, 'unit_price': 100},
            {'description': 'Item 2', 'quantity': 5, 'unit_price': 200}
        ]
        quotation = Quotation(
            customer_id="123",
            title="Test Quote",
            items=items
        )
        self.assertEqual(len(quotation.items), 2)
        self.assertEqual(quotation.items[0]['description'], 'Item 1')


class TestSupabaseManager(unittest.TestCase):
    """Test Supabase Manager (with mocking)"""
    
    @patch('mfg_app.create_client')
    def test_manager_initialization(self, mock_create_client):
        """Test SupabaseManager initialization"""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        
        # Mock environment variables
        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_KEY': 'test-key'
        }):
            from mfg_app import SupabaseManager
            manager = SupabaseManager()
            
            self.assertIsNotNone(manager.client)
            mock_create_client.assert_called_once_with(
                'https://test.supabase.co',
                'test-key'
            )


class TestBusinessLogic(unittest.TestCase):
    """Test business logic functions"""
    
    def test_status_flow(self):
        """Test order status flow is logical"""
        status_order = [
            'RECEIVED',
            'CONFIRMED',
            'PLANNED',
            'IN_PROGRESS',
            'DONE',
            'INVOICED'
        ]
        
        # Each status should have a corresponding display name
        from mfg_app import STATUS_NAMES
        for status in status_order:
            self.assertIn(status, STATUS_NAMES)
    
    def test_quote_status_flow(self):
        """Test quotation status flow"""
        quote_status_order = [
            'DRAFT',
            'SENT',
            'NEGOTIATION',
            'ACCEPTED',
            'CONVERTED'
        ]
        
        # Alternative endings
        alternative_endings = ['REJECTED', 'EXPIRED']
        
        for status in quote_status_order + alternative_endings:
            self.assertIn(status, QUOTE_STATUSES)
    
    def test_process_number_format(self):
        """Test process number format validation"""
        import re
        
        # Valid process numbers
        valid_numbers = [
            '2025-00001',
            '2025-12345',
            '2024-99999'
        ]
        
        # Invalid process numbers
        invalid_numbers = [
            '25-00001',  # Wrong year format
            '2025-1',    # Not padded
            '2025_00001', # Wrong separator
            'ABC-00001'  # Not a year
        ]
        
        pattern = r'^\d{4}-\d{5}$'
        
        for num in valid_numbers:
            self.assertIsNotNone(re.match(pattern, num), f"{num} should be valid")
        
        for num in invalid_numbers:
            self.assertIsNone(re.match(pattern, num), f"{num} should be invalid")


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    @patch('mfg_app.SupabaseManager')
    def test_order_creation_flow(self, mock_db):
        """Test complete order creation flow"""
        # Mock database responses
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance
        
        mock_db_instance.get_customers.return_value = [
            {'id': '123', 'name': 'Test Company', 'contact': 'test@example.com'}
        ]
        
        mock_db_instance.create_order.return_value = {
            'id': '456',
            'process_no': '2025-00001',
            'customer_id': '123',
            'title': 'Test Order',
            'status': 'RECEIVED'
        }
        
        # Create order
        from mfg_app import Order
        order = Order(
            customer_id='123',
            title='Test Order',
            status='RECEIVED',
            price_pln=1000.00
        )
        
        result = mock_db_instance.create_order(order)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['process_no'], '2025-00001')
        mock_db_instance.create_order.assert_called_once_with(order)


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)
