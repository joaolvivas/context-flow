import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { config } from './config.js';
import { logInfo, logError, logDebug } from './logger.js';

export interface SearchResult {
  name: string;
  content: string;
  relevance?: number;
}

export interface GraphitiMemory {
  nodes: SearchResult[];
  facts: SearchResult[];
}

/**
 * MCP Client for communicating with Graphiti server via stdio
 */
export class GraphitiMCPClient {
  private client: Client | null = null;
  private isConnected = false;

  /**
   * Initialize and connect to Graphiti MCP server
   */
  async connect(): Promise<void> {
    if (this.isConnected) {
      logDebug('MCP client already connected');
      return;
    }

    try {
      logInfo('Connecting to Graphiti MCP server', {
        command: config.graphiti.command,
      });

      // Parse the command (e.g., "npx @getzep/mcp-server-graphiti")
      const [command, ...args] = config.graphiti.command.split(' ');

      // Create stdio transport
      const transport = new StdioClientTransport({
        command,
        args,
      });

      // Create MCP client
      this.client = new Client(
        {
          name: 'memory-orchestrator-proxy',
          version: '1.0.0',
        },
        {
          capabilities: {},
        }
      );

      // Connect to server
      await this.client.connect(transport);
      this.isConnected = true;

      logInfo('✅ Successfully connected to Graphiti MCP server');
    } catch (error) {
      logError('Failed to connect to Graphiti MCP server', error);
      throw error;
    }
  }

  /**
   * Search for relevant nodes in the knowledge graph
   */
  async searchNodes(query: string, limit?: number): Promise<SearchResult[]> {
    if (!this.isConnected || !this.client) {
      logWarn('MCP client not connected, skipping node search');
      return [];
    }

    try {
      logDebug('Searching nodes', { query, limit });

      const result = await this.client.callTool({
        name: 'search_nodes',
        arguments: {
          query,
          limit: limit || config.memory.searchLimit,
        },
      });

      // Parse the result based on MCP response format
      const nodes = this.parseSearchResults(result);
      logInfo(`Found ${nodes.length} relevant nodes`, { query });

      return nodes;
    } catch (error) {
      logError('Error searching nodes', error, { query });
      return [];
    }
  }

  /**
   * Search for relevant facts in the knowledge graph
   */
  async searchFacts(query: string, limit?: number): Promise<SearchResult[]> {
    if (!this.isConnected || !this.client) {
      logWarn('MCP client not connected, skipping fact search');
      return [];
    }

    try {
      logDebug('Searching facts', { query, limit });

      const result = await this.client.callTool({
        name: 'search_facts',
        arguments: {
          query,
          limit: limit || config.memory.searchLimit,
        },
      });

      const facts = this.parseSearchResults(result);
      logInfo(`Found ${facts.length} relevant facts`, { query });

      return facts;
    } catch (error) {
      logError('Error searching facts', error, { query });
      return [];
    }
  }

  /**
   * Search both nodes and facts (parallel execution)
   */
  async searchMemories(query: string): Promise<GraphitiMemory> {
    const [nodes, facts] = await Promise.all([
      this.searchNodes(query),
      this.searchFacts(query),
    ]);

    return { nodes, facts };
  }

  /**
   * Add an episode to the knowledge graph (for memory persistence in V2)
   */
  async addEpisode(content: string, name: string): Promise<void> {
    if (!this.isConnected || !this.client) {
      logWarn('MCP client not connected, skipping episode addition');
      return;
    }

    try {
      logDebug('Adding episode', { name, contentLength: content.length });

      await this.client.callTool({
        name: 'add_episode',
        arguments: {
          content,
          name,
          source_description: name,
        },
      });

      logInfo('✅ Episode added successfully', { name });
    } catch (error) {
      logError('Error adding episode', error, { name });
    }
  }

  /**
   * Parse MCP tool call results into SearchResult array
   */
  private parseSearchResults(result: any): SearchResult[] {
    try {
      // MCP returns results in content array
      if (!result.content || !Array.isArray(result.content)) {
        return [];
      }

      // Extract text content from MCP response
      const results: SearchResult[] = [];

      for (const item of result.content) {
        if (item.type === 'text' && item.text) {
          // Try to parse as JSON array
          try {
            const parsed = JSON.parse(item.text);
            if (Array.isArray(parsed)) {
              results.push(...parsed.map((p: any) => ({
                name: p.name || p.id || 'Unknown',
                content: p.content || p.fact || p.description || JSON.stringify(p),
                relevance: p.score || p.relevance,
              })));
            } else {
              // Single result
              results.push({
                name: parsed.name || parsed.id || 'Unknown',
                content: parsed.content || parsed.fact || parsed.description || JSON.stringify(parsed),
                relevance: parsed.score || parsed.relevance,
              });
            }
          } catch {
            // If not JSON, treat as plain text
            results.push({
              name: 'Memory',
              content: item.text,
            });
          }
        }
      }

      return results;
    } catch (error) {
      logError('Error parsing search results', error);
      return [];
    }
  }

  /**
   * Disconnect from MCP server
   */
  async disconnect(): Promise<void> {
    if (this.client && this.isConnected) {
      try {
        await this.client.close();
        this.isConnected = false;
        logInfo('Disconnected from Graphiti MCP server');
      } catch (error) {
        logError('Error disconnecting from MCP server', error);
      }
    }
  }
}

// Import logWarn that was missing
function logWarn(message: string, context?: Record<string, any>) {
  logDebug(message, context); // Fallback to debug for now
}

// Singleton instance
let mcpClientInstance: GraphitiMCPClient | null = null;

/**
 * Get or create MCP client singleton
 */
export async function getMCPClient(): Promise<GraphitiMCPClient> {
  if (!mcpClientInstance) {
    mcpClientInstance = new GraphitiMCPClient();
    await mcpClientInstance.connect();
  }
  return mcpClientInstance;
}

/**
 * Cleanup function for graceful shutdown
 */
export async function disconnectMCPClient(): Promise<void> {
  if (mcpClientInstance) {
    await mcpClientInstance.disconnect();
    mcpClientInstance = null;
  }
}
