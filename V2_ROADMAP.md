# 🚀 V2 Roadmap: Job Search Automation + Persistent Memory

## Based on User Interview (2025-11-05)

### User Profile
- **Volume:** 5 applications/day (high velocity)
- **Pain Points:**
  1. Company research (biggest time sink)
  2. No tracking system (applications go into void)
  3. No persistent memory (re-explaining context constantly)
- **Tools:** Msty (ChatGPT + Claude), Twenty CRM (self-hosted), Obsidian, Gmail, Calendar
- **Workflow:** Morning = AI experimentation, then job search
- **Learning Style:** Conversational, no formal notes
- **Vision:** Multi-agent team working autonomously

---

## 🎯 V2 FOCUS: Persistent Memory + Job Application Intelligence

### Core Philosophy
**Transform from:** "Memory layer that remembers conversations"
**Into:** "AI Chief of Staff that researches companies, tracks applications, and maintains context forever"

---

## 📦 Phase 1: Foundation (Week 1) - $50 budget

### 1.1 Persistent Memory Across All Conversations ⭐⭐⭐
**Problem:** You talk to ChatGPT via Msty, then Claude via Msty - they don't share context

**Solution:**
- All conversations through proxy store to same Graphiti knowledge graph
- Memories persist across models, sessions, days
- Each LLM gets enriched with SAME personal context

**Implementation:**
- Add namespace support: `user_profile`, `job_applications`, `companies`, `learning`
- Every conversation adds episodes to graph
- Cross-session memory retrieval

**User Experience:**
```
[Morning - ChatGPT via Msty]
You: "I'm applying to AI-focused startups in SF"

[Afternoon - Claude via Msty]
You: "Help me with this cover letter"
Claude: [Retrieves from shared memory]
        "Based on your focus on AI startups in SF, here's a draft..."
```

### 1.2 Application Auto-Tracking ⭐⭐⭐
**Problem:** 5 apps/day, zero tracking, no follow-up system

**Solution:**
- Proxy detects application events in conversation
- Extracts: company, role, date, stage, job URL
- Stores in structured format

**Trigger phrases:**
- "Applied to X"
- "Submitted application for Y"
- "Just sent my resume to Z"

**Implementation:**
- Entity extraction from user messages
- Structured storage in Graphiti with `application` namespace
- Timestamped, searchable

**User Experience:**
```
You: "Just applied to Linear's Growth Engineer role via their careers page"
Proxy: [Detects application event]
       [Stores: company=Linear, role=Growth Engineer, date=2025-11-05,
        stage=applied, source=careers_page]

You: "What companies have I applied to this week?"
Claude: "You've applied to 23 companies this week:
         - Linear (Growth Engineer) - 2 hours ago
         - Vercel (Marketing Engineer) - Yesterday
         - Notion (Product Marketing) - 3 days ago
         ..."
```

---

## 📦 Phase 2: Intelligence Layer (Week 2) - $75 budget

### 2.1 Automated Company Research Agent ⭐⭐⭐⭐
**Problem:** Company research eats 70% of application time

**Solution:**
- Research Agent that auto-gathers company intel
- Triggered by: "Research [Company]" or "I'm applying to [Company]"
- Stores findings in knowledge graph for reuse

**Data Sources (Progressive Enhancement):**

**MVP (Free):**
- Company website scraping (About, Careers, Blog)
- LinkedIn company page (public info)
- Recent news via Google search

**Enhanced (API):**
- Crunchbase API (funding, investors, team size)
- Clearbit/BuiltWith (tech stack)
- Y Combinator DB (if YC company)

**What it gathers:**
- Company stage (seed, Series A, etc.)
- Funding amount & investors
- Team size & key hires
- Recent news (launches, acquisitions)
- Tech stack (relevant for engineering roles)
- Company values/culture signals
- Remote work policy
- Hiring velocity

