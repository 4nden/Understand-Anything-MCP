# Marketing Announcements Drafts

## GitHub Discussions
**Title:** Introducing Understand-Anything: A Production-Ready MCP Server for Knowledge Graphs 🚀

**Body:**
Hi everyone!
We're thrilled to announce the open-source release of **Understand-Anything**, an English-first MCP server that allows LLMs to easily build and query complex knowledge graphs of your code and documentation.

**Why did we build this?**
We noticed a gap in the ecosystem for robust, persistent context management across large projects. Understand-Anything enables your AI assistant to "remember" and query architectural decisions, code dependencies, and business logic.

**Key Features:**
- Seamless Claude Desktop integration.
- Advanced relationship tracking.
- CI/CD integrations for graph validations.
- Open-source with scalable Pro/Team tiers.

Check out the repository and let us know what you think! We welcome issues and pull requests.
Quick start: `npm install -g ua-mcp`

## Hacker News
**Title:** Show HN: Understand-Anything – An MCP server for LLM Knowledge Graphs

**Body:**
Hey HN,
I've been frustrated by LLMs losing track of project context once the codebase gets too large. Today I'm releasing Understand-Anything, a Model Context Protocol (MCP) server that empowers LLMs to build and manage persistent knowledge graphs over time.

It allows AI assistants (like Claude) to dynamically add nodes/edges representing architectural components, and later query them with tools like `read_graph` or `search_nodes`.

The core server is MIT licensed and free, with paid options for advanced analytics and team sync. I'd love to hear your feedback on the API design and use cases!

Repo: [Link]
Install: `npm install -g ua-mcp`

## r/ClaudeAI
**Title:** I built an MCP server to give Claude a persistent Knowledge Graph memory 🧠

**Body:**
Hey r/ClaudeAI,
I wanted to share a tool I just released called **Understand-Anything**. It's an MCP server that you can plug directly into your Claude Desktop app. 

Instead of re-explaining your project architecture in every prompt, Claude can now use this server to read and write to a persistent Knowledge Graph. It can map out dependencies, concepts, and relationships, saving a ton of tokens and preventing hallucinations on complex codebases.

**How to try it:**
1. Run `npm install -g ua-mcp`
2. Add the server to your `claude_desktop_config.json`
3. Tell Claude: "Analyze this project and map out the core components."

Let me know what you build with it! I'm actively looking for feedback.
