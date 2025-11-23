#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Version checker utility module
"""

import requests
from endabyss import __version__

def get_version_notification():
    """Check for newer version and return notification if available"""
    try:
        response = requests.get(
            "https://api.github.com/repos/arrester/endabyss/releases/latest",
            timeout=5
        )
        if response.status_code == 200:
            latest_version = response.json().get("tag_name", "").lstrip("v")
            if latest_version and latest_version != __version__:
                return f"A newer version ({latest_version}) is available. Current version: {__version__}"
    except:
        pass
    return None