**Implementation:**
```typescript
// src/agents/research-agent.ts

async function researchCompany(companyName: string) {
  // 1. Scrape company website
  const aboutPage = await scrapeWebsite(`${companyWebsite}/about`)

  // 2. Check Crunchbase (if API key available)
  const fundingData = await getCrunchbaseData(companyName)

  // 3. Search recent news
  const news = await searchNews(companyName, days=30)

  // 4. Structure and store
  await graphiti.addEpisode({
    content: `Company: ${companyName}
              Stage: ${fundingData.stage}
              Funding: $${fundingData.totalFunding}
              Team: ${fundingData.employeeCount}
              Recent: ${news[0].headline}
              Tech: ${techStack.join(', ')}
              Remote: ${remotePolicy}`,
    name: `company_research_${companyName}`,
    tags: ['company', 'research', companyName.toLowerCase()]
  })

  return researchSummary
}
```

**User Experience:**
```
You: "I'm applying to Vercel"
Proxy: [Triggers Research Agent]
       [2 seconds later]

Claude: "Vercel Research Summary:

         📊 Company Profile:
         - Stage: Series C ($150M raised)
         - Investors: Accel, GV, Bedrock
         - Team: ~200 employees, growing fast
         - HQ: San Francisco (Remote-friendly)

         🚀 Recent Activity:
         - Launched v1 SDK (Oct 2025)
         - Acquired Turborepo team
         - Hiring 15 roles (3 in marketing)

         💻 Tech Stack:
         - Next.js, React, TypeScript
         - Edge computing focus

         🎯 Why You're a Fit:
         - They value performance marketing (your TikTok background)
         - Technical marketing roles (your AI + marketing combo)
         - Remote-first culture

         Want me to draft a tailored cover letter?"
```

### 2.2 Twenty CRM Integration ⭐⭐⭐
**Problem:** Applications tracked in memory but not visible/manageable

**Solution:**
- Auto-sync applications to Twenty CRM via API
- Two-way sync: proxy → CRM, CRM → proxy
- Dashboard for visual pipeline management

**Implementation:**
```typescript
// src/integrations/twenty-crm.ts

async function syncToTwentyCRM(application: Application) {
  const crm = new TwentyClient(config.twenty.apiUrl, config.twenty.apiKey)

  await crm.createOpportunity({
    name: `${application.company} - ${application.role}`,
    stage: application.stage, // applied, interview, offer, rejected
    company: application.company,
    role: application.role,
    appliedDate: application.date,
    jobUrl: application.url,
    notes: application.researchSummary,
    followUpDate: calculateFollowUp(application.date), // +5 days
  })
}

// Webhook handler for CRM updates
app.post('/webhook/twenty-crm', async (req, res) => {
  const { event, opportunity } = req.body

  if (event === 'opportunity.updated') {
    // Update knowledge graph with CRM changes
    await updateApplicationStatus(opportunity)
  }
})
```

**User Experience:**
```
You: "Applied to Notion Product Marketing Manager role"
Proxy: [Creates application in memory + Twenty CRM]

[You open Twenty CRM dashboard]
- See: Notion card in "Applied" column
- Notes: Auto-populated with research summary
- Follow-up: Auto-scheduled for 5 days from now

[You move Notion to "Interview" in CRM]
Proxy: [Detects webhook, updates memory]

You: "What's my interview pipeline?"
Claude: "You have 3 interviews scheduled:
         - Notion (Product Marketing) - moved to interview stage today
         - Linear (Growth) - phone screen tomorrow
         - Vercel (Marketing Engineer) - take-home in progress"
```

### 2.3 Personal Brand Memory Database ⭐⭐
**Problem:** Re-typing accomplishments for every cover letter

**Solution:**
- Structured accomplishments database
- Tagged by: skill, metric, company, domain
- Auto-retrieval for cover letters

