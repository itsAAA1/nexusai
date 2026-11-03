# NexusAI Agent Stack Integration

This branch prepares integration of four open-source projects without modifying the production application.

| Component | Upstream | Role |
| --- | --- | --- |
| LangGraph | https://github.com/langchain-ai/langgraph | Stateful agent orchestration |
| Browser Use | https://github.com/browser-use/browser-use | Browser automation |
| CrewAI | https://github.com/crewAIInc/crewAI | Multi-agent workflows |
| Dify | https://github.com/langgenius/dify | AI workflow platform |

## Integration rules
- Pin upstream versions before installation and review their licenses and security advisories.
- Keep API keys in secrets, never commit credentials.
- Run services in isolated containers; avoid giving browser agents unrestricted access.
- Add integration tests and manual approval gates for external write actions.
- No components are installed or running as a result of this document.

## Next steps
1. Inspect the existing NexusAI architecture and deployment configuration.
2. Choose integration boundaries and compatible versions.
3. Implement adapters, tests and deployment files on this feature branch.
4. Review changes before merging into the default branch.
