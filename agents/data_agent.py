#!/usr/bin/env python3
"""
Data Agent for E-commerce Testing
Generates and manages test data, scenarios, and validation sets
"""

import json
import random
from typing import Dict, Any, List
from faker import Faker
from .base_agent import BaseAgent

class DataAgent(BaseAgent):
    """Data generation and management agent"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "DataAgent")
        self.faker = Faker()
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data generation task"""
        task_type = task.get("type")
        
        if task_type == "generate_test_data":
            return await self.generate_test_data(task)
        elif task_type == "generate_invalid_data":
            return await self.generate_invalid_data(task)
        elif task_type == "generate_edge_cases":
            return await self.generate_edge_cases(task)
        elif task_type == "generate_performance_data":
            return await self.generate_performance_data(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def generate_test_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test data set"""
        site_config = task.get("site_config", {})
        
        # Get LLM guidance for test data generation
        llm_prompt = f"""
        Generate test data strategy for e-commerce site: {site_config.get('name', 'unknown')}
        Site URL: {site_config.get('base_url', 'unknown')}
        
        Provide recommendations for:
        1. User profiles to test
        2. Product categories to focus on
        3. Payment scenarios to cover
        4. Geographic regions to test
        5. Edge cases specific to this site
        """
        
        llm_guidance = await self.call_llm(llm_prompt, "Test data generation strategy")
        
        test_data = {
            "llm_guidance": llm_guidance,
            "valid_test_cards": self._generate_test_cards(),
            "test_addresses": self._generate_test_addresses(),
            "user_profiles": self._generate_user_profiles(),
            "product_scenarios": self._generate_product_scenarios(),
            "invalid_data_sets": await self.generate_invalid_data({}),
            "edge_cases": await self.generate_edge_cases({}),
            "performance_data": await self.generate_performance_data({})
        }
        
        await self.log_task_completion("generate_test_data", True, {
            "cards_generated": len(test_data["valid_test_cards"]),
            "addresses_generated": len(test_data["test_addresses"]),
            "profiles_generated": len(test_data["user_profiles"])
        })
        
        return test_data
    
    async def generate_invalid_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate invalid data for validation testing"""
        invalid_data = {
            "invalid_emails": [
                "invalid-email",
                "@invalid.com",
                "test@",
                "test..test@example.com",
                "test@.com",
                "",
                "a" * 100 + "@example.com"
            ],
            "invalid_cards": [
                {
                    "number": "1234567890123456",
                    "expiry": "12/20",
                    "cvv": "123",
                    "name": "Test User",
                    "error_type": "invalid_number"
                },
                {
                    "number": "4242424242424242",
                    "expiry": "12/20",
                    "cvv": "123",
                    "name": "Test User",
                    "error_type": "expired_card"
                },
                {
                    "number": "4242424242424242",
                    "expiry": "12/25",
                    "cvv": "12",
                    "name": "Test User",
                    "error_type": "invalid_cvv"
                }
            ],
            "invalid_addresses": [
                {
                    "first_name": "",
                    "last_name": "Doe",
                    "address": "123 Test St",
                    "city": "Test City",
                    "error_type": "missing_first_name"
                },
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address": "",
                    "city": "Test City",
                    "error_type": "missing_address"
                }
            ],
            "invalid_phones": [
                "123",
                "abc-def-ghij",
                "+1-800-INVALID",
                "",
                "1" * 20
            ],
            "sql_injection_attempts": [
                "'; DROP TABLE users; --",
                "1' OR '1'='1",
                "<script>alert('xss')</script>",
                "../../etc/passwd"
            ]
        }
        
        await self.log_task_completion("generate_invalid_data", True, {
            "invalid_sets_generated": len(invalid_data)
        })
        
        return invalid_data
    
    async def generate_edge_cases(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate edge case scenarios"""
        edge_cases = {
            "boundary_values": {
                "max_quantity": 999999,
                "zero_quantity": 0,
                "negative_quantity": -1,
                "max_string_length": "A" * 1000,
                "unicode_characters": "测试用户名 🛒 émile",
                "special_characters": "!@#$%^&*()_+-=[]{}|;:,.<>?"
            },
            "timing_scenarios": {
                "rapid_clicks": "simulate_rapid_button_clicks",
                "session_timeout": "test_session_expiration",
                "concurrent_users": "simulate_multiple_sessions",
                "slow_network": "simulate_network_delays"
            },
            "browser_scenarios": {
                "disabled_javascript": "test_without_js",
                "disabled_cookies": "test_without_cookies",
                "mobile_viewport": "test_mobile_responsive",
                "old_browser": "test_legacy_browser_support"
            },
            "payment_edge_cases": {
                "international_cards": self._generate_international_cards(),
                "corporate_cards": self._generate_corporate_cards(),
                "prepaid_cards": self._generate_prepaid_cards(),
                "gift_cards": self._generate_gift_cards()
            }
        }
        
        await self.log_task_completion("generate_edge_cases", True, {
            "edge_case_categories": len(edge_cases)
        })
        
        return edge_cases
    
    async def generate_performance_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance testing scenarios"""
        performance_data = {
            "load_scenarios": [
                {
                    "name": "normal_load",
                    "concurrent_users": 10,
                    "duration_minutes": 5,
                    "ramp_up_time": 60
                },
                {
                    "name": "peak_load",
                    "concurrent_users": 50,
                    "duration_minutes": 10,
                    "ramp_up_time": 120
                },
                {
                    "name": "stress_test",
                    "concurrent_users": 100,
                    "duration_minutes": 15,
                    "ramp_up_time": 300
                }
            ],
            "performance_thresholds": {
                "page_load_time_ms": 3000,
                "api_response_time_ms": 1000,
                "checkout_completion_time_ms": 30000,
                "error_rate_percentage": 1.0,
                "cpu_usage_percentage": 80.0,
                "memory_usage_mb": 512
            },
            "monitoring_points": [
                "page_load_start",
                "dom_content_loaded",
                "first_contentful_paint",
                "largest_contentful_paint",
                "form_submission_start",
                "payment_processing_start",
                "order_confirmation_loaded"
            ]
        }
        
        await self.log_task_completion("generate_performance_data", True, {
            "scenarios_generated": len(performance_data["load_scenarios"])
        })
        
        return performance_data
    
    def _generate_test_cards(self) -> List[Dict[str, str]]:
        """Generate valid test credit cards"""
        test_cards = [
            {
                "number": "4242424242424242",
                "expiry": "12/25",
                "cvv": "123",
                "name": "Test User",
                "type": "visa",
                "description": "Valid Visa test card"
            },
            {
                "number": "5555555555554444",
                "expiry": "12/25",
                "cvv": "123",
                "name": "Test User",
                "type": "mastercard",
                "description": "Valid Mastercard test card"
            },
            {
                "number": "378282246310005",
                "expiry": "12/25",
                "cvv": "1234",
                "name": "Test User",
                "type": "amex",
                "description": "Valid American Express test card"
            },
            {
                "number": "4000000000000002",
                "expiry": "12/25",
                "cvv": "123",
                "name": "Test User",
                "type": "visa_declined",
                "description": "Visa card that will be declined"
            }
        ]
        
        return test_cards
    
    def _generate_test_addresses(self) -> List[Dict[str, str]]:
        """Generate test addresses for different regions"""
        addresses = []
        
        # US addresses
        for _ in range(3):
            addresses.append({
                "first_name": self.faker.first_name(),
                "last_name": self.faker.last_name(),
                "email": self.faker.email(),
                "phone": self.faker.phone_number(),
                "address": self.faker.street_address(),
                "city": self.faker.city(),
                "state": self.faker.state_abbr(),
                "zip": self.faker.zipcode(),
                "country": "US",
                "region": "North America"
            })
        
        # International addresses
        locales = ['en_GB', 'de_DE', 'fr_FR', 'ja_JP']
        for locale in locales:
            fake_intl = Faker(locale)
            addresses.append({
                "first_name": fake_intl.first_name(),
                "last_name": fake_intl.last_name(),
                "email": fake_intl.email(),
                "phone": fake_intl.phone_number(),
                "address": fake_intl.street_address(),
                "city": fake_intl.city(),
                "state": fake_intl.state() if hasattr(fake_intl, 'state') else fake_intl.city(),
                "zip": fake_intl.postcode(),
                "country": locale.split('_')[1],
                "region": "International"
            })
        
        return addresses
    
    def _generate_user_profiles(self) -> List[Dict[str, Any]]:
        """Generate different user profiles for testing"""
        profiles = [
            {
                "type": "new_customer",
                "description": "First-time buyer",
                "behavior": "cautious, reads reviews, compares prices",
                "expected_actions": ["browse_products", "read_reviews", "add_to_cart", "checkout"]
            },
            {
                "type": "returning_customer",
                "description": "Loyal customer with account",
                "behavior": "quick purchase, uses saved payment methods",
                "expected_actions": ["login", "quick_add_to_cart", "express_checkout"]
            },
            {
                "type": "mobile_user",
                "description": "Shopping on mobile device",
                "behavior": "touch interactions, smaller screen",
                "expected_actions": ["mobile_browse", "mobile_checkout", "mobile_payment"]
            },
            {
                "type": "international_customer",
                "description": "Customer from different country",
                "behavior": "currency conversion, international shipping",
                "expected_actions": ["currency_check", "shipping_options", "international_payment"]
            },
            {
                "type": "bulk_buyer",
                "description": "Business customer buying in quantity",
                "behavior": "large quantities, bulk discounts",
                "expected_actions": ["quantity_selection", "bulk_pricing", "business_checkout"]
            }
        ]
        
        return profiles
    
    def _generate_product_scenarios(self) -> List[Dict[str, Any]]:
        """Generate product-specific test scenarios"""
        scenarios = [
            {
                "category": "electronics",
                "test_cases": ["warranty_options", "technical_specs", "compatibility_check"],
                "special_handling": "extended_warranty_popup"
            },
            {
                "category": "clothing",
                "test_cases": ["size_selection", "color_options", "return_policy"],
                "special_handling": "size_guide_modal"
            },
            {
                "category": "digital_products",
                "test_cases": ["instant_download", "license_agreement", "digital_delivery"],
                "special_handling": "no_shipping_required"
            },
            {
                "category": "subscription",
                "test_cases": ["recurring_billing", "trial_period", "cancellation_policy"],
                "special_handling": "subscription_terms_modal"
            }
        ]
        
        return scenarios
    
    def _generate_international_cards(self) -> List[Dict[str, str]]:
        """Generate international test cards"""
        return [
            {
                "number": "4000000760000002",
                "expiry": "12/25",
                "cvv": "123",
                "name": "Test User",
                "country": "BR",
                "type": "visa_brazil"
            },
            {
                "number": "4000001240000000",
                "expiry": "12/25",
                "cvv": "123",
                "name": "Test User",
                "country": "CA",
                "type": "visa_canada"
            }
        ]
    
    def _generate_corporate_cards(self) -> List[Dict[str, str]]:
        """Generate corporate test cards"""
        return [
            {
                "number": "5555555555554444",
                "expiry": "12/25",
                "cvv": "123",
                "name": "Corporate Account",
                "type": "corporate_mastercard",
                "billing_type": "corporate"
            }
        ]
    
    def _generate_prepaid_cards(self) -> List[Dict[str, str]]:
        """Generate prepaid test cards"""
        return [
            {
                "number": "4000000000000010",
                "expiry": "12/25",
                "cvv": "123",
                "name": "Prepaid User",
                "type": "visa_prepaid",
                "balance": "100.00"
            }
        ]
    
    def _generate_gift_cards(self) -> List[Dict[str, str]]:
        """Generate gift card test data"""
        return [
            {
                "code": "GIFT-TEST-001",
                "balance": "50.00",
                "type": "gift_card",
                "expiry": "12/25"
            },
            {
                "code": "PROMO-TEST-001",
                "discount": "10%",
                "type": "promo_code",
                "min_purchase": "25.00"
            }
        ]