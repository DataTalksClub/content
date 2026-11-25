---
layout: article
path: /academy/guides/ai-engineering-vs-agentic-engineering/
title: AI Engineering vs Agentic Engineering for Developers | DataTalks.Club Academy
description: AI engineering is building apps on LLMs. Agentic engineering is shipping code with tools like Claude Code. How they differ and which to pick by background.
og_image: images/academy/og/home.png
sitemap: 6
eyebrow: Guide
heading: 'AI Engineering vs Agentic Engineering: Which One Should an Experienced Developer Learn'
lead: AI engineering is building apps that use LLMs, like chatbots, search over documents or agents. Agentic engineering is using tools like Claude Code or Cursor to write and ship code faster.
author: Alexey Grigorev
published: '2026-11-24'
related:
  heading: Read Next
  links:
  - label: The AI Engineering program
    href: /academy/ai-engineering/
  - label: The Agentic Engineering program
    href: /academy/agentic-engineering/
  - label: 'Session 1 recap: AI Engineering vs Agentic Engineering'
    href: /academy/sessions/ai-engineering-vs-agentic-engineering/
  - label: 'Guide: How to Get Hired as an Experienced Developer in an AI Job Market'
    href: /academy/guides/getting-hired-with-ai/
  - label: Questions about the Academy
    href: /academy/faq/
join:
  heading: Join the Waitlist
  text: 'Start: April 2027. Join the waitlist and you hear first when applications open.'
---

Job ads now mention "AI", "agents", "LLM" and "Claude Code" in the same breath, so this guide explains what each term means, what companies ask for under each, and how to choose based on the work you already do.

