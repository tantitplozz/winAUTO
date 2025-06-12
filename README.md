# winAUTO - E-commerce Testing Automation Stack

## Overview
Production-ready multi-agent testing framework for e-commerce checkout flows using OpenHands + Dolphin-24B-Venice LLM integration.

## Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Test Agent    │────│  Browser Agent  │────│  Report Agent   │
│   (Orchestrator)│    │  (Playwright)   │    │  (Notifications)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Data Agent    │
                    │ (Test Scenarios)│
                    └─────────────────┘
```

## Features
- ✅ Multi-browser testing (Chrome, Firefox, Safari)
- ✅ Form validation testing
- ✅ Payment flow simulation (test cards only)
- ✅ Performance monitoring
- ✅ Screenshot capture on failures
- ✅ Detailed reporting with Telegram notifications
- ✅ LLM-powered test case generation
- ✅ Auto-retry mechanisms
- ✅ Session isolation

## Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure test environment
cp config/config.example.json config/config.json
# Edit config.json with your test site details

# 3. Run test suite
python main.py --site your-test-site.com --flow checkout

# 4. View reports
open reports/latest_test_report.html
```

## Test Scenarios
- Product search and selection
- Cart management
- Checkout form validation
- Payment processing (test mode)
- Order confirmation
- Error handling
- Performance benchmarks

## Configuration
All settings in `config/config.json`:
- Test site URLs
- Browser configurations
- Test data sets
- Notification settings
- LLM integration settings
