import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import urllib.request
import json

def check_status():
    print("=== CAMUNDA 8.9 STATUS CHECK ===")
    
    # 1. Search ALL process instances
    req = urllib.request.Request(
        'http://localhost:8080/v2/process-instances/search',
        data=b'{}',
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            res = json.loads(r.read().decode())
            items = res.get('items', [])
            print(f"Total process instances found: {len(items)}")
            for item in items:
                print(f"  Instance Key: {item.get('processInstanceKey')} | Process: '{item.get('processDefinitionId')}' | Version: {item.get('processDefinitionVersion')} | State: {item.get('state')} | Incidents: {item.get('hasIncident')}")
    except Exception as e:
        print(f"Error querying process instances: {e}")

    # 2. Search ALL process definitions
    req2 = urllib.request.Request(
        'http://localhost:8080/v2/process-definitions/search',
        data=b'{}',
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req2, timeout=5) as r:
            res2 = json.loads(r.read().decode())
            items2 = res2.get('items', [])
            print(f"\nTotal process definitions deployed: {len(items2)}")
            for item in items2:
                print(f"  Def Key: {item.get('processDefinitionKey')} | Process ID: '{item.get('processDefinitionId')}' | Version: {item.get('version')} | Name: '{item.get('name')}'")
    except Exception as e:
        print(f"Error querying process definitions: {e}")

    # 3. Search ACTIVE incidents
    req3 = urllib.request.Request(
        'http://localhost:8080/v2/incidents/search',
        data=json.dumps({'filter': {'state': 'ACTIVE'}}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req3, timeout=5) as r:
            res3 = json.loads(r.read().decode())
            items3 = res3.get('items', [])
            print(f"\nTotal ACTIVE incidents found: {len(items3)}")
            for item in items3:
                print(f"  [*] Incident Key: {item.get('incidentKey')} | Process: {item.get('processDefinitionId')} | Error: {item.get('errorType')} | Element: {item.get('elementId')}")
    except Exception as e:
        print(f"Error querying incidents: {e}")

if __name__ == '__main__':
    check_status()