[DataTalks.Club Academy](/academy/) teaches both as full-time live programs in English for experienced developers in Germany. **Join the Waitlist** for the [AI Engineering program](/academy/ai-engineering/?utm_source=article&utm_medium=article&utm_campaign=ai-engineering-vs-agentic-engineering&utm_content=top#signup-hero) or the [Agentic Engineering program](/academy/agentic-engineering/?utm_source=article&utm_medium=article&utm_campaign=ai-engineering-vs-agentic-engineering&utm_content=top#signup-hero).

## What AI Engineering Is

AI engineering means you integrate AI into the product. Think of the shopping assistant in an online store, the assistant in your banking app, or a marketplace where you upload a photo of something you want to sell and the system recognizes what it is.

AI engineers make calls to OpenAI, Anthropic or other providers and build things around those calls. They build agents and RAG systems, and they know how to evaluate the system once it's built. In some roles you train or fine-tune a model, but usually you use an API and build things around it. For this path you need an engineering background.

## What Agentic Engineering Is

Agentic engineering means you use coding agents like Claude Code or Cursor to be more effective at your work as a software engineer. The agent writes most of the code, while you decide what to build and check the result.

In practice that means:

- giving tasks to AI
- making sure it does the work in a way that makes sense and doesn't make things up
- checking that a task the agent calls complete is actually complete
- organizing the process so the result is what you wanted and the cost stays reasonable
- scaling it to many agents running in parallel

Some people call this AI native development, or just modern software engineering.

## How They Are Different

For AI engineering you need to know how AI works. For agentic engineering you need to know how to use AI.

- **What you build.** AI engineering: products where an LLM is part of the product, like assistants, search over company documents and agents that do tasks for users. Agentic engineering: any software product, built with coding agents.
- **Daily work.** AI engineering: retrieval, prompts, tool calling, evaluation datasets, tracing, cost and latency. Agentic engineering: specs and small tasks, reviewing agent-generated changes, tests, CI/CD, deployment and running agents in parallel.
- **Tools.** AI engineering: LLM APIs from providers like OpenAI or Anthropic, vector and hybrid search, agent frameworks, MCP. Agentic engineering: Claude Code, Cursor, Copilot or Codex, plus skills, subagents, hooks and MCP.
- **What you show in an interview.** AI engineering: an AI application, with evidence of where it works, where it fails and how you measured that. Agentic engineering: a working product, and how you tested and released each change.

## What Companies Ask For in Each

Every month I collect job postings with the title "AI engineer" in Berlin, Amsterdam, London, New York and Los Angeles, and publish the analysis in the [AI Engineering Field Guide](https://github.com/alexeygrigorev/ai-engineering-field-guide). Companies ask again and again for RAG, prompt engineering, LLM evaluation and MCP. Most AI engineers call a provider through an API rather than train models. In a sample of 83 AI engineering job ads analysed by [match.dev](https://www.match.dev/post/how-to-hire-ai-engineers/), 10% asked for model training.

For software engineering roles, I see a growing number of postings that explicitly ask for Claude Code, Copilot, Cursor or Codex. Even when a posting doesn't mention them, employers assume you know how to use these tools.

## Which One to Pick If You Are a Backend Developer

Both fit. If you already build services and APIs in Python, AI engineering builds directly on that: an assistant is a service that calls an LLM API, retrieves documents and calls tools. If you want to ship whole features faster and work across the interface, the API and the database, start with agentic engineering.

## Which One to Pick If You Are a Frontend Developer

Agentic engineering is usually the easier start. You can keep working in JavaScript or TypeScript, and coding agents help you build full-stack features beyond the interface. AI engineering is a good second step once you're comfortable with Python and APIs.

## Which One to Pick If You Work with Data

AI engineering is usually the closer fit. Document processing, pipelines that keep an index up to date, and evaluation datasets are data work. You still don't need a machine learning background or advanced mathematics.

## Where the Two Overlap

The two directions overlap. An AI engineer could build a tool like Claude Code, and a software engineer who works with agents may sometimes integrate AI into the product. In DataTalks.Club Academy each program includes a module on the other:

- the Agentic Engineering program includes an introduction to AI engineering, where you build an LLM API app with a chatbot, RAG over documents and a simple tool-calling agent
- the AI Engineering program starts with agentic engineering basics, a working coding-agent setup on day 1, and uses the full agent workflow on your project repository

## How to Learn Each

Start with the free courses. [AI Dev Tools Zoomcamp](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp) covers the basics of agentic engineering. [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) covers building applications on top of LLMs.

If you want to go further full-time, DataTalks.Club Academy has two programs. Both are 3 months (13 weeks), full-time and live, Monday to Friday, 09:00 to 16:30 Berlin time, in English, in Berlin or live online, with 15 seats. Start: April 2027. Bildungsgutschein (coming soon). The [Bildungsgutschein guide in English](/academy/guides/bildungsgutschein-in-english/) explains how the voucher works, and there is also a [German Bildungsgutschein guide](/academy/bildungsgutschein/).

The [Agentic Engineering program](/academy/agentic-engineering/) builds on AI Dev Tools Zoomcamp and my experience running coding agents 24/7 for the last year. You finish by shipping a working web application for a real user task.

The [AI Engineering program](/academy/ai-engineering/) builds on LLM Zoomcamp, AI Engineering Buildcamp and my experience building AI products and putting them in production. You finish by building and deploying an AI assistant for a concrete company use case.

I explained the difference live in the first Hireable With AI session. The [session 1 recap](/academy/sessions/ai-engineering-vs-agentic-engineering/) has my answers to the questions people asked.

## FAQ

### Is Agentic Engineering the Same as Building AI Agents?

No. Building agents that do tasks for users is part of AI engineering. Agentic engineering means you use coding agents such as Claude Code or Cursor to write software, and you decide what to build and check the result.

### Do I Need a Machine Learning Background for Either One?

No. Both start from software development experience. In a sample of 83 AI engineering job ads analysed by match.dev, 10% asked for model training.

### Can I Learn Both?

Yes. They complement each other. In DataTalks.Club Academy each program includes a module on the other.
