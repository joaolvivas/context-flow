import express, { Request, Response } from 'express';
import OpenAI from 'openai';
import { config } from './config.js';
import { logger, logInfo, logError, logDebug } from './logger.js';
import { processMemoryEnrichment } from './memory-manager.js';
import { disconnectMCPClient } from './mcp-client.js';

// Initialize Express app
const app = express();

// Middleware
app.use(express.json({ limit: '10mb' }));

// Request logging middleware
app.use((req, res, next) => {
  logDebug(`${req.method} ${req.path}`, {
    headers: req.headers,
    body: req.method === 'POST' ? '...' : undefined,
  });
  next();
});

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: config.openai.apiKey,
});

/**
 * Health check endpoint
 */
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'ok',
    service: 'memory-orchestrator-proxy',
    version: '1.0.0',
    memory: {
      enabled: config.memory.enabled,
      searchLimit: config.memory.searchLimit,
    },
  });
});

/**
 * Main chat completions endpoint (OpenAI compatible)
 */
app.post('/v1/chat/completions', async (req: Request, res: Response) => {
  const startTime = Date.now();

  try {
    const { messages, stream = false, model, ...otherParams } = req.body;

    // Validate request
    if (!messages || !Array.isArray(messages)) {
      res.status(400).json({
        error: {
          message: 'Invalid request: messages array is required',
          type: 'invalid_request_error',
        },
      });
      return;
    }

    logInfo('Received chat completion request', {
      messageCount: messages.length,
      stream,
      model: model || config.openai.model,
    });

    // Enrich messages with memory context
    const { enrichedMessages, metadata } = await processMemoryEnrichment(messages);

    logInfo('Memory enrichment complete', {
      memoriesFound: metadata.memoriesFound,
      enrichmentTime: Date.now() - startTime,
    });

    // Prepare OpenAI request
    const openaiRequest: OpenAI.Chat.ChatCompletionCreateParamsStreaming | OpenAI.Chat.ChatCompletionCreateParamsNonStreaming = {
      model: model || config.openai.model,
      messages: enrichedMessages,
      stream: stream as any,
      ...otherParams,
    };

    // Handle streaming vs non-streaming
    if (stream) {
      // Set headers for Server-Sent Events
      res.setHeader('Content-Type', 'text/event-stream');
      res.setHeader('Cache-Control', 'no-cache');
      res.setHeader('Connection', 'keep-alive');

      try {
        const streamResponse = await openai.chat.completions.create(openaiRequest as OpenAI.Chat.ChatCompletionCreateParamsStreaming);

        // Stream chunks to client
        for await (const chunk of streamResponse) {
          const data = JSON.stringify(chunk);
          res.write(`data: ${data}\n\n`);
        }

        // Send completion signal
        res.write('data: [DONE]\n\n');
        res.end();

        logInfo('Streaming response completed', {
          totalTime: Date.now() - startTime,
          memoriesUsed: metadata.memoriesFound,
        });
      } catch (error) {
        logError('Error during streaming', error);

        // Send error in SSE format
        res.write(`data: ${JSON.stringify({ error: 'Streaming failed' })}\n\n`);
        res.end();
      }
    } else {
      // Non-streaming response
      const completion = await openai.chat.completions.create(openaiRequest as OpenAI.Chat.ChatCompletionCreateParamsNonStreaming);

      logInfo('Chat completion successful', {
        totalTime: Date.now() - startTime,
        memoriesUsed: metadata.memoriesFound,
        tokensUsed: completion.usage?.total_tokens,
      });

      // Return OpenAI response as-is
      res.json(completion);
    }
  } catch (error: any) {
    logError('Error processing chat completion', error);

    // Handle OpenAI API errors
    if (error?.status) {
      res.status(error.status).json({
        error: {
          message: error.message,
          type: error.type || 'api_error',
          code: error.code,
        },
      });
    } else {
      // Internal server error
      res.status(500).json({
        error: {
          message: 'Internal server error',
          type: 'internal_error',
        },
      });
    }
  }
});

/**
 * Fallback for unsupported endpoints
 */
app.all('*', (req: Request, res: Response) => {
  res.status(404).json({
    error: {
      message: `Endpoint not found: ${req.method} ${req.path}`,
      type: 'invalid_request_error',
    },
  });
});

/**
 * Start server
 */
const server = app.listen(config.proxy.port, () => {
  logInfo(`🚀 Memory Orchestrator Proxy running on http://localhost:${config.proxy.port}`);
  logInfo('Configuration:', {
    openaiModel: config.openai.model,
    memoryEnabled: config.memory.enabled,
    memoryLimit: config.memory.searchLimit,
    logLevel: config.logging.level,
  });
  logInfo('📋 Available endpoints:');
  logInfo('  GET  /health');
  logInfo('  POST /v1/chat/completions (OpenAI compatible)');
});

/**
 * Graceful shutdown
 */
process.on('SIGINT', async () => {
  logInfo('Shutting down gracefully...');

  server.close(() => {
    logInfo('HTTP server closed');
  });

  await disconnectMCPClient();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logInfo('Received SIGTERM, shutting down...');

  server.close(() => {
    logInfo('HTTP server closed');
  });

  await disconnectMCPClient();
  process.exit(0);
});

// Handle uncaught errors
process.on('unhandledRejection', (reason, promise) => {
  logError('Unhandled Rejection at:', reason);
});

process.on('uncaughtException', (error) => {
  logError('Uncaught Exception:', error);
  process.exit(1);
});