**Implementation:**
```typescript
// One-time setup conversation
You: "Let me tell you my key accomplishments:

      1. Scaled TikTok campaigns from $5K to $15K/day, achieving 3.2 ROAS
      2. Generated $700K monthly revenue for DTC brand in Q4 2024
      3. Built custom attribution model reducing CPA by 40%
      4. Managed $2M annual ad budget across Meta, TikTok, Google
      5. Led creative testing framework improving CTR by 60%
      6. Launched 15+ successful product launches
      7. Built this memory orchestrator proxy (TypeScript, MCP, AI)
      8. Contributed to open-source AI projects"

Proxy: [Structures as:]
{
  accomplishments: [
    {
      id: 1,
      description: "Scaled TikTok campaigns from $5K to $15K/day",
      metric: "3.2 ROAS",
      tags: ["tiktok", "paid_social", "scaling", "performance_marketing"],
      domain: "marketing",
      impact: "high"
    },
    {
      id: 7,
      description: "Built memory orchestrator proxy",
      metric: "Full-stack TypeScript project",
      tags: ["typescript", "ai", "mcp", "backend", "api_design"],
      domain: "engineering",
      impact: "high"
    }
  ]
}

// Later when writing cover letters
You: "Cover letter for this AI Marketing Engineer role at Vercel"

Claude: [Proxy retrieves relevant accomplishments]
        [Matches: TikTok scaling + proxy building + technical background]

        "Dear Vercel Team,

        I'm excited to apply for the AI Marketing Engineer role. My background
        uniquely combines performance marketing execution with AI engineering:

        Marketing Impact:
        - Scaled TikTok campaigns to $15K/day achieving 3.2 ROAS
        - Generated $700K monthly revenue through data-driven optimization

        Technical Execution:
        - Built production AI systems (memory orchestrator with MCP integration)
        - Proficient in TypeScript, API design, and LLM orchestration

        This role is perfect intersection of my skills..."
```

---

## 📦 Phase 3: Multi-Agent Orchestration (Week 3) - $75 budget

### 3.1 Agent Orchestrator Framework ⭐⭐⭐
**Problem:** You want "team of AI agents" but unclear what's possible

**Solution:**
- Multi-agent system where specialized agents work in parallel
- Each agent has specific role and tools
- Orchestrator coordinates based on task

**Agents:**

**Research Agent:**
- Scrapes company websites
- Calls external APIs (Crunchbase, Clearbit)
- Stores findings in knowledge graph

**Writing Agent:**
- Generates cover letters
- Drafts follow-up emails
- Uses personal brand memory

**Tracking Agent:**
- Monitors application status
- Calculates follow-up dates
- Syncs with Twenty CRM

**Learning Agent:**
- Curates resources based on your goals
- Identifies knowledge gaps
- Suggests next topics

**Implementation:**
```typescript
// src/orchestrator/agent-system.ts

class AgentOrchestrator {
  agents = {
    research: new ResearchAgent(),
    writing: new WritingAgent(),
    tracking: new TrackingAgent(),
    learning: new LearningAgent(),
  }

  async processTask(userMessage: string, context: any) {
    // Analyze intent
    const intent = this.detectIntent(userMessage)

    // Route to appropriate agent(s)
    switch(intent) {
      case 'apply_to_job':
        // Parallel execution
        const [research, tracking] = await Promise.all([
          this.agents.research.researchCompany(context.company),
          this.agents.tracking.createApplication(context)
        ])

        // Sequential: writing needs research results
        const coverLetter = await this.agents.writing.generateCoverLetter({
          company: context.company,
          research,
          userProfile: context.userProfile
        })

        return { research, coverLetter, tracking }

      case 'daily_briefing':
        const briefing = await this.agents.tracking.getDailyBriefing()
        return briefing

      case 'learning_question':
        const resources = await this.agents.learning.findResources(context.topic)
        return resources
    }
  }
}
```

