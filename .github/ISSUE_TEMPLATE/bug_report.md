---
name: Bug Report
about: Report a bug or issue with MemoryStack
title: '[BUG] '
labels: bug
assignees: ''
---

## Describe the Bug

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:
1. Start MemoryStack with configuration...
2. Send request with...
3. See error...

## Expected Behavior

A clear description of what you expected to happen.

## Actual Behavior

What actually happened instead.

## Environment

- **MemoryStack Version**: [e.g., 3.0.0]
- **Python Version**: [e.g., 3.11.5]
- **Operating System**: [e.g., Ubuntu 22.04, macOS 14, Windows 11]
- **Deployment Method**: [e.g., Docker, Manual]
- **Memory Backend**: [e.g., Graphiti, Supermemory]
- **Redis Version**: [e.g., 7.0]

## Configuration

```bash
# Relevant parts of your .env (remove sensitive values!)
MEMORY_BACKEND=graphiti
WORKING_MEMORY_TURNS=10
PROGRESSIVE_INJECTION=true
# ... other relevant config
```

## Logs

```
Paste relevant logs here.
Docker: docker logs memorystack-proxy
Manual: cat /tmp/proxy_v3.log
```

## Additional Context

Add any other context about the problem here. Screenshots, error messages, etc.

## Possible Solution

(Optional) If you have an idea of what might be causing this or how to fix it.
