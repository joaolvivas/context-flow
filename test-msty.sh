#!/bin/bash
# Test the proxy with a real chat request

echo "🧪 Testing chat completion..."

curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello, who are you?"}]
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print('❌ Error:', data['error']['message'])
        sys.exit(1)
    else:
        print('✅ Success! Proxy is working')
        print('Response preview:', data.get('choices', [{}])[0].get('message', {}).get('content', '')[:100])
except Exception as e:
    print('❌ Failed to parse response:', e)
    sys.exit(1)
"
