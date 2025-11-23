#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JavaScript endpoint finder module (based on LinkFinder)
"""

import re
try:
    import jsbeautifier
except ImportError:
    jsbeautifier = None

regex_str = r"""

  (?:"|')                               # Start newline delimiter

  (
    ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
    [^"'/]{1,}\.                        # Match a domainname (any character + dot)
    [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path

    |

    ((?:/|\.\./|\./)                    # Start with /,../,./
    [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
    [^"'><,;|()]{1,})                   # Rest of the characters can't be

    |

    ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
    [a-zA-Z0-9_\-/.]{1,}                # Resource name
    \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters

    |

    ([a-zA-Z0-9_\-/]{1,}/               # REST API (no extension) with /
    [a-zA-Z0-9_\-/]{3,}                 # Proper REST endpoints usually have 3+ chars
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters

    |

    ([a-zA-Z0-9_\-]{1,}                 # filename
    \.(?:php|asp|aspx|jsp|json|
         action|html|js|txt|xml)        # . + extension
    (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters

  )

  (?:"|')                               # End newline delimiter

"""

def extract_endpoints_from_js(content, base_url=None, filter_regex=None):
    """Extract endpoints from JavaScript content
    
    Args:
        content: JavaScript content as string
        base_url: Base URL to resolve relative URLs
        filter_regex: Optional regex to filter results
        
    Returns:
        List of endpoint URLs
    """
    endpoints = set()
    
    try:
        if len(content) > 1000000:
            content = content.replace(";",";\r\n").replace(",",",\r\n")
        else:
            if jsbeautifier:
                content = jsbeautifier.beautify(content)
    except Exception:
        pass
    
    regex = re.compile(regex_str, re.VERBOSE)
    
    for match in re.finditer(regex, content):
        endpoint = match.group(1)
        
        if filter_regex and not re.search(filter_regex, endpoint):
            continue
            
        if base_url:
            if endpoint.startswith("//"):
                endpoint = "https:" + endpoint
            elif endpoint.startswith("/"):
                endpoint = base_url.rstrip("/") + endpoint
            elif not endpoint.startswith("http"):
                endpoint = base_url.rstrip("/") + "/" + endpoint
        
        endpoints.add(endpoint)
    
    return list(endpoints)

async def extract_endpoints_from_url(js_url, session=None, base_url=None, filter_regex=None):
    """Extract endpoints from JavaScript file URL
    
    Args:
        js_url: URL of JavaScript file
        session: aiohttp session for requests
        base_url: Base URL to resolve relative URLs
        filter_regex: Optional regex to filter results
        
    Returns:
        List of endpoint URLs
    """
    import aiohttp
    
    try:
        if session:
            async with session.get(js_url) as response:
                if response.status == 200:
                    content = await response.text()
                    return extract_endpoints_from_js(content, base_url or js_url, filter_regex)
        else:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(js_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return extract_endpoints_from_js(content, base_url or js_url, filter_regex)
    except Exception:
        pass
    return []

