# 🌊 EndAbyss

![Python Version](https://img.shields.io/badge/python-3.13%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.0-orange)

EndAbyss is a fast endpoint discovery tool that crawls websites to collect endpoints and parameters for bug bounty and red team operations.

<br>

## 🌟 Features
- **Red Team/Bug Bounty Support**: Useful for both red team operations and web bug bounty projects
- **Static/Dynamic Scanning**: Fast static scanning or Playwright-based dynamic scanning for modern frameworks
- **Endpoint Discovery**: Automatic collection of endpoints from HTML, JavaScript, and API responses
- **Parameter Extraction**: Automatic extraction of GET/POST parameters from forms and URLs
- **Directory Scanning**: Wordlist-based directory brute-forcing support
- **Pipeline Integration**: Supports integration with other tools using `-pipeurl`, `-pipeendpoint`, `-pipeparam`, `-pipejson` options
- **WAF Bypass Options**: Delay, random delay, rate limiting, and proxy support
- **Modular Design**: Can be imported and used as a Python module

<br>

## 🚀 Installation
<b>bash</b>
```bash
git clone https://github.com/arrester/endabyss.git
cd endabyss
pip install -r requirements.txt
pip install -e .
```

or <br>

<b>Python</b>
```bash
pip install endabyss
```

For dynamic scanning mode, install Playwright browsers:
```bash
playwright install chromium
```

<br>

## 📖 Usage
### CLI Mode
<b>Basic Scan</b><br>
`endabyss -t http://example.com`

<b>Dynamic Scanning Mode</b><br>
`endabyss -t http://example.com -m dynamic`

<b>Directory Scanning</b><br>
`endabyss -t http://example.com -ds -w wordlist.txt`

<b>Pipeline Output</b><br>
`endabyss -t http://example.com -pipeurl` # Output URLs only<br>
`endabyss -t http://example.com -pipeendpoint` # Output endpoints only<br>
`endabyss -t http://example.com -pipeparam` # Output parameters only<br>
`endabyss -t http://example.com -pipejson` # Output JSON format

<b>Pipeline Integration Example</b><br>
`endabyss -t http://example.com -pipeurl | sqlmap --batch`

### Using as a Python Module
<b>Basic Endpoint Scan</b><br>
```python
from endabyss.core.controller.controller import EndAbyssController
import asyncio

async def main():
    controller = EndAbyssController(
        target="http://example.com",
        mode="static",
        verbose=1,
        depth=5
    )
    
    results = await controller.scan()
    
    print(f"Found {len(results['endpoints'])} endpoints")
    print(f"Found {len(results['forms'])} forms")
    print(f"Found {len(results['parameters'])} parameter sets")
    
    for param_data in results['parameters']:
        url = param_data['url']
        params = param_data.get('parameters', {})
        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        print(f"{url}?{param_str} [{param_data['method']}]")

if __name__ == "__main__":
    asyncio.run(main())
```

<br>

<b>Dynamic Scanning</b><br>
```python
from endabyss.core.controller.controller import EndAbyssController
import asyncio

async def main():
    controller = EndAbyssController(
        target="http://example.com",
        mode="dynamic",
        headless=True,
        wait_time=3.0
    )
    
    results = await controller.scan()
    
    for endpoint in results['endpoints']:
        print(endpoint['url'])

if __name__ == "__main__":
    asyncio.run(main())
```

<br>

<b>Result Save</b><br>
```python
from endabyss.core.controller.controller import EndAbyssController
import asyncio

async def main():
    controller = EndAbyssController("http://example.com")
    
    results = await controller.scan()
    
    output_path = controller.get_output_path("results.json")
    controller.save_results(results, output_path)
    print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

<br>

## 🔧 Key Features from Reference Tools

EndAbyss incorporates key features from various reference tools:

- **Katana**: Deep crawling and endpoint discovery methodology
- **LinkFinder**: JavaScript endpoint extraction using regex patterns
- **ParamSpider**: Parameter extraction and URL cleaning techniques
- **SubSurfer**: CLI design, pipeline integration, and modular architecture

<br>

## 📋 Available Options

| Option | Description |
|--------|-------------|
| `-t, --target` | Target URL or domain |
| `-tf, --targetfile` | File containing list of targets |
| `-m, --mode` | Scan mode: static (default) or dynamic |
| `-d, --depth` | Crawling depth (default: 5) |
| `-c, --concurrency` | Number of concurrent requests (default: 10) |
| `-ds, --dirscan` | Enable directory scanning |
| `-w, --wordlist` | Wordlist file for directory scanning |
| `--delay` | Delay between requests in seconds |
| `--random-delay` | Random delay range (e.g. 1-3) |
| `--proxy` | Proxy URL (HTTP/HTTPS/SOCKS5) |
| `--rate-limit` | Rate limit (requests per second) |
| `-pipeurl` | Output URLs only for pipeline |
| `-pipeendpoint` | Output endpoints only for pipeline |
| `-pipeparam` | Output parameters only for pipeline |
| `-pipejson` | Output JSON format for pipeline |

<br>

## 📋 Requirements
- Recommended: Python 3.13.0 or later
- aiohttp
- beautifulsoup4
- playwright (for dynamic scanning)
- rich
- requests

## 📝 License
MIT License

## 🤝 Contributions
Bug Report, Feature Suggestions, Issue Report
