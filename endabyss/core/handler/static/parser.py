#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Static HTML parser module
"""

from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from typing import List, Dict, Set, Tuple
import re

class StaticParser:
    """Parser for static HTML content"""
    
    def __init__(self, base_url: str, exclude_extensions: List[str] = None, 
                 exclude_paths: List[str] = None, include_extensions: List[str] = None,
                 include_paths: List[str] = None):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.exclude_extensions = exclude_extensions or []
        self.exclude_paths = exclude_paths or []
        self.include_extensions = include_extensions or []
        self.include_paths = include_paths or []
        
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
        
    def parse_html(self, html_content: str, current_url: str) -> Dict:
        """Parse HTML content and extract endpoints and parameters
        
        Returns:
            Dict with keys: 'endpoints', 'forms', 'js_files'
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        results = {
            'endpoints': set(),
            'forms': [],
            'js_files': set()
        }
        
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            if href.startswith('javascript:') or href.startswith('mailto:') or href.startswith('#'):
                continue
            full_url = urljoin(current_url, href)
            
            if not self._should_exclude(full_url):
                results['endpoints'].add(full_url)
        
        for tag in soup.find_all(attrs={'onclick': True}):
            onclick = tag.get('onclick', '')
            urls = self._extract_urls_from_js(onclick, current_url)
            for url in urls:
                if not self._should_exclude(url):
                    results['endpoints'].add(url)
        
        for tag in soup.find_all(['link', 'script', 'img'], src=True):
            src = tag.get('src') or tag.get('href')
            if src:
                full_url = urljoin(current_url, src)
                if tag.name == 'script' and full_url.endswith('.js'):
                    results['js_files'].add(full_url)
                elif not self._should_exclude(full_url):
                    results['endpoints'].add(full_url)
        
        for script_tag in soup.find_all('script'):
            if script_tag.string:
                urls = self._extract_urls_from_js(script_tag.string, current_url)
                for url in urls:
                    parsed_url = urlparse(url)
                    if parsed_url.netloc == self.base_domain or not parsed_url.netloc:
                        if not self._should_exclude(url):
                            results['endpoints'].add(url)
                    
        for tag in soup.find_all(attrs={'data-href': True}):
            href = tag.get('data-href')
            full_url = urljoin(current_url, href)
            if not self._should_exclude(full_url):
                results['endpoints'].add(full_url)
        
        for tag in soup.find_all(attrs={'data-url': True}):
            href = tag.get('data-url')
            full_url = urljoin(current_url, href)
            if not self._should_exclude(full_url):
                results['endpoints'].add(full_url)

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment_endpoints, comment_forms = self._parse_html_comment(str(comment), current_url)
            for url in comment_endpoints:
                if not self._should_exclude(url):
                    results['endpoints'].add(url)
            for form_data in comment_forms:
                results['forms'].append(form_data)

        for form in soup.find_all('form'):
            form_data = self._parse_form(form, current_url)
            if form_data:
                results['forms'].append(form_data)
                
        return {
            'endpoints': list(results['endpoints']),
            'forms': results['forms'],
            'js_files': list(results['js_files'])
        }
    
    def _parse_html_comment(self, comment_text: str, current_url: str):
        """Parse HTML comment and extract endpoints and forms"""
        endpoints = set()
        forms = []

        try:
            comment_soup = BeautifulSoup(comment_text, 'html.parser')

            for tag in comment_soup.find_all('a', href=True):
                href = tag['href']
                if href.startswith('javascript:') or href.startswith('mailto:') or href.startswith('#'):
                    continue
                full_url = urljoin(current_url, href)
                endpoints.add(full_url)

            for tag in comment_soup.find_all(attrs={'onclick': True}):
                onclick = tag.get('onclick', '')
                urls = self._extract_urls_from_js(onclick, current_url)
                endpoints.update(urls)

            for tag in comment_soup.find_all(True):
                for attr in ('href', 'src', 'action', 'data-href', 'data-url'):
                    val = tag.get(attr)
                    if val and not val.startswith(('javascript:', 'mailto:', '#')):
                        full_url = urljoin(current_url, val)
                        endpoints.add(full_url)

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
                        full_url = urljoin(current_url, url)
                        endpoints.add(full_url)

            for form_tag in comment_soup.find_all('form'):
                form_data = self._parse_form(form_tag, current_url)
                if form_data:
                    forms.append(form_data)

        except Exception:
            pass

        return list(endpoints), forms

    def _extract_urls_from_js(self, js_content: str, base_url: str) -> List[str]:
        """Extract URLs from JavaScript code"""
        urls = set()
        
        url_patterns = [
            r'["\']([^"\']*\.php[^"\']*\?[^"\']*)["\']',
            r'["\']([^"\']*\.asp[^"\']*\?[^"\']*)["\']',
            r'["\']([^"\']*\.jsp[^"\']*\?[^"\']*)["\']',
            r'["\']([^"\']*\.aspx[^"\']*\?[^"\']*)["\']',
            r'["\']([^"\']*/\?[^"\']*)["\']',
            r'["\']([^"\']*\?[^"\']*=[^"\']*)["\']',
            r'window\.open\(["\']([^"\']+)["\']',
            r'window\.open\(["\']([^"\']*\?[^"\']*)["\']',
            r'href\s*=\s*["\']([^"\']+)["\']',
            r'src\s*=\s*["\']([^"\']+)["\']',
            r'action\s*=\s*["\']([^"\']+)["\']',
            r'url\s*[:=]\s*["\']([^"\']+)["\']',
            r'["\'](https?://[^"\']+)["\']',
            r'["\'](/[^"\']*\?[^"\']*)["\']',
            r'["\']([^"\']*\.php[^"\']*)["\']',
            r'["\']([^"\']*\.asp[^"\']*)["\']',
            r'["\']([^"\']*\.jsp[^"\']*)["\']',
            r'["\']([^"\']*\.aspx[^"\']*)["\']',
        ]
        
        for pattern in url_patterns:
            for match in re.finditer(pattern, js_content, re.IGNORECASE):
                url = match.group(1)
                if url:
                    if '?' in url or url.startswith('http') or url.startswith('/') or '.' in url:
                        full_url = urljoin(base_url, url)
                        urls.add(full_url)
        
        return list(urls)
        
    def _parse_form(self, form_tag, base_url: str) -> Dict:
        """Parse form tag and extract parameters"""
        action = form_tag.get('action', '')
        method = form_tag.get('method', 'GET').upper()
        
        if not action:
            action = base_url
        else:
            action = urljoin(base_url, action)
            
        parsed_action = urlparse(action)
        base_action_url = f"{parsed_action.scheme}://{parsed_action.netloc}{parsed_action.path}"
        
        parameters = {}
        
        if parsed_action.query:
            existing_params = parse_qs(parsed_action.query)
            for k, v in existing_params.items():
                parameters[k] = v[0] if len(v) == 1 else v
        
        for input_tag in form_tag.find_all(['input', 'textarea', 'select']):
            name = input_tag.get('name')
            if not name:
                continue
                
            input_type = input_tag.get('type', 'text').lower()
            
            if input_type in ['submit', 'button', 'reset', 'image', 'hidden']:
                continue
                
            value = input_tag.get('value', '')
            
            if input_tag.name == 'select':
                option = input_tag.find('option', selected=True)
                if option:
                    value = option.get('value', '')
                else:
                    first_option = input_tag.find('option')
                    if first_option:
                        value = first_option.get('value', '')
                        
            if input_tag.name == 'textarea' and not value:
                value = ''
                    
            parameters[name] = value
            
        return {
            'url': base_action_url,
            'method': method,
            'parameters': parameters,
            'original_action': action
        }
        
    def extract_get_parameters(self, url: str) -> Dict:
        """Extract GET parameters from URL"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        return {
            'url': f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
            'method': 'GET',
            'parameters': {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        }
        
    def extract_api_endpoints(self, content: str) -> List[str]:
        """Extract API endpoints from JSON responses or API patterns"""
        endpoints = set()
        
        api_patterns = [
            r'/api/[^"\')\s]+',
            r'/v\d+/[^"\')\s]+',
            r'/rest/[^"\')\s]+',
            r'/graphql[^"\')\s]*',
        ]
        
        for pattern in api_patterns:
            for match in re.finditer(pattern, content):
                endpoint = match.group(0).rstrip('.,;)\'"')
                if not self._should_exclude(endpoint):
                    endpoints.add(urljoin(self.base_url, endpoint))
                    
        return list(endpoints)

