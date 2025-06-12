#!/usr/bin/env python3
"""
Browser Agent for E-commerce Testing
Handles browser automation, form filling, and checkout flow testing
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from .base_agent import BaseAgent

class BrowserAgent(BaseAgent):
    """Browser automation agent for e-commerce testing"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "BrowserAgent")
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def __aenter__(self):
        await super().__aenter__()
        self.playwright = await async_playwright().start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        await super().__aexit__(exc_type, exc_val, exc_tb)
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser testing task"""
        task_type = task.get("type")
        
        if task_type == "checkout_flow":
            return await self.test_checkout_flow(task)
        elif task_type == "form_validation":
            return await self.test_form_validation(task)
        elif task_type == "product_search":
            return await self.test_product_search(task)
        elif task_type == "cart_management":
            return await self.test_cart_management(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def setup_browser(self, browser_type: str = "chromium") -> None:
        """Setup browser with stealth configurations"""
        browser_config = {
            "headless": self.config["testing"]["headless"],
            "args": [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        }
        
        if browser_type == "chromium":
            self.browser = await self.playwright.chromium.launch(**browser_config)
        elif browser_type == "firefox":
            self.browser = await self.playwright.firefox.launch(**browser_config)
        elif browser_type == "webkit":
            self.browser = await self.playwright.webkit.launch(**browser_config)
        
        # Create context with realistic user agent and viewport
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self.page = await self.context.new_page()
        
        # Add stealth scripts
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        self.logger.info(f"Browser {browser_type} setup completed")
    
    async def test_checkout_flow(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Test complete checkout flow"""
        site_config = task["site_config"]
        test_data = task["test_data"]
        
        results = {
            "success": False,
            "steps_completed": [],
            "errors": [],
            "performance": {},
            "screenshots": []
        }
        
        try:
            await self.setup_browser(task.get("browser", "chromium"))
            
            # Step 1: Navigate to product page
            start_time = time.time()
            await self.page.goto(site_config["product_urls"][0])
            await self.page.wait_for_load_state("networkidle")
            results["performance"]["page_load"] = time.time() - start_time
            results["steps_completed"].append("product_page_loaded")
            
            # Step 2: Add to cart
            await self._add_to_cart()
            results["steps_completed"].append("added_to_cart")
            
            # Step 3: Navigate to checkout
            await self.page.goto(site_config["checkout_url"])
            await self.page.wait_for_load_state("networkidle")
            results["steps_completed"].append("checkout_page_loaded")
            
            # Step 4: Fill shipping information
            await self._fill_shipping_form(test_data["test_addresses"][0])
            results["steps_completed"].append("shipping_form_filled")
            
            # Step 5: Fill payment information
            await self._fill_payment_form(test_data["valid_test_cards"][0])
            results["steps_completed"].append("payment_form_filled")
            
            # Step 6: Submit order (in test mode)
            if task.get("submit_order", False):
                await self._submit_order()
                results["steps_completed"].append("order_submitted")
            
            results["success"] = True
            await self.log_task_completion("checkout_flow", True, results)
            
        except Exception as e:
            results["errors"].append(str(e))
            await self._capture_screenshot(results, "checkout_flow_error")
            await self.log_task_completion("checkout_flow", False, results)
            self.logger.error(f"Checkout flow failed: {str(e)}")
        
        return results
    
    async def test_form_validation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Test form validation with invalid data"""
        results = {
            "success": False,
            "validations_tested": [],
            "errors": []
        }
        
        try:
            await self.setup_browser(task.get("browser", "chromium"))
            await self.page.goto(task["site_config"]["checkout_url"])
            
            # Test empty form submission
            await self._test_empty_form_validation(results)
            
            # Test invalid email formats
            await self._test_invalid_email_validation(results)
            
            # Test invalid card numbers
            await self._test_invalid_card_validation(results)
            
            results["success"] = True
            await self.log_task_completion("form_validation", True, results)
            
        except Exception as e:
            results["errors"].append(str(e))
            await self.log_task_completion("form_validation", False, results)
        
        return results
    
    async def test_product_search(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Test product search functionality"""
        results = {
            "success": False,
            "search_results": [],
            "errors": []
        }
        
        try:
            await self.setup_browser(task.get("browser", "chromium"))
            site_config = task["site_config"]
            
            await self.page.goto(site_config["base_url"])
            
            # Find search input
            search_selectors = [
                'input[name="search"]',
                'input[type="search"]',
                '#search',
                '.search-input'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await self.page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue
            
            if search_input:
                await search_input.fill(task.get("search_term", "test"))
                await search_input.press("Enter")
                await self.page.wait_for_load_state("networkidle")
                
                # Count search results
                result_selectors = [
                    '.product-item',
                    '.search-result',
                    '[data-testid="product"]'
                ]
                
                for selector in result_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if elements:
                            results["search_results"] = len(elements)
                            break
                    except:
                        continue
                
                results["success"] = True
            
            await self.log_task_completion("product_search", results["success"], results)
            
        except Exception as e:
            results["errors"].append(str(e))
            await self.log_task_completion("product_search", False, results)
        
        return results
    
    async def test_cart_management(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Test cart add/remove functionality"""
        results = {
            "success": False,
            "cart_operations": [],
            "errors": []
        }
        
        try:
            await self.setup_browser(task.get("browser", "chromium"))
            site_config = task["site_config"]
            
            # Navigate to product page
            await self.page.goto(site_config["product_urls"][0])
            
            # Add to cart
            await self._add_to_cart()
            results["cart_operations"].append("item_added")
            
            # Navigate to cart
            cart_selectors = [
                'a[href*="cart"]',
                '.cart-link',
                '#cart-button'
            ]
            
            for selector in cart_selectors:
                try:
                    await self.page.click(selector)
                    break
                except:
                    continue
            
            await self.page.wait_for_load_state("networkidle")
            
            # Test quantity update
            quantity_selectors = [
                'input[name*="quantity"]',
                '.quantity-input',
                '[data-testid="quantity"]'
            ]
            
            for selector in quantity_selectors:
                try:
                    await self.page.fill(selector, "2")
                    results["cart_operations"].append("quantity_updated")
                    break
                except:
                    continue
            
            # Test remove item
            remove_selectors = [
                '.remove-item',
                'button[data-action="remove"]',
                '.delete-button'
            ]
            
            for selector in remove_selectors:
                try:
                    await self.page.click(selector)
                    results["cart_operations"].append("item_removed")
                    break
                except:
                    continue
            
            results["success"] = True
            await self.log_task_completion("cart_management", True, results)
            
        except Exception as e:
            results["errors"].append(str(e))
            await self.log_task_completion("cart_management", False, results)
        
        return results
    
    async def _add_to_cart(self) -> None:
        """Add product to cart"""
        add_to_cart_selectors = [
            'button[data-action="add-to-cart"]',
            '.add-to-cart',
            '#add-to-cart-button',
            'button:has-text("Add to Cart")',
            'button:has-text("เพิ่มลงตะกร้า")'
        ]
        
        for selector in add_to_cart_selectors:
            try:
                await self.page.click(selector)
                await self.page.wait_for_timeout(2000)
                return
            except:
                continue
        
        raise Exception("Could not find add to cart button")
    
    async def _fill_shipping_form(self, address_data: Dict[str, str]) -> None:
        """Fill shipping form with test data"""
        form_fields = {
            'input[name*="first_name"], input[name*="firstName"]': address_data["first_name"],
            'input[name*="last_name"], input[name*="lastName"]': address_data["last_name"],
            'input[name*="email"]': address_data["email"],
            'input[name*="phone"]': address_data["phone"],
            'input[name*="address"]': address_data["address"],
            'input[name*="city"]': address_data["city"],
            'input[name*="state"]': address_data["state"],
            'input[name*="zip"], input[name*="postal"]': address_data["zip"]
        }
        
        for selector, value in form_fields.items():
            try:
                await self.page.fill(selector, value)
            except:
                self.logger.warning(f"Could not fill field: {selector}")
    
    async def _fill_payment_form(self, card_data: Dict[str, str]) -> None:
        """Fill payment form with test card data"""
        payment_fields = {
            'input[name*="card_number"], input[name*="cardNumber"]': card_data["number"],
            'input[name*="expiry"], input[name*="exp"]': card_data["expiry"],
            'input[name*="cvv"], input[name*="cvc"]': card_data["cvv"],
            'input[name*="card_name"], input[name*="cardName"]': card_data["name"]
        }
        
        for selector, value in payment_fields.items():
            try:
                await self.page.fill(selector, value)
            except:
                self.logger.warning(f"Could not fill payment field: {selector}")
    
    async def _submit_order(self) -> None:
        """Submit order (test mode only)"""
        submit_selectors = [
            'button[type="submit"]',
            '.submit-order',
            '#place-order',
            'button:has-text("Place Order")',
            'button:has-text("สั่งซื้อ")'
        ]
        
        for selector in submit_selectors:
            try:
                await self.page.click(selector)
                await self.page.wait_for_load_state("networkidle")
                return
            except:
                continue
        
        raise Exception("Could not find submit order button")
    
    async def _test_empty_form_validation(self, results: Dict[str, Any]) -> None:
        """Test empty form validation"""
        try:
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_timeout(1000)
            
            # Check for validation messages
            validation_selectors = [
                '.error-message',
                '.validation-error',
                '.field-error',
                '[data-testid="error"]'
            ]
            
            for selector in validation_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    results["validations_tested"].append("empty_form_validation")
                    break
        except:
            pass
    
    async def _test_invalid_email_validation(self, results: Dict[str, Any]) -> None:
        """Test invalid email validation"""
        try:
            await self.page.fill('input[name*="email"]', "invalid-email")
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_timeout(1000)
            
            # Check for email validation error
            email_error = await self.page.query_selector('.email-error, [data-field="email"] .error')
            if email_error:
                results["validations_tested"].append("invalid_email_validation")
        except:
            pass
    
    async def _test_invalid_card_validation(self, results: Dict[str, Any]) -> None:
        """Test invalid card validation"""
        try:
            await self.page.fill('input[name*="card_number"]', "1234567890123456")
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_timeout(1000)
            
            # Check for card validation error
            card_error = await self.page.query_selector('.card-error, [data-field="card"] .error')
            if card_error:
                results["validations_tested"].append("invalid_card_validation")
        except:
            pass
    
    async def _capture_screenshot(self, results: Dict[str, Any], filename: str) -> None:
        """Capture screenshot on error"""
        try:
            if self.config["testing"]["screenshot_on_failure"]:
                screenshot_path = f"reports/screenshots/{filename}_{int(time.time())}.png"
                await self.page.screenshot(path=screenshot_path)
                results["screenshots"].append(screenshot_path)
                self.logger.info(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {str(e)}")