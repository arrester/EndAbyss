#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dynamic browser-based crawler module using Playwright
"""

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Set, Optional
from collections import deque
import asyncio
import random
import time

class DynamicCrawler:
    """Dynamic crawler using Playwright"""
    
    def __init__(self, base_url: str, depth: int = 5, concurrency: int = 10,
                 delay: float = 0, random_delay: Optional[str] = None,
                 wait_time: float = 3.0, headless: bool = True,
                 exclude_extensions: List[str] = None, exclude_paths: List[str] = None,
                 include_extensions: List[str] = None, include_paths: List[str] = None,
                 min_params: Optional[int] = None, verbose: int = 0,
                 session: Optional[Dict] = None):
        self.base_url = base_url.rstrip('/')
        self.base_domain = urlparse(base_url).netloc
        self.depth = depth if depth > 0 else float('inf')
        self.concurrency = concurrency
        self.delay = delay
        self.random_delay = random_delay
        self.wait_time = wait_time
        self.headless = headless
        self.verbose = verbose
        self.session_data = session
        
        self.exclude_extensions = exclude_extensions or []
        self.exclude_paths = exclude_paths or []
        self.include_extensions = include_extensions or []
        self.include_paths = include_paths or []
        self.min_params = min_params
        
        self.visited = set()
        self.queue = deque()
        self.results = {
            'endpoints': [],
            'forms': [],
            'parameters': []
        }
        self.semaphore = asyncio.Semaphore(concurrency)
        
    def _should_exclude(self, url: str) -> bool:
        """Check if URL should be excluded"""
        parsed = urlparse(url)
        
        if parsed.netloc and parsed.netloc != self.base_domain:
            return True
            
        path = parsed.path.lower()
        
        for exclude_path in self.exclude_paths:
            if exclude_path.lower() in path:
                return True
                
        if self.include_paths:
            matched = False
            for include_path in self.include_paths:
                if include_path.lower() in path:
                    matched = True
                    break
            if not matched:
                return True
                
        ext = ""
        if "." in path:
            ext = "." + path.split(".")[-1].lower()
            
        if ext in self.exclude_extensions:
            return True
            
        if self.include_extensions and ext not in self.include_extensions:
            return True
            
        return False
        
    def _get_delay(self) -> float:
        """Calculate delay for next request"""
        if self.random_delay:
            try:
                min_delay, max_delay = map(float, self.random_delay.split('-'))
                return random.uniform(min_delay, max_delay)
            except:
                pass
        return self.delay
        
    async def _extract_from_page(self, page: Page, url: str) -> Dict:
        """Extract endpoints and parameters from page"""
        results = {
            'endpoints': [],
            'forms': [],
            'parameters': []
        }
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=int(self.wait_time * 1000))
            await asyncio.sleep(self.wait_time)
            
            links = await page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        links.push(a.href);
                    });
                    return links;
                }
            """)
            
            forms = await page.evaluate("""
                () => {
                    const forms = [];
                    document.querySelectorAll('form').forEach(form => {
                        const formData = {
                            action: form.action || window.location.href,
                            method: (form.method || 'GET').toUpperCase(),
                            parameters: {}
                        };
                        form.querySelectorAll('input, textarea, select').forEach(input => {
                            if (input.name && input.type !== 'submit' && input.type !== 'button' && input.type !== 'reset') {
                                formData.parameters[input.name] = input.value || '';
                            }
                        });
                        if (Object.keys(formData.parameters).length > 0) {
                            forms.push(formData);
                        }
                    });
                    return forms;
                }
            """)
            
            for link in links:
                if not self._should_exclude(link):
                    parsed = urlparse(link)
                    if parsed.netloc == self.base_domain or not parsed.netloc:
                        full_url = urljoin(self.base_url, link)
                        if full_url not in self.visited:
                            if parsed.query:
                                params = {}
                                for param in parsed.query.split('&'):
                                    if '=' in param:
                                        k, v = param.split('=', 1)
                                        params[k] = v
                                if not self.min_params or len(params) >= self.min_params:
                                    results['parameters'].append({
                                        'url': full_url.split('?')[0],
                                        'method': 'GET',
                                        'parameters': params
                                    })
                            else:
                                results['endpoints'].append({
                                    'url': full_url,
                                    'method': 'GET',
                                    'parameters': {}
                                })
                                
            for form in forms:
                if not self.min_params or len(form['parameters']) >= self.min_params:
                    results['forms'].append(form)
                    results['parameters'].append({
                        'url': form['action'],
                        'method': form['method'],
                        'parameters': form['parameters']
                    })
                    
        except Exception as e:
            if self.verbose >= 1:
                print(f"Error extracting from {url}: {e}")
                
        return results
        
    async def _crawl_page(self, browser: Browser, url: str, current_depth: int):
        """Crawl a single page"""
        if url in self.visited or current_depth > self.depth:
            return
            
        self.visited.add(url)
        
        delay = self._get_delay()
        if delay > 0:
            await asyncio.sleep(delay)
            
        async with self.semaphore:
            context = await browser.new_context()
            if self.session_data:
                if 'cookies' in self.session_data:
                    await context.add_cookies(self.session_data['cookies'])
                    
            page = await context.new_page()
            
            try:
                extracted = await self._extract_from_page(page, url)
                
                for endpoint in extracted['endpoints']:
                    if endpoint['url'] not in self.visited:
                        if current_depth < self.depth:
                            self.queue.append((endpoint['url'], current_depth + 1))
                            
                self.results['endpoints'].extend(extracted['endpoints'])
                self.results['forms'].extend(extracted['forms'])
                self.results['parameters'].extend(extracted['parameters'])
                
            finally:
                await page.close()
                await context.close()
                
    async def crawl(self) -> Dict:
        """Start crawling process"""
        self.queue.append((self.base_url, 0))
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            try:
                tasks = []
                
                while self.queue or tasks:
                    while self.queue and len(tasks) < self.concurrency:
                        url, depth = self.queue.popleft()
                        task = asyncio.create_task(self._crawl_page(browser, url, depth))
                        tasks.append(task)
                        
                    if tasks:
                        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                        tasks = list(pending)
                        for task in done:
                            try:
                                await task
                            except Exception as e:
                                if self.verbose >= 1:
                                    print(f"Task error: {e}")
                                    
            finally:
                await browser.close()
                
        return {
            'endpoints': self.results['endpoints'],
            'forms': self.results['forms'],
            'parameters': self.results['parameters']
        }

