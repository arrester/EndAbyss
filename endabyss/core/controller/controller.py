#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EndAbyss Controller Module
"""

import asyncio
import json
import os
import yaml
from typing import Dict, List, Set, Any, Optional
from urllib.parse import urlparse
from datetime import datetime
import aiohttp
import dns.resolver

from endabyss.core.cli.cli import console, print_status
from endabyss.core.handler.static.crawler import StaticCrawler
from endabyss.core.handler.dynamic.browser import DynamicCrawler
from endabyss.core.handler.dirscan.dirscanner import DirectoryScanner

class EndAbyssController:
    """EndAbyss 메인 컨트롤러"""
    
    def __init__(self, target: str, mode: str = 'static', verbose: int = 0,
                 depth: int = 5, concurrency: int = 10, session: Optional[str] = None,
                 delay: float = 0, random_delay: Optional[str] = None,
                 timeout: int = 5, retry: int = 3, retry_delay: float = 1.0,
                 user_agent: Optional[str] = None, proxy: Optional[str] = None,
                 rate_limit: Optional[float] = None, headless: bool = True,
                 wait_time: float = 3.0, dirscan: bool = False,
                 wordlist: Optional[str] = None, status_codes: Optional[str] = None,
                 exclude_ext: Optional[str] = None, exclude_path: Optional[str] = None,
                 include_ext: Optional[str] = None, include_path: Optional[str] = None,
                 min_params: Optional[int] = None, silent: bool = False):
        self.target = target
        self.mode = mode
        self.verbose = verbose
        self.depth = depth
        self.concurrency = concurrency
        self.session_file = session
        self.delay = delay
        self.random_delay = random_delay
        self.timeout = timeout
        self.retry = retry
        self.retry_delay = retry_delay
        self.user_agent = user_agent
        self.proxy = proxy
        self.rate_limit = rate_limit
        self.headless = headless
        self.wait_time = wait_time
        self.dirscan = dirscan
        self.wordlist = wordlist
        self.status_codes = status_codes
        self.exclude_ext = exclude_ext
        self.exclude_path = exclude_path
        self.include_ext = include_ext
        self.include_path = include_path
        self.min_params = min_params
        self.silent = silent
        
        self.config = self._load_config()
        self.session_data = self._load_session()
        
    def _load_config(self) -> Dict:
        """Load configuration from config.yaml"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config', 'config.yaml'
        )
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
        
    def _load_session(self) -> Optional[Dict]:
        """Load session data from file"""
        if not self.session_file or not os.path.exists(self.session_file):
            return None
            
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip().startswith('{'):
                    return json.loads(content)
                else:
                    return self._parse_netscape_cookies(content)
        except:
            return None
            
    def _parse_netscape_cookies(self, content: str) -> Dict:
        """Parse Netscape format cookie file"""
        cookies = []
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#'):
                parts = line.split('\t')
                if len(parts) >= 7:
                    cookies.append({
                        'name': parts[5],
                        'value': parts[6],
                        'domain': parts[0],
                        'path': parts[2]
                    })
        return {'cookies': cookies} if cookies else None
        
    async def _validate_target(self, target: str) -> Optional[str]:
        """Validate target and return full URL"""
        if target.startswith(('http://', 'https://')):
            return target
            
        parsed = urlparse(f"http://{target}")
        
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5
            resolver.resolve(parsed.netloc, 'A')
        except:
            if self.verbose >= 1:
                print_status(f"DNS resolution failed for {target}", "warning", cli_only=not self.silent)
            return None
            
        async with aiohttp.ClientSession() as session:
            for scheme in ['https', 'http']:
                url = f"{scheme}://{target}"
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status < 500:
                            return url
                except:
                    continue
                    
        return None
        
    def _parse_list(self, value: Optional[str]) -> List[str]:
        """Parse comma-separated list"""
        if not value:
            return []
        return [item.strip() for item in value.split(',') if item.strip()]
        
    def _parse_status_codes(self, value: Optional[str]) -> List[int]:
        """Parse comma-separated status codes"""
        if not value:
            return self.config.get('status_codes', [200, 201, 202, 204, 301, 302, 307, 401, 403])
        return [int(code.strip()) for code in value.split(',') if code.strip().isdigit()]
        
    async def scan(self) -> Dict:
        """Execute scan"""
        url = await self._validate_target(self.target)
        if not url:
            if not self.silent:
                print_status(f"Target {self.target} is not accessible", "error")
            return {'endpoints': [], 'forms': [], 'parameters': []}
            
        if not self.silent:
            print_status(f"Starting scan on {url}", "info")
            
        exclude_extensions = self._parse_list(self.exclude_ext) or self.config.get('exclude_extensions', [])
        exclude_paths = self._parse_list(self.exclude_path) or self.config.get('exclude_paths', [])
        include_extensions = self._parse_list(self.include_ext)
        include_paths = self._parse_list(self.include_path)
        
        if self.mode == 'dynamic':
            crawler = DynamicCrawler(
                url, self.depth, self.concurrency, self.delay, self.random_delay,
                self.wait_time, self.headless, exclude_extensions=exclude_extensions,
                exclude_paths=exclude_paths, include_extensions=include_extensions,
                include_paths=include_paths, min_params=self.min_params,
                verbose=self.verbose, session=self.session_data
            )
        else:
            crawler = StaticCrawler(
                url, self.depth, self.concurrency, self.delay, self.random_delay,
                self.timeout, self.retry, self.retry_delay, self.user_agent,
                self.proxy, self.rate_limit, self.session_data,
                exclude_extensions=exclude_extensions, exclude_paths=exclude_paths,
                include_extensions=include_extensions, include_paths=include_paths,
                min_params=self.min_params, verbose=self.verbose
            )
            
        results = await crawler.crawl()
        
        if self.dirscan:
            if not self.silent:
                print_status("Starting directory scan", "info")
            dir_scanner = DirectoryScanner(
                url, wordlist_file=self.wordlist,
                status_codes=self._parse_status_codes(self.status_codes),
                concurrency=self.concurrency, timeout=self.timeout,
                verbose=self.verbose
            )
            dir_results = await dir_scanner.scan()
            
            for dir_result in dir_results:
                dir_url = dir_result['url']
                if dir_url not in [r['url'] for r in results['endpoints']]:
                    results['endpoints'].append({
                        'url': dir_url,
                        'method': 'GET',
                        'parameters': {},
                        'source': 'dirscan'
                    })
                    
        return results
        
    def get_output_path(self, user_path: str = None) -> str:
        """Generate output file path"""
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M')
        parsed = urlparse(self.target)
        domain = parsed.netloc or self.target.replace('http://', '').replace('https://', '')
        filename = f"endabyss_{domain}_{timestamp}.txt"
        
        if user_path:
            if os.path.isdir(user_path):
                return os.path.join(user_path, filename)
            else:
                return user_path
        else:
            results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'results')
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            return os.path.join(results_dir, filename)
            
    def save_results(self, results: Dict, output_path: str) -> None:
        """Save results to file"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if output_path.endswith('.json'):
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write("EndAbyss - Endpoints and Parameters\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write("Endpoints:\n")
                    for endpoint in results.get('endpoints', []):
                        source = endpoint.get('source', 'crawl')
                        prefix = "[DIRSCAN] " if source == 'dirscan' else ""
                        f.write(f"{prefix}{endpoint['url']}\n")
                    f.write("\n")
                    
                    f.write("Forms:\n")
                    for form in results.get('forms', []):
                        f.write(f"{form['url']} [{form['method']}]\n")
                        for param, value in form.get('parameters', {}).items():
                            f.write(f"  {param}: {value}\n")
                    f.write("\n")
                    
                    f.write("Parameters:\n")
                    for param_data in results.get('parameters', []):
                        url = param_data['url']
                        method = param_data['method']
                        params = param_data.get('parameters', {})
                        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
                        f.write(f"{url}?{param_str} [{method}]\n")
                        
        except Exception as e:
            if not self.silent:
                console.print(f"[bold red][-][/] Error saving results: {str(e)}")
                
    def print_results(self, results: Dict, output_mode: str = None, output_path: str = None) -> None:
        """Print results"""
        if output_mode:
            if output_mode == "url":
                for param_data in results.get('parameters', []):
                    url = param_data['url']
                    params = param_data.get('parameters', {})
                    if params:
                        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
                        print(f"{url}?{param_str}")
                    else:
                        print(url)
            elif output_mode == "endpoint":
                for endpoint in results.get('endpoints', []):
                    print(endpoint['url'])
            elif output_mode == "param":
                for param_data in results.get('parameters', []):
                    params = param_data.get('parameters', {})
                    for param, value in params.items():
                        print(f"{param}={value}")
            elif output_mode == "json":
                print(json.dumps(results, indent=None, ensure_ascii=False))
            return
            
        if not self.silent:
            total_endpoints = len(results.get('endpoints', []))
            total_forms = len(results.get('forms', []))
            total_params = len(results.get('parameters', []))
            
            print_status(f"Found {total_endpoints} endpoints, {total_forms} forms, {total_params} parameter sets", "success")
            
            if results.get('endpoints'):
                print_status("Endpoints Discovered:", "info")
                for endpoint in results['endpoints']:
                    source = endpoint.get('source', 'crawl')
                    prefix = "[DIRSCAN] " if source == 'dirscan' else ""
                    console.print(f"[cyan]{prefix}{endpoint['url']}[/]")
            
            if results.get('forms'):
                print_status("Forms Discovered:", "info")
                for form in results['forms']:
                    url = form['url']
                    method = form.get('method', 'GET')
                    params = form.get('parameters', {})
                    if params:
                        param_str = '&'.join([f"{k}={v}" for k, v in list(params.items())[:3]])
                        if len(params) > 3:
                            param_str += "..."
                        console.print(f"[cyan]{url}?{param_str}[/] [{method}]")
                    else:
                        console.print(f"[cyan]{url}[/] [{method}]")
                    
            if results.get('parameters'):
                print_status("Parameters Discovered:", "info")
                for param_data in results['parameters']:
                    url = param_data['url']
                    params = param_data.get('parameters', {})
                    method = param_data.get('method', 'GET')
                    if params:
                        param_str = '&'.join([f"{k}={v}" for k, v in params.items() if v])
                        if not param_str:
                            param_str = '&'.join([f"{k}=" for k in params.keys()])
                        console.print(f"[cyan]{url}?{param_str}[/] [{method}]")
                    else:
                        console.print(f"[cyan]{url}[/] [{method}]")
                    
            if output_path:
                print_status(f"Results saved to: {output_path}", "success")

