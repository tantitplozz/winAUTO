#!/usr/bin/env python3
"""
Test Orchestrator Agent
Coordinates all testing agents and manages test execution flow
"""

import asyncio
import json
import time
from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent
from .browser_agent import BrowserAgent
from .data_agent import DataAgent
from .report_agent import ReportAgent

class TestOrchestrator(BaseAgent):
    """Main orchestrator for e-commerce testing"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "TestOrchestrator")
        self.browser_agent = None
        self.data_agent = None
        self.report_agent = None
        self.test_results = []
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestrated test suite"""
        test_suite = task.get("test_suite", "full")
        target_site = task.get("target_site")
        
        if test_suite == "full":
            return await self.run_full_test_suite(target_site)
        elif test_suite == "checkout_only":
            return await self.run_checkout_tests(target_site)
        elif test_suite == "validation_only":
            return await self.run_validation_tests(target_site)
        else:
            raise ValueError(f"Unknown test suite: {test_suite}")
    
    async def run_full_test_suite(self, target_site: str) -> Dict[str, Any]:
        """Run complete test suite"""
        self.logger.info(f"Starting full test suite for {target_site}")
        
        suite_results = {
            "suite_name": "full_test_suite",
            "target_site": target_site,
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "duration": 0
            }
        }
        
        start_time = time.time()
        
        try:
            # Initialize agents
            await self._initialize_agents()
            
            # Get site configuration
            site_config = self._get_site_config(target_site)
            if not site_config:
                raise ValueError(f"No configuration found for site: {target_site}")
            
            # Generate test data
            test_data = await self.data_agent.execute({
                "type": "generate_test_data",
                "site_config": site_config
            })
            
            # Run test scenarios
            test_scenarios = [
                {
                    "name": "product_search",
                    "type": "product_search",
                    "browser": "chromium",
                    "site_config": site_config,
                    "search_term": "test product"
                },
                {
                    "name": "cart_management",
                    "type": "cart_management", 
                    "browser": "chromium",
                    "site_config": site_config,
                    "test_data": test_data
                },
                {
                    "name": "form_validation",
                    "type": "form_validation",
                    "browser": "chromium",
                    "site_config": site_config,
                    "test_data": test_data
                },
                {
                    "name": "checkout_flow_chrome",
                    "type": "checkout_flow",
                    "browser": "chromium",
                    "site_config": site_config,
                    "test_data": test_data,
                    "submit_order": False
                },
                {
                    "name": "checkout_flow_firefox",
                    "type": "checkout_flow",
                    "browser": "firefox",
                    "site_config": site_config,
                    "test_data": test_data,
                    "submit_order": False
                }
            ]
            
            # Execute tests with LLM guidance
            for scenario in test_scenarios:
                await self._execute_test_with_llm_guidance(scenario, suite_results)
            
            # Generate performance analysis
            await self._analyze_performance(suite_results)
            
            # Generate final report
            report_result = await self.report_agent.execute({
                "type": "generate_report",
                "test_results": suite_results,
                "include_recommendations": True
            })
            
            suite_results["report_path"] = report_result.get("report_path")
            
        except Exception as e:
            self.logger.error(f"Test suite execution failed: {str(e)}")
            suite_results["error"] = str(e)
        
        finally:
            suite_results["end_time"] = datetime.now().isoformat()
            suite_results["summary"]["duration"] = time.time() - start_time
            
            # Send notifications
            await self._send_notifications(suite_results)
        
        return suite_results
    
    async def run_checkout_tests(self, target_site: str) -> Dict[str, Any]:
        """Run checkout-specific tests"""
        self.logger.info(f"Starting checkout tests for {target_site}")
        
        suite_results = {
            "suite_name": "checkout_tests",
            "target_site": target_site,
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "summary": {"total_tests": 0, "passed": 0, "failed": 0}
        }
        
        try:
            await self._initialize_agents()
            site_config = self._get_site_config(target_site)
            test_data = await self.data_agent.execute({
                "type": "generate_test_data",
                "site_config": site_config
            })
            
            # Checkout tests for different browsers
            browsers = self.config["testing"]["browsers"]
            for browser in browsers:
                scenario = {
                    "name": f"checkout_flow_{browser}",
                    "type": "checkout_flow",
                    "browser": browser,
                    "site_config": site_config,
                    "test_data": test_data,
                    "submit_order": False
                }
                
                await self._execute_test_with_llm_guidance(scenario, suite_results)
        
        except Exception as e:
            self.logger.error(f"Checkout tests failed: {str(e)}")
            suite_results["error"] = str(e)
        
        return suite_results
    
    async def run_validation_tests(self, target_site: str) -> Dict[str, Any]:
        """Run form validation tests"""
        self.logger.info(f"Starting validation tests for {target_site}")
        
        suite_results = {
            "suite_name": "validation_tests",
            "target_site": target_site,
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "summary": {"total_tests": 0, "passed": 0, "failed": 0}
        }
        
        try:
            await self._initialize_agents()
            site_config = self._get_site_config(target_site)
            test_data = await self.data_agent.execute({
                "type": "generate_test_data",
                "site_config": site_config
            })
            
            scenario = {
                "name": "form_validation_comprehensive",
                "type": "form_validation",
                "browser": "chromium",
                "site_config": site_config,
                "test_data": test_data
            }
            
            await self._execute_test_with_llm_guidance(scenario, suite_results)
        
        except Exception as e:
            self.logger.error(f"Validation tests failed: {str(e)}")
            suite_results["error"] = str(e)
        
        return suite_results
    
    async def _initialize_agents(self) -> None:
        """Initialize all required agents"""
        self.browser_agent = BrowserAgent(self.config)
        self.data_agent = DataAgent(self.config)
        self.report_agent = ReportAgent(self.config)
        
        self.logger.info("All agents initialized successfully")
    
    def _get_site_config(self, target_site: str) -> Dict[str, Any]:
        """Get configuration for target site"""
        sites = self.config["testing"]["target_sites"]
        for site in sites:
            if site["name"] == target_site:
                return site
        return None
    
    async def _execute_test_with_llm_guidance(self, scenario: Dict[str, Any], suite_results: Dict[str, Any]) -> None:
        """Execute test with LLM guidance and analysis"""
        test_name = scenario["name"]
        self.logger.info(f"Executing test: {test_name}")
        
        test_result = {
            "name": test_name,
            "type": scenario["type"],
            "browser": scenario.get("browser", "chromium"),
            "start_time": datetime.now().isoformat(),
            "success": False,
            "details": {},
            "llm_analysis": "",
            "recommendations": []
        }
        
        try:
            # Get LLM pre-test analysis
            pre_test_prompt = f"""
            About to execute test: {test_name}
            Test type: {scenario['type']}
            Browser: {scenario.get('browser')}
            Site: {scenario.get('site_config', {}).get('name', 'unknown')}
            
            Provide pre-test analysis and key checkpoints to monitor.
            """
            
            pre_analysis = await self.call_llm(
                pre_test_prompt,
                f"Pre-test analysis for {test_name}"
            )
            
            test_result["pre_analysis"] = pre_analysis
            
            # Execute the test
            async with self.browser_agent as browser:
                result = await browser.execute(scenario)
                test_result["details"] = result
                test_result["success"] = result.get("success", False)
            
            # Get LLM post-test analysis
            post_test_prompt = f"""
            Test completed: {test_name}
            Success: {test_result['success']}
            Results: {json.dumps(result, indent=2)}
            
            Analyze the results and provide:
            1. Performance assessment
            2. Issues identified
            3. Recommendations for improvement
            4. Risk assessment
            """
            
            post_analysis = await self.call_llm(
                post_test_prompt,
                f"Post-test analysis for {test_name}"
            )
            
            test_result["llm_analysis"] = post_analysis
            
            # Update suite summary
            suite_results["summary"]["total_tests"] += 1
            if test_result["success"]:
                suite_results["summary"]["passed"] += 1
            else:
                suite_results["summary"]["failed"] += 1
            
        except Exception as e:
            test_result["error"] = str(e)
            suite_results["summary"]["total_tests"] += 1
            suite_results["summary"]["failed"] += 1
            self.logger.error(f"Test {test_name} failed: {str(e)}")
        
        finally:
            test_result["end_time"] = datetime.now().isoformat()
            suite_results["tests"].append(test_result)
    
    async def _analyze_performance(self, suite_results: Dict[str, Any]) -> None:
        """Analyze overall performance metrics"""
        performance_data = {
            "total_duration": suite_results["summary"]["duration"],
            "success_rate": (suite_results["summary"]["passed"] / 
                           suite_results["summary"]["total_tests"] * 100) if suite_results["summary"]["total_tests"] > 0 else 0,
            "average_test_duration": 0,
            "slowest_tests": [],
            "failed_tests": []
        }
        
        test_durations = []
        for test in suite_results["tests"]:
            if "start_time" in test and "end_time" in test:
                start = datetime.fromisoformat(test["start_time"])
                end = datetime.fromisoformat(test["end_time"])
                duration = (end - start).total_seconds()
                test_durations.append({"name": test["name"], "duration": duration})
                
                if not test["success"]:
                    performance_data["failed_tests"].append(test["name"])
        
        if test_durations:
            performance_data["average_test_duration"] = sum(t["duration"] for t in test_durations) / len(test_durations)
            performance_data["slowest_tests"] = sorted(test_durations, key=lambda x: x["duration"], reverse=True)[:3]
        
        # Get LLM performance analysis
        performance_prompt = f"""
        Performance Analysis Request:
        {json.dumps(performance_data, indent=2)}
        
        Provide insights on:
        1. Overall performance assessment
        2. Bottlenecks identified
        3. Optimization recommendations
        4. Scaling considerations
        """
        
        performance_analysis = await self.call_llm(
            performance_prompt,
            "Performance analysis"
        )
        
        suite_results["performance_analysis"] = {
            "metrics": performance_data,
            "llm_insights": performance_analysis
        }
    
    async def _send_notifications(self, suite_results: Dict[str, Any]) -> None:
        """Send test completion notifications"""
        try:
            if self.config.get("notifications", {}).get("telegram", {}).get("enabled", False):
                await self.report_agent.execute({
                    "type": "send_telegram_notification",
                    "test_results": suite_results
                })
        except Exception as e:
            self.logger.error(f"Failed to send notifications: {str(e)}")