"""
Fetch injury data from ESPN and persist a disk cache to speed repeated runs.
This module attempts multiple sources in order:
  1. Disk cache (if fresh)
  2. ESPN teams API
  3. ESPN scoreboard event injury notes

The returned structure is a mapping {team_name: ["Player Name (status)", ...]}.
"""

import requests
from typing import Dict, List
import time
import json
import os
from pathlib import Path

# In-memory cache
_INJURY_CACHE = None
_INJURY_CACHE_TS = 0
_INJURY_CACHE_TTL = 3600  # 1 hour

# Disk cache location
_CACHE_DIR = Path('.cache')
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE_FILE = _CACHE_DIR / 'injuries.json'


def _load_disk_cache() -> Dict:
    try:
        if not _CACHE_FILE.exists():
            return {}
        payload = json.loads(_CACHE_FILE.read_text())
        ts = payload.get('ts', 0)
        if time.time() - ts > _INJURY_CACHE_TTL:
            return {}
        return payload.get('injuries', {})
    except Exception:
        return {}


def _write_disk_cache(injuries: Dict):
    try:
        payload = {'ts': time.time(), 'injuries': injuries}
        _CACHE_FILE.write_text(json.dumps(payload))
    except Exception:
        pass


def get_team_injuries() -> Dict[str, List[str]]:
    """
    Get injuries map. Uses in-memory + disk cache and falls back to ESPN endpoints.
    """
    global _INJURY_CACHE, _INJURY_CACHE_TS

    # In-memory cache
    if _INJURY_CACHE is not None and (time.time() - _INJURY_CACHE_TS) < _INJURY_CACHE_TTL:
        return _INJURY_CACHE

    # Disk cache
    disk = _load_disk_cache()
    if disk:
        _INJURY_CACHE = disk
        _INJURY_CACHE_TS = time.time()
        return _INJURY_CACHE

    injuries = {}
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        # The structure can be nested; try multiple safe access patterns
        for item in data.get('teams', []) or []:
            # team object may be under 'team' key
            team_obj = item.get('team') if isinstance(item, dict) and item.get('team') else item
            team_name = team_obj.get('displayName') or team_obj.get('name') or team_obj.get('location')
            if not team_name:
                continue
            injured = []
            for inj in item.get('injuries', []) or []:
                # inj might be dict with displayName/status
                name = inj.get('displayName') or inj.get('player', {}).get('displayName') or ''
                status = inj.get('status') or inj.get('description') or ''
                label = f"{name} ({status})".strip()
                if name:
                    injured.append(label)

            injuries[team_name] = injured

    except Exception:
        injuries = {}

    # If teams endpoint didn't provide many injuries, try scoreboard events
    if len(injuries) <= 5:
        try:
            sb_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
            sb = requests.get(sb_url, timeout=5).json()
            for event in sb.get('events', []) or []:
                comps = event.get('competitions') or []
                if not comps:
                    continue
                comp = comps[0]
                notes = comp.get('notes') or []
                # some notes include injury text; also 'injuries' may be present
                for inj in comp.get('injuries', []) or []:
                    t = inj.get('team', {}).get('displayName') or ''
                    pname = inj.get('displayName') or inj.get('player', {}).get('displayName') or ''
                    status = inj.get('status') or ''
                    if pname and t:
                        injuries.setdefault(t, []).append(f"{pname} ({status})")
                # fallback: parse notes text for 'out' or 'questionable' (best-effort)
                for note in notes:
                    text = note.get('headline') or note.get('text') or ''
                    if not text:
                        continue
                    # best-effort: if text mentions 'out' or 'questionable' and a player name pattern
                    for team in [comp.get('home', {}).get('team', {}).get('displayName'), comp.get('away', {}).get('team', {}).get('displayName')]:
                        if not team:
                            continue
                        if 'out' in text.lower() or 'questionable' in text.lower() or 'did not travel' in text.lower():
                            injuries.setdefault(team, []).append(text[:80])
        except Exception:
            pass

    # normalize empty -> empty dict
    if not injuries:
        injuries = {}

    # save to caches
    _INJURY_CACHE = injuries
    _INJURY_CACHE_TS = time.time()
    try:
        _write_disk_cache(injuries)
    except Exception:
        pass

    return injuries


def calculate_injury_impact(team_name: str, injuries_dict: Dict[str, List[str]]) -> float:
    """
    Estimate scoring impact (points) of injuries for a team.
    Returns a non-negative float (points lost).
    """
    injured = injuries_dict.get(team_name, [])
    if not injured:
        return 0.0

    SUPERSTARS = {
        "Luka Doncic": 10, "LeBron James": 10, "Giannis Antetokounmpo": 10,
        "Kevin Durant": 9, "Jayson Tatum": 8, "Stephen Curry": 9,
        "Shai Gilgeous-Alexander": 8, "Joel Embiid": 10, "Damian Lillard": 8,
        "Kawhi Leonard": 8, "Jimmy Butler": 7, "Anthony Davis": 9,
    }

    superstar_total = 0.0
    superstar_count = 0
    role_count = 0

    for entry in injured:
        name = entry.split('(')[0].strip()
        matched = False
        for star, impact in SUPERSTARS.items():
            if star.lower() in name.lower():
                superstar_total += impact
                superstar_count += 1
                matched = True
                break
        if not matched:
            role_count += 1

    role_impact = role_count * 1.5
    total = superstar_total + role_impact
    # apply a conservative scaling: if many stars out, downscale slightly
    if superstar_count >= 2:
        total *= 0.9
    # cap
    return min(total, 15.0)


def adjust_prediction_for_injuries(away_team: str, home_team: str, injuries_map=None) -> float:
    """
    Return the additive injury adjustment to the model prediction (negative reduces total).
    """
    if injuries_map is None:
        injuries = get_team_injuries()
    else:
        injuries = injuries_map or {}

    home_impact = calculate_injury_impact(home_team, injuries)
    away_impact = calculate_injury_impact(away_team, injuries)

    # average of both teams' lost points reduces the game total
    return - (home_impact + away_impact) / 2.0
