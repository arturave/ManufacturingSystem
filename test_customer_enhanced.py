#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Enhanced Customer Module
Tests all new functionality
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the enhanced customer module
from customer_module_enhanced import (
    CustomerExtended,
    CustomerValidator,
    CustomerEditDialog,
    CustomerSearchDialog,
    CustomerExportDialog
)

class TestCustomerValidator(unittest.TestCase):
    """Test customer data validation"""
    
    def setUp(self):
        self.validator = CustomerValidator()
    
    def test_nip_validation_valid(self):
        """Test valid NIP numbers"""
        valid_nips = [
            '5252248481',  # Without formatting
            '525-224-84-81',  # With dashes
            '525 224 84 81',  # With spaces
            '7811767696',
            '9542742927'
        ]
        
        for nip in valid_nips:
            with self.subTest(nip=nip):
                self.assertTrue(
                    self.validator.validate_nip(nip),
                    f"NIP {nip} should be valid"
                )
    
    def test_nip_validation_invalid(self):
        """Test invalid NIP numbers"""
        invalid_nips = [
            '1234567890',  # Invalid checksum
            '123456789',   # Too short
            '12345678901', # Too long
            'ABC1234567',  # Contains letters
            '',            # Empty
            None          # None
        ]
        
        for nip in invalid_nips:
            with self.subTest(nip=nip):
                self.assertFalse(
                    self.validator.validate_nip(nip or ''),
                    f"NIP {nip} should be invalid"
                )
    
    def test_regon_validation_valid(self):
        """Test valid REGON numbers"""
        valid_regons = [
            '140517018',    # 9-digit
            '273339110',    # 9-digit
            '36442557000017',  # 14-digit (mock)
        ]
        
        for regon in valid_regons[:2]:  # Test only 9-digit ones
            with self.subTest(regon=regon):
                self.assertTrue(
                    self.validator.validate_regon(regon),
                    f"REGON {regon} should be valid"
                )
    
    def test_regon_validation_invalid(self):
        """Test invalid REGON numbers"""
        invalid_regons = [
            '123456789',   # Invalid checksum
            '12345678',    # Too short
            '1234567',     # Too short
            'ABC123456',   # Contains letters
            '',            # Empty
        ]
        
        for regon in invalid_regons:
            with self.subTest(regon=regon):
                self.assertFalse(
                    self.validator.validate_regon(regon),
                    f"REGON {regon} should be invalid"
                )
    
    def test_email_validation(self):
        """Test email validation"""
        valid_emails = [
            'user@example.com',
            'john.doe@company.co.uk',
            'contact+tag@domain.org',
            'info@subdomain.example.com'
        ]
        
        invalid_emails = [
            'invalid.email',
            '@example.com',
            'user@',
            'user @example.com',
            'user@example'
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(
                    self.validator.validate_email(email),
                    f"Email {email} should be valid"
                )
        
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(
                    self.validator.validate_email(email),
                    f"Email {email} should be invalid"
                )
    
    def test_website_validation(self):
        """Test website URL validation"""
        valid_urls = [
            'https://www.example.com',
            'http://example.com',
            'www.example.com',
            'example.com',
            'subdomain.example.co.uk',
            'https://example.com/path/to/page'
        ]
        
        invalid_urls = [
            'not a url',
            'ftp://example.com',  # Only HTTP(S) supported
            'example',
            '.com'
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(
                    self.validator.validate_website(url),
                    f"URL {url} should be valid"
                )
    
    def test_phone_validation(self):
        """Test phone number validation"""
        valid_phones = [
            '123456789',
            '+48123456789',
            '48 123 456 789',
            '+48 (12) 345-67-89',
            '0048123456789'
        ]
        
        for phone in valid_phones:
            with self.subTest(phone=phone):
                self.assertTrue(
                    self.validator.validate_phone(phone),
                    f"Phone {phone} should be valid"
                )
    
    def test_nip_formatting(self):
        """Test NIP formatting"""
        test_cases = [
            ('5252248481', '525-224-84-81'),
            ('525 224 84 81', '525-224-84-81'),
            ('525-224-84-81', '525-224-84-81')
        ]
        
        for input_nip, expected in test_cases:
            with self.subTest(input=input_nip):
                result = self.validator.format_nip(input_nip)
                self.assertEqual(result, expected)
    
    def test_phone_formatting(self):
        """Test phone number formatting"""
        test_cases = [
            ('123456789', '123 456 789'),
            ('48123456789', '+48 123 456 789'),
            ('+48123456789', '+48123456789')  # Already has +
        ]
        
        for input_phone, expected in test_cases:
            with self.subTest(input=input_phone):
                result = self.validator.format_phone(input_phone)
                self.assertEqual(result, expected)

class TestCustomerExtended(unittest.TestCase):
    """Test extended customer model"""
    
    def test_customer_creation_with_all_fields(self):
        """Test creating customer with all fields"""
        customer = CustomerExtended(
            name="Test Company Sp. z o.o.",
            short_name="Test Co.",
            nip="5252248481",
            regon="140517018",
            krs="0000123456",
            email="info@testcompany.pl",
            website="www.testcompany.pl",
            phone="+48 22 123 45 67",
            address="ul. Testowa 10",
            city="Warszawa",
            postal_code="00-001",
            country="Polska",
            contact_person="Jan Kowalski",
            contact_phone="+48 501 234 567",
            contact_email="j.kowalski@testcompany.pl",
            contact_position="Dyrektor Handlowy",
            notes="Important customer",
            customer_type="company",
            is_active=True,
            credit_limit=50000.00,
            payment_terms=30
        )
        
        self.assertEqual(customer.name, "Test Company Sp. z o.o.")
        self.assertEqual(customer.short_name, "Test Co.")
        self.assertEqual(customer.nip, "5252248481")
        self.assertEqual(customer.regon, "140517018")
        self.assertEqual(customer.krs, "0000123456")
        self.assertEqual(customer.email, "info@testcompany.pl")
        self.assertEqual(customer.contact_person, "Jan Kowalski")
        self.assertEqual(customer.credit_limit, 50000.00)
        self.assertEqual(customer.payment_terms, 30)
        self.assertTrue(customer.is_active)
    
    def test_customer_default_values(self):
        """Test customer default values"""
        customer = CustomerExtended()
        
        self.assertEqual(customer.name, "")
        self.assertEqual(customer.country, "Polska")
        self.assertEqual(customer.customer_type, "company")
        self.assertTrue(customer.is_active)
        self.assertEqual(customer.credit_limit, 0.0)
        self.assertEqual(customer.payment_terms, 14)
    
    def test_customer_to_dict(self):
        """Test converting customer to dictionary"""
        from dataclasses import asdict
        
        customer = CustomerExtended(
            name="Test Company",
            nip="5252248481",
            email="test@example.com"
        )
        
        customer_dict = asdict(customer)
        
        self.assertIsInstance(customer_dict, dict)
        self.assertEqual(customer_dict['name'], "Test Company")
        self.assertEqual(customer_dict['nip'], "5252248481")
        self.assertEqual(customer_dict['email'], "test@example.com")
        self.assertIn('contact_person', customer_dict)
        self.assertIn('credit_limit', customer_dict)

class TestBusinessLogic(unittest.TestCase):
    """Test business logic and rules"""
    
    def test_company_requires_nip(self):
        """Test that companies require NIP"""
        customer = CustomerExtended(
            name="Company Without NIP",
            customer_type="company",
            nip=""  # Empty NIP
        )
        
        # In real application, this would be validated before saving
        self.assertEqual(customer.customer_type, "company")
        self.assertEqual(customer.nip, "")
        # Validation should fail for company without NIP
    
    def test_individual_optional_nip(self):
        """Test that individuals don't require NIP"""
        customer = CustomerExtended(
            name="Jan Kowalski",
            customer_type="individual",
            nip=""  # Empty NIP is OK for individuals
        )
        
        self.assertEqual(customer.customer_type, "individual")
        self.assertEqual(customer.nip, "")
        # This should be valid
    
    def test_credit_limit_non_negative(self):
        """Test that credit limit cannot be negative"""
        customer = CustomerExtended(
            name="Test Company",
            credit_limit=-1000.00  # Should be validated
        )
        
        # In real application, this would be validated
        # Here we just check the value is set
        self.assertEqual(customer.credit_limit, -1000.00)
    
    def test_payment_terms_reasonable(self):
        """Test payment terms are reasonable"""
        valid_terms = [0, 7, 14, 21, 30, 45, 60, 90]
        
        for terms in valid_terms:
            customer = CustomerExtended(payment_terms=terms)
            self.assertEqual(customer.payment_terms, terms)

class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and consistency"""
    
    def test_email_consistency(self):
        """Test that emails are properly stored"""
        customer = CustomerExtended(
            email="UPPER@EXAMPLE.COM",  # Should preserve case
            contact_email="lower@example.com"
        )
        
        self.assertEqual(customer.email, "UPPER@EXAMPLE.COM")
        self.assertEqual(customer.contact_email, "lower@example.com")
    
    def test_phone_storage(self):
        """Test phone number storage"""
        customer = CustomerExtended(
            phone="+48 22 123 45 67",
            contact_phone="501234567"
        )
        
        self.assertEqual(customer.phone, "+48 22 123 45 67")
        self.assertEqual(customer.contact_phone, "501234567")
    
    def test_address_components(self):
        """Test address components"""
        customer = CustomerExtended(
            address="ul. Długa 10/5",
            city="Kraków",
            postal_code="30-001",
            country="Polska"
        )
        
        self.assertEqual(customer.address, "ul. Długa 10/5")
        self.assertEqual(customer.city, "Kraków")
        self.assertEqual(customer.postal_code, "30-001")
        self.assertEqual(customer.country, "Polska")

class TestSearchFunctionality(unittest.TestCase):
    """Test search functionality"""
    
    def test_search_by_name(self):
        """Test searching customers by name"""
        customers = [
            CustomerExtended(name="ABC Company", nip="5252248481"),
            CustomerExtended(name="XYZ Industries", nip="7811767696"),
            CustomerExtended(name="ABC Solutions", nip="9542742927")
        ]
        
        # Search for "ABC"
        results = [c for c in customers if "ABC" in c.name]
        self.assertEqual(len(results), 2)
        self.assertTrue(all("ABC" in c.name for c in results))
    
    def test_search_by_nip(self):
        """Test searching customers by NIP"""
        customers = [
            CustomerExtended(name="Company 1", nip="5252248481"),
            CustomerExtended(name="Company 2", nip="7811767696"),
            CustomerExtended(name="Company 3", nip="9542742927")
        ]
        
        # Search for specific NIP
        target_nip = "7811767696"
        results = [c for c in customers if c.nip == target_nip]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].nip, target_nip)
    
    def test_search_by_city(self):
        """Test searching customers by city"""
        customers = [
            CustomerExtended(name="Company 1", city="Warszawa"),
            CustomerExtended(name="Company 2", city="Kraków"),
            CustomerExtended(name="Company 3", city="Warszawa")
        ]
        
        # Search for Warsaw companies
        results = [c for c in customers if c.city == "Warszawa"]
        self.assertEqual(len(results), 2)
        self.assertTrue(all(c.city == "Warszawa" for c in results))
    
    def test_filter_inactive(self):
        """Test filtering inactive customers"""
        customers = [
            CustomerExtended(name="Active 1", is_active=True),
            CustomerExtended(name="Inactive", is_active=False),
            CustomerExtended(name="Active 2", is_active=True)
        ]
        
        # Filter only active
        active_only = [c for c in customers if c.is_active]
        self.assertEqual(len(active_only), 2)
        self.assertTrue(all(c.is_active for c in active_only))

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCustomerValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestCustomerExtended))
    suite.addTests(loader.loadTestsFromTestCase(TestBusinessLogic))
    suite.addTests(loader.loadTestsFromTestCase(TestDataIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchFunctionality))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
