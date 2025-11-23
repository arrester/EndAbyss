#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command line argument parser module
"""

import argparse

def create_parser():
    """Create and return argument parser"""
    parser = argparse.ArgumentParser(
        description='EndAbyss - Red Teaming and Web Bug Bounty Fast Endpoint Discovery Tool'
    )
    
    parser.add_argument('-t', '--target', 
                      help='Target URL or domain (e.g. http://example.com)')
    parser.add_argument('-tf', '--targetfile',
                      dest='targetfile',
                      help='File containing list of targets')
    parser.add_argument('-m', '--mode',
                      choices=['static', 'dynamic'],
                      default='static',
                      help='Scan mode: static (default) or dynamic')
    parser.add_argument('-o', '--output',
                      help='Output file path')
    parser.add_argument('-v', '--verbose',
                      action='count',
                      default=0,
                      help='Increase output verbosity (-v, -vv, -vvv)')
    parser.add_argument('-d', '--depth',
                      type=int,
                      default=5,
                      help='Crawling depth (default: 5, unlimited: 0)')
    parser.add_argument('-c', '--concurrency',
                      type=int,
                      default=10,
                      help='Number of concurrent requests (default: 10)')
    parser.add_argument('-s', '--session',
                      help='Session file path (cookies or JSON)')
    parser.add_argument('-ds', '--dirscan',
                      action='store_true',
                      help='Enable directory scanning')
    parser.add_argument('-w', '--wordlist',
                      help='Wordlist file for directory scanning')
    parser.add_argument('--delay',
                      type=float,
                      default=0,
                      help='Delay between requests in seconds (default: 0)')
    parser.add_argument('--random-delay',
                      help='Random delay range (e.g. 1-3)')
    parser.add_argument('--timeout',
                      type=int,
                      default=30,
                      help='Request timeout in seconds (default: 30)')
    parser.add_argument('--retry',
                      type=int,
                      default=3,
                      help='Number of retries on failure (default: 3)')
    parser.add_argument('--retry-delay',
                      type=float,
                      default=1.0,
                      help='Delay between retries in seconds (default: 1)')
    parser.add_argument('--user-agent',
                      help='Custom User-Agent string')
    parser.add_argument('--proxy',
                      help='Proxy URL (HTTP/HTTPS/SOCKS5)')
    parser.add_argument('--rate-limit',
                      type=float,
                      help='Rate limit (requests per second)')
    parser.add_argument('--headless',
                      action='store_true',
                      default=True,
                      help='Run browser in headless mode (default: True)')
    parser.add_argument('--wait-time',
                      type=float,
                      default=3.0,
                      help='Wait time for page load in seconds (default: 3)')
    parser.add_argument('--exclude-ext',
                      help='Exclude file extensions (comma-separated)')
    parser.add_argument('--include-ext',
                      help='Include only these extensions (comma-separated)')
    parser.add_argument('--exclude-path',
                      help='Exclude paths (comma-separated)')
    parser.add_argument('--include-path',
                      help='Include only these paths (comma-separated)')
    parser.add_argument('--min-params',
                      type=int,
                      help='Minimum number of parameters to include')
    parser.add_argument('--status-codes',
                      help='HTTP status codes to include (comma-separated, default: 200,201,202,204,301,302,307,401,403)')
    parser.add_argument('--error-log',
                      help='File to save error logs')
    parser.add_argument('-pipeurl', action='store_true',
                      help='Output URLs only for pipeline')
    parser.add_argument('-pipeendpoint', action='store_true',
                      help='Output endpoints only for pipeline')
    parser.add_argument('-pipeparam', action='store_true',
                      help='Output parameters only for pipeline')
    parser.add_argument('-pipejson', action='store_true',
                      help='Output all results in JSON format for pipeline')
                      
    return parser

def parse_args():
    """Parse and return command line arguments"""
    parser = create_parser()
    return parser.parse_args()

