import dotenv from 'dotenv';
import { z } from 'zod';

// Load environment variables
dotenv.config();

// Configuration schema with validation
const configSchema = z.object({
  // OpenAI
  openai: z.object({
    apiKey: z.string().min(1, 'OPENAI_API_KEY is required'),
    model: z.string().default('gpt-4-turbo-preview'),
  }),

  // Graphiti MCP
  graphiti: z.object({
    command: z.string().default('npx @getzep/mcp-server-graphiti'),
    enabled: z.boolean().default(true),
  }),

  // Proxy
  proxy: z.object({
    port: z.number().int().positive().default(3000),
  }),

  // Logging
  logging: z.object({
    level: z.enum(['error', 'warn', 'info', 'debug']).default('info'),
  }),

  // Memory
  memory: z.object({
    searchLimit: z.number().int().positive().default(5),
    enabled: z.boolean().default(true),
  }),
});

// Parse and validate configuration
function loadConfig() {
  const rawConfig = {
    openai: {
      apiKey: process.env.OPENAI_API_KEY || '',
      model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
    },
    graphiti: {
      command: process.env.GRAPHITI_MCP_COMMAND || 'npx @getzep/mcp-server-graphiti',
      enabled: process.env.MEMORY_ENABLED !== 'false',
    },
    proxy: {
      port: parseInt(process.env.PROXY_PORT || '3000', 10),
    },
    logging: {
      level: (process.env.LOG_LEVEL || 'info') as 'error' | 'warn' | 'info' | 'debug',
    },
    memory: {
      searchLimit: parseInt(process.env.MEMORY_SEARCH_LIMIT || '5', 10),
      enabled: process.env.MEMORY_ENABLED !== 'false',
    },
  };

  try {
    return configSchema.parse(rawConfig);
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('❌ Configuration validation failed:');
      error.errors.forEach((err) => {
        console.error(`  - ${err.path.join('.')}: ${err.message}`);
      });
      process.exit(1);
    }
    throw error;
  }
}

export const config = loadConfig();
