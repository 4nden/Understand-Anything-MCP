# Understand-Anything MCP Server

![Claude Desktop Integration](examples/claude-desktop-screenshot.md)

This MCP Server bridges [Egonex-AI/Understand-Anything](https://github.com/Egonex-AI/Understand-Anything) with Claude Desktop and other MCP clients, giving LLMs native access to full-codebase structural graphs, architecture analysis, and CI/CD validation.

## Privacy Policy
> [!IMPORTANT]
> **[Link to Privacy Policy](#)** (Placeholder - A real privacy policy URL is required for submission to the Anthropic Connectors Directory. It must confirm that codebase/knowledge-graph data is processed locally and never sent to external servers.)

Understand-Anything is a production-ready MCP (Model Context Protocol) server that empowers LLMs to dynamically construct, update, and analyze complex knowledge graphs of codebases and text.

## Features
- **Knowledge Graph Management**: Create entities, define relations, and add observations.
- **Advanced Context Analysis**: Export targeted contexts or the full graph for advanced LLM reasoning.
- **Open-source with Premium Tiers**: Free essential features, with advanced capabilities for Pro and Team users.

## Quick Start
Install the server globally:
```bash
npm install -g ua-mcp
```

## Claude Desktop Configuration
Add the following to your Claude Desktop config file (usually `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "understand-anything": {
      "command": "npx",
      "args": ["-y", "ua-mcp"],
      "env": {
        "UA_PROJECT_PATH": "/path/to/your/project",
        "UA_LICENSE_KEY": "your_license_key_here"
      }
    }
  }
}
```

## Available Tools & Tiering

The Understand-Anything MCP Server operates on a tiered licensing model.

### Core Tools (Free Tier)
Available out of the box with no license required.
- `ua_status`: Returns MCP health status.
- `ua_scan`: Forces a re-scan of the workspace.
- `ua_graph_summary`: Returns aggregated node/edge statistics.
- `ua_architecture_report`: Groups files by top-level modules.
- `ua_dependency_report`: Identifies files with the most incoming dependencies (fan-in).
- `ua_explain`: Retrieves 1-hop dependencies for a specific file.
  - *Input*: `{"target": "src/index.ts"}`
- `ua_onboarding_doc`: Generates onboarding context.

### Premium Tools (Pro Tier - $29/mo)
- `ua_find_callers`: Retrieves reverse dependencies up to 2 hops.
  - *Input*: `{"target": "src/utils.ts"}`
- `ua_impact_analysis`: Retrieves full transitive closure of reverse dependencies.
  - *Input*: `{"target": "src/core/db.ts"}`

### Enterprise Tools (Team Tier - $99/mo)
- `ua_validate_graph`: Checks the knowledge graph schema for corruption.
- `ua_ci_check`: Analyzes Git PR diffs for architectural impact.
  - *Input*: `{"pr_diff": "..."}`

## Pricing

| Tier | Price | Features |
|---|---|---|
| **Free** | $0/mo | Basic graph operations, local storage. |
| **Pro** | $29/mo | Unlimited nodes, advanced graph analytics, semantic search, priority support. |
| **Team** | $99/mo | Multi-user sync, CI/CD integration, advanced validation, dedicated support. |

Get your license key at: [https://understand-anything.example.com](https://understand-anything.example.com)

## Troubleshooting

- **Server fails to start**: Ensure you have Node.js v18 or later installed.
- **License key error**: Verify your key in the `.env` file or Claude config matches the one on your dashboard.
- **Path not found**: Ensure `UA_PROJECT_PATH` is absolute or resolves correctly relative to where the server runs.

## License
MIT License
