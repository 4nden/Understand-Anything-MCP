import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { getGraph } from "../services/understand.js";
import { getCallers, getImpactAnalysis } from "../services/graph.js";

export function registerPremiumTools(server: McpServer) {
    server.tool(
        "ua_find_callers",
        "Find callers (reverse dependencies) of a specific file or module up to 2 hops (Pro Tier)",
        {
            target: z.string().describe("The file or module to find callers for"),
            maxHops: z.number().optional().describe("Maximum number of hops (default 2, up to 2 hops supported for callers)")
        },
        async ({ target, maxHops }) => {
            const graph = getGraph();
            if (!graph) {
                return { content: [{ type: "text", text: "No knowledge graph loaded. Please run ua_scan first." }] };
            }

            const hops = maxHops ?? 2;
            const callers = getCallers(graph, target, hops);
            
            return {
                content: [{ type: "text", text: `Found ${callers.length} callers for ${target} within ${hops} hops:\n- ${callers.join('\n- ')}` }]
            };
        }
    );

    server.tool(
        "ua_impact_analysis",
        "Analyze the impact of changing a file by finding all transitive reverse dependencies (Pro Tier)",
        {
            target: z.string().describe("The file or module to analyze for impact")
        },
        async ({ target }) => {
            const graph = getGraph();
            if (!graph) {
                return { content: [{ type: "text", text: "No knowledge graph loaded. Please run ua_scan first." }] };
            }

            const impactedNodes = getImpactAnalysis(graph, target);
            
            return {
                content: [{ type: "text", text: `Impact analysis for ${target} reveals ${impactedNodes.length} potentially affected nodes:\n- ${impactedNodes.join('\n- ')}` }]
            };
        }
    );
}
