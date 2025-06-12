#!/usr/bin/env python3
"""
Report Agent for E-commerce Testing
Generates reports, sends notifications, and manages test documentation
"""

import json
import os
import time
from typing import Dict, Any, List
from datetime import datetime
from jinja2 import Template
import aiohttp
from .base_agent import BaseAgent

class ReportAgent(BaseAgent):
    """Report generation and notification agent"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "ReportAgent")
        self.report_templates = self._load_report_templates()
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute reporting task"""
        task_type = task.get("type")
        
        if task_type == "generate_report":
            return await self.generate_report(task)
        elif task_type == "send_telegram_notification":
            return await self.send_telegram_notification(task)
        elif task_type == "send_email_notification":
            return await self.send_email_notification(task)
        elif task_type == "generate_performance_report":
            return await self.generate_performance_report(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def generate_report(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        test_results = task["test_results"]
        include_recommendations = task.get("include_recommendations", False)
        
        # Get LLM analysis for report insights
        if include_recommendations:
            llm_prompt = f"""
            Analyze test results and provide comprehensive insights:
            
            Test Summary:
            - Total Tests: {test_results['summary']['total_tests']}
            - Passed: {test_results['summary']['passed']}
            - Failed: {test_results['summary']['failed']}
            - Duration: {test_results['summary'].get('duration', 0):.2f}s
            
            Test Details:
            {json.dumps(test_results.get('tests', []), indent=2)}
            
            Provide:
            1. Executive summary
            2. Critical issues identified
            3. Performance bottlenecks
            4. Security concerns
            5. Recommendations for improvement
            6. Risk assessment
            7. Next steps
            """
            
            llm_insights = await self.call_llm(llm_prompt, "Test report analysis")
            test_results["llm_insights"] = llm_insights
        
        # Generate HTML report
        html_report = await self._generate_html_report(test_results)
        
        # Generate JSON report
        json_report = await self._generate_json_report(test_results)
        
        # Save reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = self.config["reporting"]["output_dir"]
        os.makedirs(report_dir, exist_ok=True)
        os.makedirs(f"{report_dir}/screenshots", exist_ok=True)
        
        html_path = f"{report_dir}/test_report_{timestamp}.html"
        json_path = f"{report_dir}/test_report_{timestamp}.json"
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        # Create symlink to latest report
        latest_html = f"{report_dir}/latest_test_report.html"
        latest_json = f"{report_dir}/latest_test_report.json"
        
        if os.path.exists(latest_html):
            os.remove(latest_html)
        if os.path.exists(latest_json):
            os.remove(latest_json)
        
        os.symlink(os.path.basename(html_path), latest_html)
        os.symlink(os.path.basename(json_path), latest_json)
        
        result = {
            "success": True,
            "html_report_path": html_path,
            "json_report_path": json_path,
            "latest_html_path": latest_html,
            "latest_json_path": latest_json,
            "report_url": f"file://{os.path.abspath(html_path)}"
        }
        
        await self.log_task_completion("generate_report", True, result)
        return result
    
    async def send_telegram_notification(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Send test results via Telegram"""
        test_results = task["test_results"]
        telegram_config = self.config["notifications"]["telegram"]
        
        if not telegram_config.get("enabled", False):
            return {"success": False, "error": "Telegram notifications disabled"}
        
        # Format message
        summary = test_results["summary"]
        success_rate = (summary["passed"] / summary["total_tests"] * 100) if summary["total_tests"] > 0 else 0
        
        status_emoji = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"
        
        message = f"""
{status_emoji} **E-commerce Test Results**

🎯 **Target**: {test_results.get('target_site', 'Unknown')}
📊 **Suite**: {test_results.get('suite_name', 'Unknown')}

📈 **Summary**:
• Total Tests: {summary['total_tests']}
• Passed: {summary['passed']} ✅
• Failed: {summary['failed']} ❌
• Success Rate: {success_rate:.1f}%
• Duration: {summary.get('duration', 0):.1f}s

🔍 **Failed Tests**:
"""
        
        failed_tests = [test for test in test_results.get('tests', []) if not test.get('success', False)]
        if failed_tests:
            for test in failed_tests[:5]:  # Show max 5 failed tests
                message += f"• {test['name']}: {test.get('error', 'Unknown error')}\n"
        else:
            message += "None! 🎉\n"
        
        if test_results.get('llm_insights'):
            message += f"\n🤖 **AI Insights**: {test_results['llm_insights'][:200]}..."
        
        message += f"\n⏰ **Completed**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            url = f"https://api.telegram.org/bot{telegram_config['bot_token']}/sendMessage"
            payload = {
                "chat_id": telegram_config["chat_id"],
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = {"success": True, "message_sent": True}
                    await self.log_task_completion("send_telegram_notification", True, result)
                    return result
                else:
                    error_text = await response.text()
                    result = {"success": False, "error": f"Telegram API error: {response.status} - {error_text}"}
                    await self.log_task_completion("send_telegram_notification", False, result)
                    return result
                    
        except Exception as e:
            result = {"success": False, "error": str(e)}
            await self.log_task_completion("send_telegram_notification", False, result)
            return result
    
    async def send_email_notification(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Send test results via email"""
        # Email implementation would go here
        # For now, return placeholder
        return {"success": False, "error": "Email notifications not implemented"}
    
    async def generate_performance_report(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance-specific report"""
        test_results = task["test_results"]
        
        performance_data = {
            "page_load_times": [],
            "api_response_times": [],
            "error_rates": [],
            "resource_usage": []
        }
        
        # Extract performance metrics from test results
        for test in test_results.get("tests", []):
            if "performance" in test.get("details", {}):
                perf = test["details"]["performance"]
                if "page_load" in perf:
                    performance_data["page_load_times"].append({
                        "test": test["name"],
                        "time": perf["page_load"]
                    })
        
        # Generate performance insights with LLM
        perf_prompt = f"""
        Analyze performance test results:
        {json.dumps(performance_data, indent=2)}
        
        Provide:
        1. Performance bottlenecks
        2. Optimization recommendations
        3. Scalability assessment
        4. Resource usage analysis
        """
        
        performance_insights = await self.call_llm(perf_prompt, "Performance analysis")
        
        result = {
            "success": True,
            "performance_data": performance_data,
            "insights": performance_insights
        }
        
        await self.log_task_completion("generate_performance_report", True, result)
        return result
    
    def _load_report_templates(self) -> Dict[str, str]:
        """Load report templates"""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-commerce Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
        .metric h3 { margin: 0; color: #333; }
        .metric .value { font-size: 2em; font-weight: bold; margin: 10px 0; }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .danger { color: #dc3545; }
        .test-results { margin-top: 30px; }
        .test-item { border: 1px solid #ddd; margin-bottom: 15px; border-radius: 5px; overflow: hidden; }
        .test-header { background: #f8f9fa; padding: 15px; cursor: pointer; }
        .test-details { padding: 15px; display: none; }
        .test-success { border-left: 4px solid #28a745; }
        .test-failed { border-left: 4px solid #dc3545; }
        .llm-insights { background: #e3f2fd; padding: 20px; border-radius: 5px; margin-top: 20px; }
        .performance-chart { margin: 20px 0; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }
        .screenshot { max-width: 100%; height: auto; border: 1px solid #ddd; margin: 10px 0; }
    </style>
    <script>
        function toggleDetails(id) {
            const details = document.getElementById(id);
            details.style.display = details.style.display === 'none' ? 'block' : 'none';
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛒 E-commerce Test Report</h1>
            <p><strong>Target Site:</strong> {{ target_site }}</p>
            <p><strong>Test Suite:</strong> {{ suite_name }}</p>
            <p><strong>Generated:</strong> {{ timestamp }}</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <h3>Total Tests</h3>
                <div class="value">{{ total_tests }}</div>
            </div>
            <div class="metric">
                <h3>Passed</h3>
                <div class="value success">{{ passed }}</div>
            </div>
            <div class="metric">
                <h3>Failed</h3>
                <div class="value danger">{{ failed }}</div>
            </div>
            <div class="metric">
                <h3>Success Rate</h3>
                <div class="value {{ 'success' if success_rate >= 90 else 'warning' if success_rate >= 70 else 'danger' }}">{{ success_rate }}%</div>
            </div>
            <div class="metric">
                <h3>Duration</h3>
                <div class="value">{{ duration }}s</div>
            </div>
        </div>
        
        {% if llm_insights %}
        <div class="llm-insights">
            <h3>🤖 AI Insights & Recommendations</h3>
            <pre>{{ llm_insights }}</pre>
        </div>
        {% endif %}
        
        <div class="test-results">
            <h2>Test Results</h2>
            {% for test in tests %}
            <div class="test-item {{ 'test-success' if test.success else 'test-failed' }}">
                <div class="test-header" onclick="toggleDetails('test-{{ loop.index }}')">
                    <strong>{{ test.name }}</strong>
                    <span style="float: right;">
                        {{ '✅ PASSED' if test.success else '❌ FAILED' }}
                    </span>
                </div>
                <div id="test-{{ loop.index }}" class="test-details">
                    <p><strong>Type:</strong> {{ test.type }}</p>
                    <p><strong>Browser:</strong> {{ test.browser }}</p>
                    <p><strong>Duration:</strong> {{ test.duration }}s</p>
                    
                    {% if test.details %}
                    <h4>Details:</h4>
                    <pre>{{ test.details | tojson(indent=2) }}</pre>
                    {% endif %}
                    
                    {% if test.llm_analysis %}
                    <h4>🤖 AI Analysis:</h4>
                    <pre>{{ test.llm_analysis }}</pre>
                    {% endif %}
                    
                    {% if test.error %}
                    <h4>Error:</h4>
                    <pre style="color: #dc3545;">{{ test.error }}</pre>
                    {% endif %}
                    
                    {% if test.screenshots %}
                    <h4>Screenshots:</h4>
                    {% for screenshot in test.screenshots %}
                    <img src="{{ screenshot }}" alt="Screenshot" class="screenshot">
                    {% endfor %}
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
        
        {% if performance_analysis %}
        <div class="performance-analysis">
            <h2>📊 Performance Analysis</h2>
            <pre>{{ performance_analysis | tojson(indent=2) }}</pre>
        </div>
        {% endif %}
    </div>
</body>
</html>
        """
        
        return {
            "html": html_template
        }
    
    async def _generate_html_report(self, test_results: Dict[str, Any]) -> str:
        """Generate HTML report"""
        template = Template(self.report_templates["html"])
        
        # Calculate additional metrics
        summary = test_results["summary"]
        success_rate = (summary["passed"] / summary["total_tests"] * 100) if summary["total_tests"] > 0 else 0
        
        # Add duration to each test
        for test in test_results.get("tests", []):
            if "start_time" in test and "end_time" in test:
                start = datetime.fromisoformat(test["start_time"])
                end = datetime.fromisoformat(test["end_time"])
                test["duration"] = (end - start).total_seconds()
            else:
                test["duration"] = 0
        
        return template.render(
            target_site=test_results.get("target_site", "Unknown"),
            suite_name=test_results.get("suite_name", "Unknown"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_tests=summary["total_tests"],
            passed=summary["passed"],
            failed=summary["failed"],
            success_rate=f"{success_rate:.1f}",
            duration=f"{summary.get('duration', 0):.1f}",
            tests=test_results.get("tests", []),
            llm_insights=test_results.get("llm_insights", ""),
            performance_analysis=test_results.get("performance_analysis", {})
        )
    
    async def _generate_json_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON report with additional metadata"""
        json_report = test_results.copy()
        json_report["report_metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "generator": "E-commerce Testing Framework",
            "version": "1.0.0",
            "format_version": "1.0"
        }
        
        return json_report