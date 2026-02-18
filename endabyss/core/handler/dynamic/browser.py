#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dynamic browser-based crawler module using Playwright
"""

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Set, Optional
from collections import deque
from bs4 import BeautifulSoup, Comment
import asyncio
import random
import time
import re

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
        
    def _parse_html_comments(self, html_content: str, current_url: str):
        """Parse HTML comments and extract endpoints and forms"""
        endpoints = set()
        forms = []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment_text = str(comment)
                try:
                    comment_soup = BeautifulSoup(comment_text, 'html.parser')

                    for tag in comment_soup.find_all('a', href=True):
                        href = tag['href']
                        if href.startswith(('javascript:', 'mailto:', '#')):
                            continue
                        endpoints.add(urljoin(current_url, href))

                    for tag in comment_soup.find_all(True):
                        for attr in ('href', 'src', 'action', 'data-href', 'data-url'):
                            val = tag.get(attr)
                            if val and not val.startswith(('javascript:', 'mailto:', '#')):
                                endpoints.add(urljoin(current_url, val))

                    js_patterns = [
                        r'location\.href\s*=\s*["\']([^"\']+)["\']',
                        r'location\.assign\s*\(\s*["\']([^"\']+)["\']',
                        r'location\.replace\s*\(\s*["\']([^"\']+)["\']',
                        r'window\.open\s*\(\s*["\']([^"\']+)["\']',
                        r'window\.location\s*=\s*["\']([^"\']+)["\']',
                    ]
                    for pattern in js_patterns:
                        for match in re.finditer(pattern, comment_text, re.IGNORECASE):
                            url = match.group(1)
                            if url:
                                endpoints.add(urljoin(current_url, url))

                    for form_tag in comment_soup.find_all('form'):
                        action = form_tag.get('action', '') or current_url
                        method = (form_tag.get('method', 'GET') or 'GET').upper()
                        action_url = urljoin(current_url, action)
                        parameters = {}
                        for input_tag in form_tag.find_all(['input', 'textarea', 'select']):
                            name = input_tag.get('name')
                            if not name:
                                continue
                            input_type = input_tag.get('type', 'text').lower()
                            if input_type in ['submit', 'button', 'reset', 'image']:
                                continue
                            parameters[name] = input_tag.get('value', '')
                        if parameters:
                            forms.append({
                                'url': action_url,
                                'method': method,
                                'parameters': parameters
                            })
                except Exception:
                    pass
        except Exception:
            pass

        return list(endpoints), forms

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
                            url: form.action || window.location.href,
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
                        'url': form['url'],
                        'method': form['method'],
                        'parameters': form['parameters']
                    })

            raw_html = await page.content()
            comment_endpoints, comment_forms = self._parse_html_comments(raw_html, url)
            for ep_url in comment_endpoints:
                if not self._should_exclude(ep_url):
                    parsed_ep = urlparse(ep_url)
                    if parsed_ep.netloc == self.base_domain or not parsed_ep.netloc:
                        full_ep = urljoin(self.base_url, ep_url)
                        if parsed_ep.query:
                            params = {}
                            for param in parsed_ep.query.split('&'):
                                if '=' in param:
                                    k, v = param.split('=', 1)
                                    params[k] = v
                            if not self.min_params or len(params) >= self.min_params:
                                results['parameters'].append({
                                    'url': full_ep.split('?')[0],
                                    'method': 'GET',
                                    'parameters': params
                                })
                        else:
                            results['endpoints'].append({
                                'url': full_ep,
                                'method': 'GET',
                                'parameters': {}
                            })
            for form_data in comment_forms:
                if not self.min_params or len(form_data.get('parameters', {})) >= self.min_params:
                    results['forms'].append(form_data)
                    results['parameters'].append({
                        'url': form_data['url'],
                        'method': form_data['method'],
                        'parameters': form_data.get('parameters', {})
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
            context = await browser.new_context(ignore_https_errors=True)
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

