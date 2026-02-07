#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Directory scanner module
"""

import asyncio
import aiohttp
from urllib.parse import urljoin
from typing import List, Set, Optional, Dict
import os

class DirectoryScanner:
    """Directory scanner using wordlist"""
    
    def __init__(self, base_url: str, wordlist: List[str] = None,
                 wordlist_file: Optional[str] = None, status_codes: List[int] = None,
                 concurrency: int = 10, timeout: int = 5, verbose: int = 0):
        self.base_url = base_url.rstrip('/')
        self.wordlist = wordlist or []
        self.status_codes = status_codes or [200, 201, 202, 204, 301, 302, 307, 401, 403]
        self.concurrency = concurrency
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.verbose = verbose
        
        if wordlist_file:
            wordlist_path = wordlist_file
            if not os.path.isabs(wordlist_path):
                wordlist_path = os.path.join(os.getcwd(), wordlist_path)
            
            if os.path.exists(wordlist_path):
                try:
                    with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                        self.wordlist.extend([line.strip() for line in f if line.strip()])
                except Exception as e:
                    if self.verbose >= 1:
                        print(f"Error reading wordlist file {wordlist_path}: {e}")
            else:
                if self.verbose >= 1:
                    print(f"Wordlist file not found: {wordlist_path}")
                
        if not self.wordlist:
            self.wordlist = self._get_default_wordlist()
            
        self.semaphore = asyncio.Semaphore(concurrency)
        self.results = []
        
    def _get_default_wordlist(self) -> List[str]:
        """Get default wordlist"""
        return [
            'admin', 'administrator', 'api', 'app', 'assets', 'backup', 'bin',
            'config', 'css', 'data', 'db', 'dev', 'doc', 'docs', 'download',
            'downloads', 'files', 'images', 'img', 'include', 'includes', 'js',
            'lib', 'libs', 'login', 'logs', 'mail', 'media', 'old', 'php',
            'private', 'public', 'res', 'resources', 'scripts', 'secure',
            'server', 'src', 'static', 'store', 'temp', 'test', 'tests',
            'tmp', 'upload', 'uploads', 'web', 'web-inf', 'www', 'xml'
        ]
        
    async def _check_path(self, session: aiohttp.ClientSession, path: str) -> Optional[Dict]:
        """Check if path exists"""
        url = urljoin(self.base_url, path)
        
        try:
            async with self.semaphore:
                async with session.head(url, allow_redirects=True) as response:
                    if response.status in self.status_codes:
                        return {
                            'url': url,
                            'status': response.status,
                            'source': 'dirscan'
                        }
        except:
            pass
            
        try:
            async with self.semaphore:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status in self.status_codes:
                        return {
                            'url': url,
                            'status': response.status,
                            'source': 'dirscan'
                        }
        except Exception as e:
            if self.verbose >= 2:
                print(f"Error checking {url}: {e}")
                
        return None
        
    async def scan(self) -> List[Dict]:
        """Start directory scanning"""
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(timeout=self.timeout, connector=connector) as session:
            tasks = [self._check_path(session, word) for word in self.wordlist]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict) and result:
                    self.results.append(result)
                elif isinstance(result, Exception) and self.verbose >= 2:
                    print(f"Scan error: {result}")
                    
        return self.results

