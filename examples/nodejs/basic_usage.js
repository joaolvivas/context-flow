#!/usr/bin/env node
/**
 * MemoryStack - Node.js Basic Usage Example
 *
 * Shows how to use MemoryStack with the OpenAI Node.js SDK.
 * Just change the baseURL and your AI gets perfect memory!
 *
 * Installation:
 *   npm install openai
 *
 * Usage:
 *   node basic_usage.js
 */

const OpenAI = require('openai');

// Initialize client pointing to MemoryStack
const client = new OpenAI({
  apiKey: 'sk-your-openai-api-key',  // Your actual OpenAI API key
  baseURL: 'http://localhost:8000/v1',  // Point to MemoryStack
  defaultHeaders: {
    'X-User-Id': 'david'  // Optional: Namespace memories per user
  }
});

async function main() {
  console.log('=== First Conversation ===');

  // First conversation - store some information
  const response1 = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      { role: 'user', content: 'My name is David and I love JavaScript. I build web applications.' }
    ]
  });

  console.log(`AI: ${response1.choices[0].message.content}\n`);

  // Second conversation - test memory
  console.log('=== Second Conversation (Different Chat) ===');

  const response2 = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      { role: 'user', content: 'What\'s my name and what do I love?' }
    ]
  });

  console.log(`AI: ${response2.choices[0].message.content}\n`);
  // Expected: "Your name is David and you love JavaScript"

  // Third conversation - deeper question
  console.log('=== Third Conversation (Needs Long-term Memory) ===');

  const response3 = await client.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [
      { role: 'user', content: 'What kind of applications do I build?' }
    ]
  });

  console.log(`AI: ${response3.choices[0].message.content}\n`);

  console.log('✅ Memory working! Your AI remembers across different chats.');
}

main().catch(console.error);
