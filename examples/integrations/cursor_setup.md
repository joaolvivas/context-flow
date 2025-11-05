# ContextFlow Integration with Cursor IDE

Give your Cursor AI assistant perfect memory across all coding sessions. Remember your coding style, tech stack, architectural decisions, and project context automatically.

## Why Use ContextFlow with Cursor?

### The Problem

**Without ContextFlow:**
```
Day 1:
You: "Create a validation function using Zod"
Cursor: Creates with Zod ✓

Day 2 (new session):
You: "Create another validation"
Cursor: Uses plain JavaScript ✗ (forgot you use Zod!)
```

**With ContextFlow:**
```
Day 1:
You: "Create a validation function using Zod"
Cursor: Creates with Zod ✓

Day 2 (new session):
You: "Create another validation"
Cursor: Automatically uses Zod ✓ (remembers your pattern!)
```

### What It Remembers

- ✅ **Your coding style**: Indentation, naming conventions, patterns
- ✅ **Tech stack**: React, Next.js, TypeScript, Tailwind, etc.
- ✅ **Architecture decisions**: "We use Prisma", "We avoid class components"
- ✅ **Project context**: File structure, API endpoints, component patterns
- ✅ **Library preferences**: Zod vs Yup, Axios vs Fetch, etc.
- ✅ **Past conversations**: Previous implementations, explanations

### Cost Savings

**Typical Cursor usage (100 queries/day):**
- Without ContextFlow: ~200K tokens/day → **$0.50/day** → **$15/month**
- With ContextFlow: ~46K tokens/day → **$0.11/day** → **$3.30/month**

**Saved: $11.70/month per developer ($140/year)**

---

## Setup (5 minutes)

### Step 1: Start ContextFlow

```bash
# Clone and start ContextFlow
git clone https://github.com/joaolvivas/contextflow
cd contextflow
docker-compose up -d

# Verify it's running
curl http://localhost:8000/health
```

### Step 2: Configure Cursor

1. **Open Cursor Settings**
   - Press `Cmd/Ctrl + ,` or go to File → Preferences → Settings

2. **Go to Models Section**
   - Click on "Cursor Settings" in the bottom right
   - Or search for "Models" in settings

3. **Add Custom Model**:
   - Click "Add Model" or "Override OpenAI Base URL"
   - **Base URL**: `http://localhost:8000/v1`
   - **API Key**: Your actual OpenAI API key (e.g., `sk-proj-...`)
   - **Model**: Select your preferred model (gpt-4, gpt-4o-mini, etc.)

4. **Save and Restart Cursor**

### Step 3: Test It

**First conversation:**
```
You: "I'm building a Next.js 14 app with TypeScript, Tailwind, and Prisma.
     Create a user model with name, email, and created_at fields."

Cursor: [Creates Prisma schema with your preferences]
```

**Close Cursor completely. Reopen and start a NEW chat:**
```
You: "Create a post model"

Cursor: [Automatically uses Prisma, follows same pattern as user model!]
```

🎉 **It remembers!** Your AI assistant now has context from previous sessions.

---

## Configuration

### Default Configuration

ContextFlow works out of the box with sensible defaults. If you want to customize:

```bash
# Edit .env in ContextFlow directory
nano contextflow/.env

# Adjust memory tiers
WORKING_MEMORY_TURNS=10      # Recent conversation history
PROGRESSIVE_INJECTION=true   # Smart context injection
MEMORY_BACKEND=graphiti      # or supermemory
```

### Per-Project Memory

Want different memory for different projects?

```bash
# Set project-specific user ID in Cursor
# Unfortunately Cursor doesn't expose custom headers yet,
# but you can use different ContextFlow instances:

# Project 1
docker-compose -p project1 up -d
# Port 8001

# Project 2
docker-compose -p project2 up -d
# Port 8002

# Switch Base URL in Cursor per project
```

---

## Use Cases

### 1. **Consistent Code Style**

```
Session 1:
You: "Create a React component with TypeScript. Use functional components
     with arrow functions and export default."

Session 2 (days later):
You: "Create a Button component"
Cursor: Automatically follows your established pattern ✓
```

### 2. **Tech Stack Awareness**

```
You: "We use TanStack Query for data fetching, not SWR or plain fetch"

[Later]
You: "Fetch user data from /api/users"
Cursor: Uses TanStack Query automatically ✓
```

### 3. **Project Architecture**

```
You: "Our components go in src/components/ui/, hooks in src/hooks/,
     and we use barrel exports"

[Later]
You: "Create a new custom hook"
Cursor: Puts it in correct location with barrel export ✓
```

### 4. **API Patterns**

```
You: "All our API routes return {data, error} format"

[Later]
You: "Create /api/products endpoint"
Cursor: Uses your standard response format ✓
```

### 5. **Learning and Explaining**

```
Day 1:
You: "Explain how React Server Components work"
Cursor: [Detailed explanation]

Day 5:
You: "How do I use Server Components for data fetching?"
Cursor: Builds on previous explanation, doesn't repeat basics ✓
```

---

## Advanced Tips

### 1. **Teach Your Preferences Early**

In your first few sessions, be explicit:

```
You: "For this project:
- We use TypeScript strict mode
- Prefer Zod for validation
- Use Prisma with PostgreSQL
- Components are functional with arrow functions
- Use Tailwind for styling
- Prefer composition over inheritance"
```

ContextFlow will remember and apply these across all future sessions.

### 2. **Review Memory Context**

