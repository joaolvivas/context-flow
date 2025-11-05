import { getMCPClient, GraphitiMemory, SearchResult } from './mcp-client.js';
import { config } from './config.js';
import { logInfo, logDebug } from './logger.js';

export interface EnrichedContext {
  systemPrompt: string;
  memoriesFound: number;
  queryUsed: string;
}

/**
 * Extract the most recent user message from chat history
 */
function extractUserQuery(messages: any[]): string {
  // Find the last user message
  const userMessages = messages.filter((msg) => msg.role === 'user');

  if (userMessages.length === 0) {
    return '';
  }

  const lastUserMessage = userMessages[userMessages.length - 1];

  // Handle both string content and array content (multimodal)
  if (typeof lastUserMessage.content === 'string') {
    return lastUserMessage.content;
  } else if (Array.isArray(lastUserMessage.content)) {
    // Extract text parts from content array
    return lastUserMessage.content
      .filter((part: any) => part.type === 'text')
      .map((part: any) => part.text)
      .join(' ');
  }

  return '';
}

/**
 * Rank and filter memories by relevance
 */
function rankMemories(memories: GraphitiMemory): SearchResult[] {
  const allMemories = [...memories.nodes, ...memories.facts];

  // Sort by relevance if available, otherwise keep original order
  const sorted = allMemories.sort((a, b) => {
    if (a.relevance !== undefined && b.relevance !== undefined) {
      return b.relevance - a.relevance;
    }
    return 0;
  });

  // Take top N results based on config
  return sorted.slice(0, config.memory.searchLimit);
}

/**
 * Format memories into a context string for the system prompt
 */
function formatMemoriesForContext(memories: SearchResult[]): string {
  if (memories.length === 0) {
    return '';
  }

  const formattedMemories = memories
    .map((mem, idx) => {
      const relevanceTag = mem.relevance ? ` (relevance: ${mem.relevance.toFixed(2)})` : '';
      return `${idx + 1}. ${mem.name}${relevanceTag}\n   ${mem.content}`;
    })
    .join('\n\n');

  return `\n\n---\n**Relevant memories from your knowledge graph:**\n\n${formattedMemories}\n---\n`;
}

/**
 * Main memory enrichment function
 *
 * Takes chat messages, searches for relevant memories, and returns enriched context
 */
export async function enrichWithMemories(messages: any[]): Promise<EnrichedContext> {
  // If memory is disabled, return empty context
  if (!config.memory.enabled) {
    logDebug('Memory enrichment disabled');
    return {
      systemPrompt: '',
      memoriesFound: 0,
      queryUsed: '',
    };
  }

  try {
    // Extract user query from messages
    const query = extractUserQuery(messages);

    if (!query) {
      logDebug('No user query found in messages');
      return {
        systemPrompt: '',
        memoriesFound: 0,
        queryUsed: '',
      };
    }

    logInfo('Enriching context with memories', { query: query.substring(0, 100) });

    // Get MCP client and search memories
    const mcpClient = await getMCPClient();
    const memories = await mcpClient.searchMemories(query);

    // Rank and select top memories
    const topMemories = rankMemories(memories);

    logInfo(`Found ${topMemories.length} relevant memories`, {
      nodes: memories.nodes.length,
      facts: memories.facts.length,
    });

    // Format memories for system prompt
    const memoryContext = formatMemoriesForContext(topMemories);

    return {
      systemPrompt: memoryContext,
      memoriesFound: topMemories.length,
      queryUsed: query,
    };
  } catch (error) {
    // Graceful degradation - if memory enrichment fails, continue without it
    logInfo('Memory enrichment failed, continuing without memories', {
      error: error instanceof Error ? error.message : String(error),
    });

    return {
      systemPrompt: '',
      memoriesFound: 0,
      queryUsed: '',
    };
  }
}

/**
 * Inject memory context into messages array
 *
 * Strategy: Add/enhance system message with memory context
 */
export function injectMemoryContext(messages: any[], memoryContext: string): any[] {
  if (!memoryContext) {
    return messages;
  }

  // Clone messages to avoid mutation
  const enrichedMessages = [...messages];

  // Find existing system message
  const systemMessageIndex = enrichedMessages.findIndex((msg) => msg.role === 'system');

  if (systemMessageIndex !== -1) {
    // Append memory context to existing system message
    const existingContent = enrichedMessages[systemMessageIndex].content;
    enrichedMessages[systemMessageIndex] = {
      ...enrichedMessages[systemMessageIndex],
      content: existingContent + memoryContext,
    };
  } else {
    // Create new system message with memory context
    enrichedMessages.unshift({
      role: 'system',
      content: `You are a helpful AI assistant with access to the user's personal knowledge graph.${memoryContext}`,
    });
  }

  return enrichedMessages;
}

/**
 * Complete memory enrichment pipeline
 *
 * 1. Search for relevant memories
 * 2. Rank and filter
 * 3. Inject into messages
 */
export async function processMemoryEnrichment(messages: any[]): Promise<{
  enrichedMessages: any[];
  metadata: {
    memoriesFound: number;
    queryUsed: string;
  };
}> {
  const { systemPrompt, memoriesFound, queryUsed } = await enrichWithMemories(messages);
  const enrichedMessages = injectMemoryContext(messages, systemPrompt);

  return {
    enrichedMessages,
    metadata: {
      memoriesFound,
      queryUsed,
    },
  };
}
