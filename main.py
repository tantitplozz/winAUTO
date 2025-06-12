#!/usr/bin/env python3
"""
E-commerce Testing Framework - Main Entry Point
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from typing import Dict, Any

# Add agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

from agents.test_orchestrator import TestOrchestrator

def load_config(config_path: str = "config/config.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        print("💡 Please copy config/config.example.json to config/config.json and configure it")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration file: {e}")
        sys.exit(1)

def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('reports/test_execution.log')
        ]
    )

async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="E-commerce Testing Framework")
    parser.add_argument("--site", required=True, help="Target site name (from config)")
    parser.add_argument("--flow", choices=["full", "checkout", "validation"], 
                       default="full", help="Test flow to execute")
    parser.add_argument("--config", default="config/config.json", 
                       help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    parser.add_argument("--browsers", nargs="+", 
                       choices=["chromium", "firefox", "webkit"],
                       help="Browsers to test (overrides config)")
    parser.add_argument("--headless", action="store_true", 
                       help="Run browsers in headless mode")
    parser.add_argument("--no-llm", action="store_true",
                       help="Disable LLM integration")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be tested without executing")
    
    args = parser.parse_args()
    
    # Setup logging
    os.makedirs("reports", exist_ok=True)
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.browsers:
        config["testing"]["browsers"] = args.browsers
    if args.headless:
        config["testing"]["headless"] = True
    if args.no_llm:
        config["llm"]["use_dolphin"] = False
    
    # Validate target site
    site_names = [site["name"] for site in config["testing"]["target_sites"]]
    if args.site not in site_names:
        logger.error(f"❌ Site '{args.site}' not found in configuration")
        logger.info(f"💡 Available sites: {', '.join(site_names)}")
        sys.exit(1)
    
    # Show configuration summary
    logger.info("🚀 E-commerce Testing Framework Starting")
    logger.info(f"🎯 Target Site: {args.site}")
    logger.info(f"🔄 Test Flow: {args.flow}")
    logger.info(f"🌐 Browsers: {config['testing']['browsers']}")
    logger.info(f"👁️ Headless: {config['testing']['headless']}")
    logger.info(f"🤖 LLM Integration: {config['llm']['use_dolphin']}")
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No tests will be executed")
        await show_test_plan(config, args.site, args.flow)
        return
    
    # Execute tests
    try:
        async with TestOrchestrator(config) as orchestrator:
            task = {
                "test_suite": args.flow,
                "target_site": args.site
            }
            
            logger.info("▶️ Starting test execution...")
            results = await orchestrator.execute(task)
            
            # Display results summary
            display_results_summary(results, logger)
            
            # Exit with appropriate code
            if results.get("summary", {}).get("failed", 0) > 0:
                sys.exit(1)
            else:
                sys.exit(0)
                
    except KeyboardInterrupt:
        logger.info("⏹️ Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Test execution failed: {str(e)}")
        sys.exit(1)

async def show_test_plan(config: Dict[str, Any], site: str, flow: str) -> None:
    """Show what tests would be executed in dry run mode"""
    logger = logging.getLogger(__name__)
    
    site_config = None
    for s in config["testing"]["target_sites"]:
        if s["name"] == site:
            site_config = s
            break
    
    if not site_config:
        return
    
    logger.info("📋 TEST EXECUTION PLAN")
    logger.info("=" * 50)
    logger.info(f"Site: {site_config['name']}")
    logger.info(f"Base URL: {site_config['base_url']}")
    logger.info(f"Checkout URL: {site_config['checkout_url']}")
    logger.info(f"Product URLs: {len(site_config.get('product_urls', []))} configured")
    
    if flow == "full":
        tests = [
            "Product Search Test",
            "Cart Management Test", 
            "Form Validation Test",
            "Checkout Flow Test (Chrome)",
            "Checkout Flow Test (Firefox)",
            "Performance Analysis",
            "Report Generation"
        ]
    elif flow == "checkout":
        tests = [
            "Checkout Flow Test (Chrome)",
            "Checkout Flow Test (Firefox)",
            "Checkout Flow Test (Safari)",
            "Report Generation"
        ]
    elif flow == "validation":
        tests = [
            "Form Validation Test",
            "Invalid Data Test",
            "Edge Case Test",
            "Report Generation"
        ]
    
    logger.info("\n🧪 TESTS TO EXECUTE:")
    for i, test in enumerate(tests, 1):
        logger.info(f"  {i}. {test}")
    
    logger.info(f"\n🌐 BROWSERS: {', '.join(config['testing']['browsers'])}")
    logger.info(f"🤖 LLM INTEGRATION: {'Enabled' if config['llm']['use_dolphin'] else 'Disabled'}")
    logger.info(f"📊 NOTIFICATIONS: {'Enabled' if config['notifications']['telegram']['enabled'] else 'Disabled'}")

def display_results_summary(results: Dict[str, Any], logger: logging.Logger) -> None:
    """Display test results summary"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST EXECUTION SUMMARY")
    logger.info("=" * 60)
    
    summary = results.get("summary", {})
    total = summary.get("total_tests", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    duration = summary.get("duration", 0)
    
    success_rate = (passed / total * 100) if total > 0 else 0
    
    logger.info(f"🎯 Target Site: {results.get('target_site', 'Unknown')}")
    logger.info(f"📋 Test Suite: {results.get('suite_name', 'Unknown')}")
    logger.info(f"⏱️ Duration: {duration:.1f} seconds")
    logger.info(f"📈 Total Tests: {total}")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📊 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        logger.info("🎉 EXCELLENT! All tests passed successfully")
    elif success_rate >= 70:
        logger.info("⚠️ GOOD with some issues to address")
    else:
        logger.info("🚨 NEEDS ATTENTION - Multiple test failures")
    
    # Show failed tests
    if failed > 0:
        logger.info("\n❌ FAILED TESTS:")
        for test in results.get("tests", []):
            if not test.get("success", False):
                logger.info(f"  • {test['name']}: {test.get('error', 'Unknown error')}")
    
    # Show report location
    if "report_path" in results:
        logger.info(f"\n📄 Detailed report: {results['report_path']}")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())