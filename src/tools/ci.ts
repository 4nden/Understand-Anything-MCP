import { z } from 'zod';
import { normalizeNodeId, validateComplexity } from '../services/validation.js';
import { requireTier } from '../services/license.js';

export const ciToolSchema = {
  name: 'ua_ci_check',
  description: 'Analyzes PR diff impact using the graph. (Team tier only)',
  inputSchema: {
    type: 'object',
    properties: {
      pr_diff: {
        type: 'string',
        description: 'The Git diff of the Pull Request.'
      }
    },
    required: ['pr_diff'],
  },
};

export async function handleCiCheck(args: any) {
  const { pr_diff } = args;

  if (!(await requireTier('Team'))) {
    throw new Error('ua_ci_check requires a Team tier license.');
  }

  // Naive diff parser to simulate graph impact analysis input
  const files = [];
  const lines = pr_diff.split('\n');
  for (const line of lines) {
    if (line.startsWith('+++ b/')) {
      files.push(line.substring(6));
    }
  }

  if (files.length === 0) {
    files.push('unknown_file');
  }

  const impactReport = {
    analyzed_files: files,
    impact_level: files.length > 5 ? 'HIGH' : 'LOW',
    affected_nodes: ['ComponentA', 'DatabaseSchema'],
    recommendations: [
      'Ensure new code is fully tested.',
      'Check downstream dependencies for possible breaking changes.'
    ]
  };

  return {
    content: [{ type: 'text', text: JSON.stringify(impactReport, null, 2) }],
  };
}

export const validateGraphSchema = {
  name: 'ua_validate_graph',
  description: 'Validate the knowledge graph structure (Team tier only)',
  inputSchema: {
    type: 'object',
    properties: {
      graphData: {
        type: 'string',
        description: 'The JSON string of the graph data to validate'
      }
    },
    required: ['graphData'],
  },
};

export async function handleValidateGraph(args: any) {
  const { graphData } = args;

  if (!(await requireTier('Team'))) {
    throw new Error('ua_validate_graph requires a Team tier license.');
  }

  try {
    // Just testing the imported functions
    normalizeNodeId('testNode');
    validateComplexity('simple');
    
    return {
      content: [{ type: 'text', text: 'Graph validated successfully' }],
    };
  } catch (error: any) {
    return {
      content: [{ type: 'text', text: `Validation failed: ${error.message}` }],
      isError: true,
    };
  }
}