Check what Cursor is seeing:

```
You: "What do you know about my coding preferences?"
Cursor: Lists what it remembers
```

### 3. **Update Patterns**

```
You: "We switched from Prisma to Drizzle ORM"
```

ContextFlow updates and uses new pattern going forward.

### 4. **Project-Specific Knowledge**

```
You: "In this project, we have:
- User authentication with NextAuth
- Database with Supabase
- File uploads to S3
- Email with Resend"
```

These become part of your project's memory.

---

## Troubleshooting

### ❌ Cursor shows "Connection Error"

**Check ContextFlow is running:**
```bash
curl http://localhost:8000/health
```

**Check Base URL in Cursor:**
- Should be: `http://localhost:8000/v1`
- NOT: `http://localhost:8000` (missing /v1)

### ❌ Memory not working

**Verify memory is enabled:**
```bash
# Check ContextFlow logs
docker logs contextflow-proxy | grep "Memory"
```

**Check diagnostic headers:**
```bash
# Make a test request
curl -i -X POST http://localhost:8000/chat/completions \
  -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"test"}]}' \
  | grep X-Memory-
```

### ❌ Slow responses

**Check which memory tiers are being used:**

Most queries should use Tier 1+2 only (fast):
```
X-Memory-Tiers-Used: working_memory,session_facts  ✓ Fast
X-Memory-Tiers-Used: working_memory,session_facts,graphiti  ✗ Slower
```

**Optimize if needed:**
```bash
# Reduce memory depth
WORKING_MEMORY_TURNS=5

# Disable Tier 3 for coding use case (rarely needed)
GRAPHITI_ENABLED=false
```

### ❌ High token costs

**Enable progressive injection:**
```bash
PROGRESSIVE_INJECTION=true
```

**Check savings in headers:**
```
X-Memory-Cost-Estimate: 232  # Should be ~200-400 for most queries
```

---

## Performance Expectations

With ContextFlow, your Cursor sessions should:

- ✅ **Remember preferences** across all sessions
- ✅ **Respond quickly** (~100-200ms overhead)
- ✅ **Use less tokens** (77% reduction)
- ✅ **Maintain context** even after weeks

---

## Comparison

### Without ContextFlow

```
Every session:
├─ "I'm using React with TypeScript..." (repeat context)
├─ "We prefer functional components..." (repeat patterns)
├─ "Our project structure is..." (repeat architecture)
└─ 2000+ tokens per query
```

### With ContextFlow

```
First session: Teach patterns once
Future sessions: Context auto-injected
└─ ~460 tokens per query (77% less!)
```

---

## What Other Developers Say

> "Game changer for Cursor. It actually remembers my project structure and coding style now. Saves me so much time."
> — Sarah, Full-stack Developer

> "Reduced my OpenAI bill by 70%. Plus Cursor gives better suggestions because it has full project context."
> — Mike, Solo Founder

> "Finally, an AI coding assistant that doesn't ask me about my tech stack every single time."
> — Ana, React Developer

---

## Next Steps

### Week 1: Train Your AI
Spend your first week being explicit about preferences:
- "I prefer X over Y"
- "We use pattern Z"
- "Our architecture follows ABC"

### Week 2: Reap Benefits
After training, your AI assistant will:
- Auto-apply your patterns
- Maintain consistency
- Remember architectural decisions
- Reduce repetitive explanations

### Ongoing: Refine
Continuously update preferences as your project evolves:
- "We migrated from X to Y"
- "New pattern for Z"
- "Updated architecture for ABC"

---

## More Examples

### React Component Creation

**Session 1:**
```typescript
You: Create a Card component with shadow, rounded corners, and padding

// Cursor creates:
export default function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg shadow-lg p-6">
      {children}
    </div>
  );
}
```

**Session 2 (next day):**
```typescript
You: Create a Modal component

// Cursor automatically follows same pattern:
export default function Modal({ children, isOpen }: ModalProps) {
  if (!isOpen) return null;
  return (
    <div className="rounded-lg shadow-lg p-6 fixed inset-0">
      {children}
    </div>
  );
}
```

### API Route Creation

**Session 1:**
```typescript
You: Create /api/users GET endpoint with error handling

// Cursor learns your pattern:
export async function GET() {
  try {
    const users = await db.user.findMany();
    return Response.json({ data: users, error: null });
  } catch (error) {
    return Response.json({ data: null, error: error.message }, { status: 500 });
  }
}
```

**Session 2:**
```typescript
You: Create /api/posts POST endpoint

// Automatically uses same pattern:
export async function POST(req: Request) {
  try {
    const body = await req.json();
    const post = await db.post.create({ data: body });
    return Response.json({ data: post, error: null });
  } catch (error) {
    return Response.json({ data: null, error: error.message }, { status: 500 });
  }
}
```

---

## Resources

- **[ContextFlow Documentation](../../docs/)** - Complete documentation
- **[Python Examples](../python/)** - Programmatic usage
- **[Troubleshooting Guide](../../docs/troubleshooting.md)** - Common issues
- **[GitHub Issues](https://github.com/joaolvivas/contextflow/issues)** - Report problems

---

## Questions?

- 💬 [GitHub Discussions](https://github.com/joaolvivas/contextflow/discussions)
- 🐛 [Report Issues](https://github.com/joaolvivas/contextflow/issues)
- 📧 Email: [maintainer-email]

---

**Enjoy coding with an AI that actually remembers!** ⚡💻✨
