import json
import urllib.request
req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/reports/4b5da880-0a1a-44ad-b9c2-cb1f1d768dc1/analysis/translate',
    data=json.dumps({"target_language":"hi"}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req)
data = json.loads(resp.read().decode('utf-8'))
print("label_not_provided:", data.get('ui_labels', {}).get('label_not_provided'))
print("label_cat_cbc:", data.get('ui_labels', {}).get('label_cat_cbc'))
