#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EndAbyss - Fast Web Bug Bounty Endpoint Discovery Tool
"""

import sys
import json
from endabyss.core.cli.cli import print_banner, print_status, print_usage, console
from endabyss.core.cli.parser import parse_args
from endabyss.core.controller.controller import EndAbyssController
from endabyss.core.utils.version_checker import get_version_notification

async def main():
    """메인 함수"""
    args = parse_args()
    
    is_pipeline = any([args.pipeurl, args.pipeendpoint, args.pipeparam, args.pipejson])
    silent = args.silent if hasattr(args, 'silent') else False
    show_output = not is_pipeline and not silent
    
    if show_output:
        print_banner()
    
    if len(sys.argv) == 1:
        print_usage()
        if show_output:
            print_status("Please specify the target URL or domain.", "error")
            version_notification = get_version_notification()
            if version_notification:
                print()
                print_status(version_notification, "warning")
        sys.exit(1)
    
    target = args.target
    if args.targetfile:
        try:
            with open(args.targetfile, 'r', encoding='utf-8') as f:
                targets = [line.strip() for line in f if line.strip()]
        except Exception as e:
            if show_output:
                print_status(f"Error reading target file: {e}", "error")
            sys.exit(1)
    else:
        targets = [target] if target else []
        
    if not targets:
        if show_output:
            print_usage()
            print_status("Please specify the target URL or domain.", "error")
            version_notification = get_version_notification()
            if version_notification:
                print()
                print_status(version_notification, "warning")
        sys.exit(1)
        
    all_results = {
        'endpoints': [],
        'forms': [],
        'parameters': []
    }
    
    for target in targets:
        if show_output:
            print_status(f"Target: {target}", "info")
            
        controller = EndAbyssController(
            target=target,
            mode=args.mode,
            verbose=0 if (is_pipeline or silent) else args.verbose,
            depth=args.depth,
            concurrency=args.concurrency,
            session=args.session,
            delay=args.delay,
            random_delay=args.random_delay,
            timeout=args.timeout,
            retry=args.retry,
            retry_delay=args.retry_delay,
            user_agent=args.user_agent,
            proxy=args.proxy,
            rate_limit=args.rate_limit,
            headless=args.headless,
            wait_time=args.wait_time,
            dirscan=args.dirscan,
            wordlist=args.wordlist,
            status_codes=args.status_codes,
            exclude_ext=args.exclude_ext,
            exclude_path=args.exclude_path,
            include_ext=args.include_ext,
            include_path=args.include_path,
            min_params=args.min_params,
            silent=(is_pipeline or silent)
        )
        
        results = await controller.scan()
        
        all_results['endpoints'].extend(results.get('endpoints', []))
        all_results['forms'].extend(results.get('forms', []))
        all_results['parameters'].extend(results.get('parameters', []))
        
    if controller:
        output_path = controller.get_output_path(args.output) if args.output else controller.get_output_path()
        controller.save_results(all_results, output_path)
    else:
        output_path = None
    
    output_mode = None
    if args.pipeurl:
        output_mode = "url"
    elif args.pipeendpoint:
        output_mode = "endpoint"
    elif args.pipeparam:
        output_mode = "param"
    elif args.pipejson:
        output_mode = "json"
        
    if args.pipejson:
        print(json.dumps(all_results, indent=None, ensure_ascii=False))
    else:
        if controller:
            controller.print_results(all_results, output_mode, output_path if (is_pipeline or silent) else None)
        
    if show_output:
        version_notification = get_version_notification()
        if version_notification:
            print()
            print_status(version_notification, "warning")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