**User Experience:**
```
You: "I want to apply to Stripe's Growth Marketing role"

Proxy: [Orchestrator activates multiple agents]

Research Agent: [Scraping Stripe website, checking Crunchbase]
Tracking Agent: [Creating application record in Twenty CRM]
Writing Agent: [Standby, waiting for research]

[3 seconds later]

Claude: "I've researched Stripe and drafted your application materials:

         📊 Stripe Research:
         - Fintech leader, $95B valuation
         - 8,000+ employees, hiring in marketing
         - Recent: Launched embedded finance APIs
         - Culture: Data-driven, customer-obsessed

         ✍️ Cover Letter Draft:
         [Tailored letter emphasizing your data-driven marketing
          and how it aligns with Stripe's culture]

         ✅ Tracked:
         - Added to Twenty CRM in 'Applied' stage
         - Follow-up reminder set for Nov 10

         Ready to submit? I can also draft the application form
         answers if you share the questions."
```

### 3.2 Proactive Daily Briefing ⭐⭐
**Problem:** No structure to daily workflow

**Solution:**
- Morning briefing generated automatically
- Prioritizes based on urgency and deadlines
- Suggests time blocks

**Triggers:**
- First conversation of the day
- Scheduled webhook at 8am
- Manual: "What should I do today?"

**User Experience:**
```
[8:00 AM - First Msty conversation]

Claude: "☀️ Good morning! Here's your briefing for Tuesday, Nov 5:

         🔴 URGENT (Today):
         - Linear: Follow up (applied 7 days ago, no response)
         - Vercel: Finish take-home assignment (due tomorrow)

         🟡 THIS WEEK:
         - Apply to 3 target companies (Notion, Retool, Replit)
         - Prepare for Faire phone screen (Friday 2pm)

         📚 LEARNING:
         - Continue: Remote MCP server tutorial (50% done)
         - New resource: Multi-agent systems course (saved yesterday)

         💡 SUGGESTED SCHEDULE:
         9-11am: Vercel take-home (deep work)
         11:30am: Draft Linear follow-up email
         1-2pm: Apply to Notion + research
         2-3:30pm: MCP tutorial

         What do you want to tackle first?"
```

### 3.3 Smart Follow-Up System ⭐⭐
**Problem:** Forgetting to follow up with companies

**Solution:**
- Auto-calculates optimal follow-up timing
- Drafts follow-up emails
- Tracks response patterns

**Logic:**
- Day 5: "No response yet, typical for this stage"
- Day 7: "Consider following up"
- Day 10: "Send follow-up email (drafted for you)"
- Day 14: "Move to rejected, focus elsewhere"

**User Experience:**
```
You: "What needs my attention?"
Claude: "You have 3 applications needing follow-up:

         1. Shopify (Applied Oct 29, 7 days ago)
            Status: No response
            Action: Send follow-up email

            Draft: 'Hi [Recruiter], I applied to the Performance Marketing
                    role last week and wanted to reiterate my interest...'

         2. Linear (Applied Oct 27, 9 days ago)
            Status: No response
            Action: Consider moving on (avg response time is 5 days)

         3. Notion (Applied Nov 2, 3 days ago)
            Status: Normal timeline, wait 2 more days

         Want me to send the Shopify follow-up?"
```

---

## 📦 Phase 4: Advanced Integrations (Week 4) - $50 budget

### 4.1 Obsidian Sync ⭐
**Problem:** Knowledge scattered between conversations and notes

**Solution:**
- Auto-export memories to Obsidian as markdown
- Organize by: companies, learnings, applications
- Bidirectional: notes → knowledge graph

**Structure:**
```
Obsidian/
├── Companies/
│   ├── Linear.md (research notes)
│   ├── Vercel.md
│   └── Notion.md
├── Applications/
│   ├── 2025-11-01-Linear-Growth.md
│   └── 2025-11-05-Vercel-Marketing.md
└── Learning/
    ├── MCP-Servers.md
    └── Multi-Agent-Systems.md
```

### 4.2 Gmail Integration ⭐
**Problem:** Follow-ups require copying from chat to email

**Solution:**
- Draft emails directly via Gmail API
- Optional: Send automatically with confirmation
- Track email threads in knowledge graph

