#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Static crawler module
"""

import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict, Optional
from collections import deque
import random
import time

from endabyss.core.handler.static.parser import StaticParser
from endabyss.core.handler.js.linkfinder import extract_endpoints_from_js

class StaticCrawler:
    """Static crawler for endpoint discovery"""
    
    def __init__(self, base_url: str, depth: int = 5, concurrency: int = 10,
                 delay: float = 0, random_delay: Optional[str] = None,
                 timeout: int = 5, retry: int = 3, retry_delay: float = 1.0,
                 user_agent: Optional[str] = None, proxy: Optional[str] = None,
                 rate_limit: Optional[float] = None, session: Optional[Dict] = None,
                 exclude_extensions: List[str] = None, exclude_paths: List[str] = None,
                 include_extensions: List[str] = None, include_paths: List[str] = None,
                 min_params: Optional[int] = None, verbose: int = 0):
        self.base_url = base_url.rstrip('/')
        self.base_domain = urlparse(base_url).netloc
        self.depth = depth if depth > 0 else float('inf')
        self.concurrency = concurrency
        self.delay = delay
        self.random_delay = random_delay
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retry = retry
        self.retry_delay = retry_delay
        self.user_agent = user_agent
        self.proxy = proxy
        self.rate_limit = rate_limit
        self.session_data = session
        self.verbose = verbose
        self.min_params = min_params
        
        self.parser = StaticParser(
            base_url, exclude_extensions, exclude_paths,
            include_extensions, include_paths
        )
        
        self.visited = set()
        self.queue = deque()
        self.results = {
            'endpoints': [],
            'forms': [],
            'parameters': []
        }
        self.semaphore = asyncio.Semaphore(concurrency)
        self.last_request_time = 0
        
    def _get_delay(self) -> float:
        """Calculate delay for next request"""
        if self.random_delay:
            try:
                min_delay, max_delay = map(float, self.random_delay.split('-'))
                return random.uniform(min_delay, max_delay)
            except ValueError:
                if self.verbose >= 1:
                    print(f"Invalid random-delay format: {self.random_delay}")
        return self.delay
        
    async def _rate_limit_wait(self):
        """Wait if rate limit is set"""
        if self.rate_limit:
            elapsed = time.time() - self.last_request_time
            min_interval = 1.0 / self.rate_limit
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        self.last_request_time = time.time()
        
    def _create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session with headers and cookies"""
        headers = {
            'User-Agent': self.user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        cookies = {}
        if self.session_data:
            if isinstance(self.session_data, dict):
                if 'cookies' in self.session_data:
                    cookies = {c['name']: c['value'] for c in self.session_data['cookies']}
                if 'headers' in self.session_data:
                    headers.update(self.session_data['headers'])
        
        connector = aiohttp.TCPConnector(limit=self.concurrency)
        return aiohttp.ClientSession(
            headers=headers,
            cookies=cookies,
            timeout=self.timeout,
            connector=connector
        )
        
    async def _fetch_url(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch URL with retry logic"""
        for attempt in range(self.retry):
            try:
                await self._rate_limit_wait()
                
                async with self.semaphore:
                    async with session.get(url, proxy=self.proxy) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status in [301, 302, 307, 308]:
                            location = response.headers.get('Location')
                            if location:
                                return await self._fetch_url(session, urljoin(url, location))
            except Exception as e:
                if self.verbose >= 2:
                    print(f"Error fetching {url} (attempt {attempt + 1}/{self.retry}): {e}")
                if attempt < self.retry - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    return None
        return None
        
    async def _crawl_page(self, session: aiohttp.ClientSession, url: str, current_depth: int):
        """Crawl a single page"""
        if url in self.visited or current_depth > self.depth:
            return
            
        self.visited.add(url)
        
        delay = self._get_delay()
        if delay > 0:
            await asyncio.sleep(delay)
            
        content = await self._fetch_url(session, url)
        if not content:
            return
            
        parsed = self.parser.parse_html(content, url)
        
        for endpoint in parsed['endpoints']:
            parsed_url = urlparse(endpoint)
            if parsed_url.netloc and parsed_url.netloc != self.base_domain:
                continue
                
            normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            
            get_params = self.parser.extract_get_parameters(endpoint)
            if get_params['parameters']:
                if not self.min_params or len(get_params['parameters']) >= self.min_params:
                    param_exists = any(
                        p['url'] == get_params['url'] and 
                        p['method'] == get_params['method'] and
                        p.get('parameters') == get_params.get('parameters')
                        for p in self.results['parameters']
                    )
                    if not param_exists:
                        self.results['parameters'].append(get_params)
            
            if normalized_url not in self.visited:
                if normalized_url not in [e['url'] for e in self.results['endpoints']]:
                    self.results['endpoints'].append({
                        'url': normalized_url,
                        'method': 'GET',
                        'parameters': {}
                    })
                if current_depth < self.depth:
                    self.queue.append((normalized_url, current_depth + 1))
                        
        for form in parsed['forms']:
            if form:
                form_exists = any(f['url'] == form['url'] and f['method'] == form['method'] 
                                for f in self.results['forms'])
                if not form_exists:
                    self.results['forms'].append(form)
                
                form_params = form.get('parameters', {})
                
                if form_params:
                    if not self.min_params or len(form_params) >= self.min_params:
                        param_exists = any(
                            p['url'] == form['url'] and 
                            p['method'] == form['method'] and
                            p.get('parameters') == form_params
                            for p in self.results['parameters']
                        )
                        if not param_exists:
                            self.results['parameters'].append(form)
                
                original_action = form.get('original_action', '')
                if original_action:
                    parsed_original = urlparse(original_action)
                    if parsed_original.query:
                        get_params_from_action = self.parser.extract_get_parameters(original_action)
                        if get_params_from_action['parameters']:
                            if not self.min_params or len(get_params_from_action['parameters']) >= self.min_params:
                                param_exists = any(
                                    p['url'] == get_params_from_action['url'] and 
                                    p['method'] == 'GET' and
                                    p.get('parameters') == get_params_from_action.get('parameters')
                                    for p in self.results['parameters']
                                )
                                if not param_exists:
                                    self.results['parameters'].append(get_params_from_action)
                                    if self.verbose >= 2:
                                        print(f"Added GET params from form action: {get_params_from_action}")
                
        for js_file in parsed['js_files']:
            if js_file not in self.visited:
                js_content = await self._fetch_url(session, js_file)
                if js_content:
                    js_endpoints = extract_endpoints_from_js(js_content, self.base_url)
                    for js_endpoint in js_endpoints:
                        parsed_js = urlparse(js_endpoint)
                        if parsed_js.netloc == self.base_domain or not parsed_js.netloc:
                            full_js_url = urljoin(self.base_url, js_endpoint)
                            if full_js_url not in self.visited:
                                get_params = self.parser.extract_get_parameters(full_js_url)
                                if get_params['parameters']:
                                    if not self.min_params or len(get_params['parameters']) >= self.min_params:
                                        if get_params not in self.results['parameters']:
                                            self.results['parameters'].append(get_params)
                                else:
                                    normalized_url = f"{parsed_js.scheme}://{parsed_js.netloc}{parsed_js.path}"
                                    if normalized_url not in [e['url'] for e in self.results['endpoints']]:
                                        if current_depth < self.depth:
                                            self.queue.append((normalized_url, current_depth + 1))
                                        self.results['endpoints'].append({
                                            'url': normalized_url,
                                            'method': 'GET',
                                            'parameters': {}
                                        })
                                    
    async def crawl(self) -> Dict:
        """Start crawling process"""
        self.queue.append((self.base_url, 0))
        
        async with self._create_session() as session:
            tasks = []
            
            while self.queue or tasks:
                while self.queue and len(tasks) < self.concurrency:
                    url, depth = self.queue.popleft()
                    task = asyncio.create_task(self._crawl_page(session, url, depth))
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
                                
        return {
            'endpoints': self.results['endpoints'],
            'forms': self.results['forms'],
            'parameters': self.results['parameters']
        }

