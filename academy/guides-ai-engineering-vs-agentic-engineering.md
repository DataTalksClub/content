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
  heading: Read next
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

Job ads now mention "AI", "agents", "LLM" and "Claude Code" side by side. Below I explain what each term means, what companies ask for under each one, and how to choose based on the work you already do.

[DataTalks.Club Academy](/academy/) teaches both as full-time live programs in English for experienced developers in Germany. Join the waitlist for the [AI Engineering program](/academy/ai-engineering/?utm_source=article&utm_medium=article&utm_campaign=ai-engineering-vs-agentic-engineering&utm_content=top#signup-hero) or the [Agentic Engineering program](/academy/agentic-engineering/?utm_source=article&utm_medium=article&utm_campaign=ai-engineering-vs-agentic-engineering&utm_content=top#signup-hero).

## What AI Engineering Is

In AI engineering, you put AI into the product. Think of the shopping assistant in an online store, the assistant in your banking app, or a marketplace where you upload a photo of something you want to sell and the system recognizes what it is.

AI engineers call models from OpenAI, Anthropic or other providers and build things around those calls. They build agents and RAG (retrieval-augmented generation) systems, and they know how to evaluate a system once it's built. In some roles you train or fine-tune a model, but usually you use an API and build around it. For this path you need an engineering background.

## What Agentic Engineering Is

In agentic engineering, you use coding agents like Claude Code or Cursor to get more done as a software engineer. The agent writes most of the code, and you decide what to build and check the result.

In practice that means:

- giving tasks to AI
- making sure it does the work in a way that makes sense and doesn't make things up
- checking that a task the agent calls complete is actually complete
- organizing the work so you get what you wanted and the cost stays reasonable
- scaling up to many agents running in parallel

Some people call this AI native development, or just modern software engineering.

## How They Are Different

For AI engineering you need to know how AI works. For agentic engineering you need to know how to use AI.

- In AI engineering you build products where an LLM is part of the product, like assistants, search over company documents and agents that do tasks for users. In agentic engineering you build any kind of software, with coding agents.
- In AI engineering your day is about retrieval, prompts, tool calling, evaluation datasets, tracing, cost and latency. In agentic engineering you write specs and small tasks, review the changes the agents make, look after tests, CI/CD and deployment, and run agents in parallel.
- AI engineers use LLM APIs from providers like OpenAI or Anthropic, vector and hybrid search, agent frameworks and MCP. Agentic engineers use Claude Code, Cursor, Copilot or Codex, plus skills, subagents, hooks and MCP.
- In an interview, an AI engineer shows an AI application and explains where it works, where it fails and how they measured that. An agentic engineer shows a working product, and explains how they tested and released each change.

## What Companies Ask For in Each

Every month I collect job postings with the title "AI engineer" in Berlin, Amsterdam, London, New York and Los Angeles. I publish the analysis in the [AI Engineering Field Guide](https://github.com/alexeygrigorev/ai-engineering-field-guide). The same skills come up again and again: RAG, prompt engineering, LLM evaluation and MCP. Most AI engineers call a provider through an API, and they don't train models. In a sample of 83 AI engineering job ads that [match.dev](https://www.match.dev/post/how-to-hire-ai-engineers/) analysed, 10% asked for model training.

For software engineering roles, I see more and more postings that ask for Claude Code, Copilot, Cursor or Codex by name. Even when a posting doesn't mention them, employers assume you know how to use these tools.

## Which One to Pick If You Are a Backend Developer

Both work. If you already build services and APIs in Python, AI engineering is a natural next step: an assistant is just a service that calls an LLM API, retrieves documents and calls tools. If you want to ship whole features faster and work on the interface, the API and the database, start with agentic engineering.

## Which One to Pick If You Are a Frontend Developer

Agentic engineering is usually the easier place to start. You can keep working in JavaScript or TypeScript, and coding agents help you build full-stack features, not only the interface. AI engineering is a good second step once you're comfortable with Python and APIs.

## Which One to Pick If You Work with Data

AI engineering is usually closer to what you already do. Processing documents, keeping an index up to date with pipelines, and building evaluation datasets are all data work. You don't need a machine learning background or advanced mathematics, though.

## Where the Two Overlap

An AI engineer could build a tool like Claude Code, and a software engineer who works with agents may sometimes put AI into the product.

In DataTalks.Club Academy each program includes a module on the other one:

- the Agentic Engineering program includes an introduction to AI engineering, where you build an app on an LLM API with a chatbot, RAG over documents and a simple tool-calling agent
- the AI Engineering program starts on day 1 with agentic engineering basics and a working coding-agent setup, and then you use the full agent workflow on your project repository

## How to Learn Each

Start with the free courses. [AI Dev Tools Zoomcamp](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp) covers the basics of agentic engineering. [LLM Zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) covers building applications on top of LLMs.

If you want to go further full-time, DataTalks.Club Academy has two programs. Both are 3 months (13 weeks), full-time and live, Monday to Friday, 09:00 to 16:30 Berlin time. They're in English, in Berlin or live online, with 15 seats, and they start in April 2027. Bildungsgutschein funding is coming soon. To see how the voucher works, read the [Bildungsgutschein guide in English](/academy/guides/bildungsgutschein-in-english/) or the [German Bildungsgutschein guide](/academy/bildungsgutschein/).

I based the [Agentic Engineering program](/academy/agentic-engineering/) on AI Dev Tools Zoomcamp and on my experience running coding agents 24/7 for the last year. At the end, you ship a working web application for a real user task.

I based the [AI Engineering program](/academy/ai-engineering/) on LLM Zoomcamp, AI Engineering Buildcamp and my experience building AI products and putting them into production. At the end, you build and deploy an AI assistant for a concrete company use case.

I explained the difference live in the first Hireable With AI session. In the [session 1 recap](/academy/sessions/ai-engineering-vs-agentic-engineering/) you'll find my answers to the questions people asked.

## FAQ

### Is Agentic Engineering the Same as Building AI Agents?

No. Building agents that do tasks for users is part of AI engineering. In agentic engineering you use coding agents such as Claude Code or Cursor to write software, and you decide what to build and check the result.

### Do I Need a Machine Learning Background for Either One?

No. For both, you start from software development experience. In a sample of 83 AI engineering job ads that match.dev analysed, 10% asked for model training.

### Can I Learn Both?

Yes, and they work well together. In DataTalks.Club Academy each program includes a module on the other one.