**User Experience:**
```
You: "Send the Shopify follow-up"
Claude: "📧 Email drafted and ready to send:

         To: recruiting@shopify.com
         Subject: Re: Performance Marketing Manager Application

         [Email preview]

         Send now? (yes/no)"

You: "yes"
Claude: "✅ Sent! I'll track replies and notify you."
```

### 4.3 Webhook Notifications (Proactive AI) ⭐⭐
**Problem:** Have to initiate every conversation

**Solution:**
- Proxy sends notifications when action needed
- Slack/Discord/Email based on preference
- Time-sensitive reminders

**Triggers:**
- Application needs follow-up
- Interview coming up (24h reminder)
- Take-home deadline approaching
- Daily briefing ready

**User Experience:**
```
[Slack notification - 9am]
🤖 Morning Briefing Ready
"You have 2 urgent items today. Open Msty to see your daily plan."

[Slack notification - 2pm]
🚨 Reminder: Vercel Take-Home
"Due tomorrow! Estimated 3 hours remaining. Block your afternoon?"

[Discord notification - next day]
📧 Shopify Responded!
"They replied to your follow-up. Want me to analyze and draft a response?"
```

---

## 🏗️ UPDATED ARCHITECTURE

```
Msty (ChatGPT, Claude, GPT-4, etc.)
        ↓
[Memory Orchestrator Proxy] :3000
        ↓
        ├─→ Graphiti MCP (persistent memory across all LLMs)
        │   └─→ Neo4j Knowledge Graph
        │       ├─ User Profile
        │       ├─ Job Applications
        │       ├─ Company Research
        │       ├─ Personal Accomplishments
        │       └─ Learning Resources
        │
        ├─→ Agent Orchestrator
        │   ├─→ Research Agent (web scraping, APIs)
        │   ├─→ Writing Agent (cover letters, emails)
        │   ├─→ Tracking Agent (applications, follow-ups)
        │   └─→ Learning Agent (resources, gaps)
        │
        ├─→ External Integrations
        │   ├─→ Twenty CRM API (job pipeline)
        │   ├─→ Obsidian (notes sync)
        │   ├─→ Gmail API (email automation)
        │   ├─→ Calendar (reminders)
        │   ├─→ Crunchbase API (company data)
        │   └─→ Webhook Server (Slack/Discord)
        │
        └─→ OpenAI API (enriched with ALL context)
```

---

## 💰 BUDGET BREAKDOWN

| Phase | Features | Est. Tokens | Cost |
|-------|----------|-------------|------|
| Phase 1 | Persistent memory + Auto-tracking | ~40K | ~$50 |
| Phase 2 | Research Agent + CRM + Brand DB | ~60K | ~$75 |
| Phase 3 | Multi-agent + Briefing + Follow-ups | ~60K | ~$75 |
| Phase 4 | Obsidian + Gmail + Webhooks | ~40K | ~$50 |
| **Total** | **Full V2 System** | **~200K** | **~$250** |

---

## 🎯 SUCCESS METRICS

**Before V2:**
- Applications: 5/day, zero tracking
- Company research: 30-45 min per company
- Follow-ups: Forgotten or manual reminders
- Context: Lost between conversations
- Cover letters: 20+ min each, repetitive

**After V2:**
- Applications: 5/day, 100% tracked in CRM
- Company research: 3 min (automated)
- Follow-ups: Automatic reminders + drafts
- Context: Persistent across all LLMs forever
- Cover letters: 5 min (auto-drafted from accomplishments)

**Time Saved:**
- Research: 27 min × 5 = **2h 15min/day**
- Cover letters: 15 min × 5 = **1h 15min/day**
- Tracking/admin: **30 min/day**
- **TOTAL: ~4 hours/day saved** → apply to 10+ companies or learn more

---

## 🚀 NEXT STEPS

1. **Confirm priorities**: Does this align with your vision?
2. **API keys needed**: Crunchbase, Twenty CRM, Gmail (which do you have?)
3. **Start Phase 1**: Persistent memory + auto-tracking (foundation)
4. **Iterate based on usage**: Build what you actually use

**Ready to build V2?** 🎯
