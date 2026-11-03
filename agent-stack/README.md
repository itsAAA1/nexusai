# NexusAI agent stack

This directory defines how the four upstream systems will connect to NexusAI, without vendoring their source or pretending they are installed.

## Architecture
- **LangGraph**: primary orchestration/state machine for NexusAI tasks.
- **Browser Use**: browser automation worker invoked only for approved browsing tasks.
- **CrewAI**: optional specialist team worker; avoid running two orchestration engines for the same request.
- **Dify**: separate optional workflow/UI service, integrated through HTTP API rather than importing its whole codebase.

## Getting the source
Run `bash scripts/fetch-agent-stack.sh` on a machine with Git and internet access. It clones all four upstream repositories under `.agent-stack/` and records their commit hashes. This is source checkout, **not installation**.

## Running
Each upstream has different installation and infrastructure requirements. Review licenses, choose pinned versions, set service credentials and create isolated deployments before starting. No production deployment is configured here.

## Verification
The GitHub Actions workflow can check source retrieval when GitHub permits it to run. It does not prove the components are operational or connected to the NexusAI API.
