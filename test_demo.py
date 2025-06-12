#!/usr/bin/env python3
"""
Quick Demo Test for E-commerce Testing Framework
"""

import asyncio
import json
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from agents.test_orchestrator import TestOrchestrator

async def run_demo():
    """Run a quick demo test"""
    print("🚀 E-commerce Testing Framework - Demo")
    print("=" * 50)
    
    # Load config
    with open("config/config.json", "r") as f:
        config = json.load(f)
    
    print(f"🎯 Target: {config['testing']['target_sites'][0]['name']}")
    print(f"🤖 LLM Integration: {config['llm']['use_dolphin']}")
    print(f"🌐 Browsers: {', '.join(config['testing']['browsers'])}")
    print("=" * 50)
    
    try:
        async with TestOrchestrator(config) as orchestrator:
            # Run a simple validation test
            task = {
                "test_suite": "validation",
                "target_site": "demo-store"
            }
            
            print("▶️ Starting validation tests...")
            results = await orchestrator.execute(task)
            
            # Display results
            summary = results.get("summary", {})
            print("\n📊 RESULTS:")
            print(f"✅ Passed: {summary.get('passed', 0)}")
            print(f"❌ Failed: {summary.get('failed', 0)}")
            print(f"⏱️ Duration: {summary.get('duration', 0):.1f}s")
            
            if results.get("report_path"):
                print(f"📄 Report: {results['report_path']}")
            
            return results.get("summary", {}).get("failed", 0) == 0
            
    except Exception as e:
        print(f"💥 Demo failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_demo())
    sys.exit(0 if success else 1)