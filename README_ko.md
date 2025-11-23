# 🌊 EndAbyss

![Python Version](https://img.shields.io/badge/python-3.13%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.0-orange)

EndAbyss는 버그 헌팅과 레드 팀 작업을 위해 웹사이트를 크롤링하여 엔드포인트와 파라미터를 수집하는 빠른 엔드포인트 발견 도구입니다.

<br>

## 🌟 특징
- **레드팀/버그바운티 지원**: 레드팀 작전과 웹 버그바운티 프로젝트 모두에서 활용 가능
- **정적/동적 스캔**: 빠른 정적 스캔 또는 현대적인 프레임워크를 위한 Playwright 기반 동적 스캔
- **엔드포인트 발견**: HTML, JavaScript, API 응답에서 엔드포인트 자동 수집
- **파라미터 추출**: 폼과 URL에서 GET/POST 파라미터 자동 추출
- **디렉토리 스캔**: Wordlist 기반 디렉토리 브루트포싱 지원
- **파이프라인 연계**: `-pipeurl`, `-pipeendpoint`, `-pipeparam`, `-pipejson` 옵션으로 다른 도구와의 연계 가능
- **WAF 우회 옵션**: Delay, Random Delay, Rate Limiting, Proxy 지원
- **모듈형 설계**: Python 모듈로 import하여 사용 가능

<br>

## 🚀 설치
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

동적 스캔 모드를 사용하려면 Playwright 브라우저를 설치해야 합니다:
```bash
playwright install chromium
```

<br>

## 📖 사용법
### CLI 모드
<b>기본 스캔</b><br>
`endabyss -t http://example.com`

<b>동적 스캔 모드</b><br>
`endabyss -t http://example.com -m dynamic`

<b>디렉토리 스캔</b><br>
`endabyss -t http://example.com -ds -w wordlist.txt`

<b>파이프라인 출력</b><br>
`endabyss -t http://example.com -pipeurl` # URL만 출력<br>
`endabyss -t http://example.com -pipeendpoint` # 엔드포인트만 출력<br>
`endabyss -t http://example.com -pipeparam` # 파라미터만 출력<br>
`endabyss -t http://example.com -pipejson` # JSON 형식 출력

<b>파이프라인 연계 예시</b><br>
`endabyss -t http://example.com -pipeurl | sqlmap --batch`

### Python 모듈로 사용
<b>기본 엔드포인트 스캔</b><br>
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
    
    print(f"발견된 엔드포인트: {len(results['endpoints'])}개")
    print(f"발견된 폼: {len(results['forms'])}개")
    print(f"발견된 파라미터 세트: {len(results['parameters'])}개")
    
    for param_data in results['parameters']:
        url = param_data['url']
        params = param_data.get('parameters', {})
        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        print(f"{url}?{param_str} [{param_data['method']}]")

if __name__ == "__main__":
    asyncio.run(main())
```

<br>

<b>동적 스캔</b><br>
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

<b>결과 저장</b><br>
```python
from endabyss.core.controller.controller import EndAbyssController
import asyncio

async def main():
    controller = EndAbyssController("http://example.com")
    
    results = await controller.scan()
    
    output_path = controller.get_output_path("results.json")
    controller.save_results(results, output_path)
    print(f"결과 저장 위치: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

<br>

## 🔧 참고 도구에서 가져온 핵심 기능

EndAbyss는 다양한 참고 도구의 핵심 기능을 통합했습니다:

- **Katana**: 깊은 크롤링 및 엔드포인트 발견 방법론
- **LinkFinder**: 정규식 패턴을 사용한 JavaScript 엔드포인트 추출
- **ParamSpider**: 파라미터 추출 및 URL 정리 기법
- **SubSurfer**: CLI 디자인, 파이프라인 연계, 모듈형 아키텍처

<br>

## 📋 사용 가능한 옵션

| 옵션 | 설명 |
|------|------|
| `-t, --target` | 대상 URL 또는 도메인 |
| `-tf, --targetfile` | 대상 목록이 포함된 파일 |
| `-m, --mode` | 스캔 모드: static (기본값) 또는 dynamic |
| `-d, --depth` | 크롤링 깊이 (기본값: 5) |
| `-c, --concurrency` | 동시 요청 수 (기본값: 10) |
| `-ds, --dirscan` | 디렉토리 스캔 활성화 |
| `-w, --wordlist` | 디렉토리 스캔용 wordlist 파일 |
| `--delay` | 요청 간 지연 시간 (초) |
| `--random-delay` | 랜덤 지연 범위 (예: 1-3) |
| `--proxy` | 프록시 URL (HTTP/HTTPS/SOCKS5) |
| `--rate-limit` | Rate limit (초당 요청 수) |
| `-pipeurl` | 파이프라인용 URL만 출력 |
| `-pipeendpoint` | 파이프라인용 엔드포인트만 출력 |
| `-pipeparam` | 파이프라인용 파라미터만 출력 |
| `-pipejson` | 파이프라인용 JSON 형식 출력 |

<br>

## 📋 요구사항
- Python 3.13.0 이상 권장
- aiohttp
- beautifulsoup4
- playwright (동적 스캔용)
- rich
- requests

## 📝 라이선스
MIT License

## 🤝 기여
Bug Report, Feature Suggestions, Issue Report

