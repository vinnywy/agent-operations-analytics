"""Classify issue data; never execute issue content or change approval status."""
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


ENUMS = {
    'area': ('policy', 'harness', 'evals', 'skill', 'onboarding', 'security', 'data-workflow', 'documentation'),
    'impact': ('low', 'medium', 'high', 'critical'),
    'origin': ('user', 'agent', 'mixed'),
}


def classify(body):
    if not isinstance(body, str) or len(body) > 65000:
        return []
    marker = re.findall(r'<!-- agentops-meta:(.*?) -->', body)
    try:
        if marker:
            if len(marker) != 1:
                return []
            values = json.loads(marker[0])
        else:
            values = {}
            for field in ENUMS:
                found = re.findall(r'^### ' + field + r'\s*\n\s*([^\n]+)', body, re.M)
                if len(found) != 1:
                    return []
                values[field] = found[0].strip()
        if not isinstance(values, dict) or set(values) != set(ENUMS):
            return []
        if any(values[k] not in options for k, options in ENUMS.items()):
            return []
        return ['type:rfc'] + [f'{k}:{values[k]}' for k in ENUMS]
    except (ValueError, TypeError):
        return []


def request(repo, path, token, method='GET', data=None):
    url = f'https://api.github.com/repos/{repo}/{path}'
    req = Request(url, method=method, headers={
        'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json',
    }, data=json.dumps(data).encode() if data is not None else None)
    with urlopen(req, timeout=20) as res:
        raw = res.read()
        return json.loads(raw) if raw else None


def main():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    repo = os.environ['GITHUB_REPOSITORY']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('Invalid repository')
    issue = event['issue']
    labels = classify(issue.get('body'))
    if not labels or not issue.get('title', '').startswith('[RFC]'):
        print('No valid RFC classification; manual triage required.')
        return
    number = issue['number']
    if not isinstance(number, int) or number < 1:
        raise ValueError('Invalid issue number')
    token = os.environ['GITHUB_TOKEN']
    # Fetch fresh labels, do not replace maintainer decisions from stale event data.
    current = request(repo, f'issues/{number}/labels', token)
    names = {x['name'] for x in current}
    if not any(x.startswith('status:') for x in names):
        labels.append('status:triage')
    for label in labels:
        try:
            request(repo, 'labels', token, 'POST', {'name': label, 'color': '1d76db'})
        except HTTPError as exc:
            if exc.code != 422:
                raise
    request(repo, f'issues/{number}/labels', token, 'POST', {'labels': labels})
    for obsolete in names - set(labels):
        if any(obsolete.startswith(k + ':') for k in ENUMS):
            try:
                request(repo, f'issues/{number}/labels/{quote(obsolete, safe="")}', token, 'DELETE')
            except HTTPError as exc:
                if exc.code != 404:
                    raise
    print('RFC classification updated; maintainer status preserved.')


if __name__ == '__main__':
    main()
