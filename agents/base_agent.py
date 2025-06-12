#!/usr/bin/env python3
"""
Base Agent Class for E-commerce Testing Framework
"""

import asyncio
import logging
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import aiohttp

class BaseAgent(ABC):
    """Base class for all testing agents"""
    
    def __init__(self, config: Dict[str, Any], agent_name: str):
        self.config = config
        self.agent_name = agent_name
        self.logger = self._setup_logger()
        self.session = None
        self.start_time = None
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_runtime": 0,
            "errors": []
        }
        
    def _setup_logger(self) -> logging.Logger:
        """Setup agent-specific logger"""
        logger = logging.getLogger(f"{self.agent_name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.agent_name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        self.start_time = time.time()
        self.logger.info(f"{self.agent_name} agent started")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        
        self.metrics["total_runtime"] = time.time() - self.start_time
        self.logger.info(f"{self.agent_name} agent stopped. Runtime: {self.metrics['total_runtime']:.2f}s")
        
        if exc_type:
            self.logger.error(f"Agent exited with exception: {exc_type.__name__}: {exc_val}")
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent-specific task"""
        pass
    
    async def retry_on_failure(self, func, *args, max_retries: int = 3, **kwargs) -> Any:
        """Retry mechanism for failed operations"""
        for attempt in range(max_retries):
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    self.metrics["tasks_failed"] += 1
                    self.metrics["errors"].append({
                        "timestamp": datetime.now().isoformat(),
                        "function": func.__name__,
                        "error": str(e),
                        "attempt": attempt + 1
                    })
                    raise e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def log_task_completion(self, task_name: str, success: bool, details: Dict[str, Any] = None):
        """Log task completion with metrics"""
        if success:
            self.metrics["tasks_completed"] += 1
            self.logger.info(f"Task '{task_name}' completed successfully")
        else:
            self.metrics["tasks_failed"] += 1
            self.logger.error(f"Task '{task_name}' failed")
        
        if details:
            self.logger.debug(f"Task details: {json.dumps(details, indent=2)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        return {
            "agent_name": self.agent_name,
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    async def call_llm(self, prompt: str, context: str = "") -> str:
        """Call Dolphin LLM for intelligent decision making"""
        if not self.config.get("llm", {}).get("use_dolphin", False):
            return ""
        
        try:
            llm_config = self.config["llm"]
            url = f"{llm_config['api_url']}/api/generate"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {llm_config['api_key']}"
            }
            
            system_prompt = f"""You are an E-commerce Testing AI Agent specialized in {self.agent_name}.
Context: {context}
Task: Analyze the situation and provide actionable testing recommendations.
Output: JSON format with specific actions, validations, and expected results."""
            
            full_prompt = f"{system_prompt}\n\nUser Query: {prompt}\nAssistant:"
            
            payload = {
                "model": llm_config["model"],
                "prompt": full_prompt,
                "stream": False
            }
            
            timeout = aiohttp.ClientTimeout(total=llm_config.get("timeout", 60))
            
            async with self.session.post(url, json=payload, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "")
                else:
                    self.logger.error(f"LLM API error: {response.status}")
                    return ""
                    
        except Exception as e:
            self.logger.error(f"LLM call failed: {str(e)}")
            return ""