---
layout: program
path: /academy/ai-engineering/
title: AI Engineering Course in English for Experienced Developers | DataTalks.Club Academy
description: 'Learn to build and evaluate LLM products. Full-time live program in English for developers with 2+ years in Germany. Start: April 2027, 15 seats.'
og_image: images/academy/og/ai-engineering.png
sitemap: 3
program:
  slug: ai-engineering
  name: AI Engineering
  label: B
  survey_option: B. AI engineering
highlights:
- Build LLM assistants with search and tools.
- Evaluate answers and catch regressions.
- Deploy, trace and monitor in production.
hero:
  eyebrow: AI Engineering
  headline: Build and Evaluate LLM Applications
  lead: 'AI Engineering is a 3-month full-time live program in English for developers with 2+ years of experience in Germany. You learn to build and evaluate products that use LLMs, like chatbots, search over company documents and agents.'
  basis: This program turns AI Engineering Buildcamp, the course I have taught for a year and a half, into a full-time program. It also builds on LLM Zoomcamp and my experience building AI products and putting them in production.
outcomes:
  heading: What You Can Do by the End
  intro: Build an AI application, and show where it works and where it fails.
  items:
  - Build an assistant in Python on an LLM API.
  - Use retrieval-augmented generation (RAG) and document processing over company data, and keep the index up to date as documents change.
  - Give the assistant tools, function calling and MCP connections to look things up or call an API.
  - Define what it can do on its own and when it needs human approval.
  - Build evaluation datasets from realistic tasks, evaluate answers and tool use, compare prompts and models, and catch regressions.
  - Deploy the application to the cloud and trace its model and tool calls.
  - Track quality, latency and cost, and handle failures safely with guardrails.
  - Use agentic engineering in your own AI engineering work.
  - Run local models on GPUs rented in the cloud. The program spends at least one week on local models.
  - Network, find projects to solve and build portfolio projects, with mock interviews.
overview:
  heading: Why This Program
  paragraphs:
  - Companies want assistants and agents that work on their own data. A demo on an LLM API is quick to build and hard to trust. If you already write software, what you need is practice building these systems and showing where they work and where they fail.
  - The program covers retrieval, agents and tools, evaluation, deployment, monitoring and safety, and spends at least one week on local models.
  - It is full-time and live, and you work on one assistant that grows every week.
project: You build and deploy an AI assistant for a concrete company use case, for example one that answers questions from messy internal documents that keep changing, with sources and carries out actions after human approval. You show where it works, where it fails, and how you measured that.
fit_first: You program today, ideally in Python, and can use APIs and work in a repository.
prerequisites: You are comfortable programming, preferably in Python, and you can use the command line, Git and basic Docker. You don't need a machine-learning background, advanced mathematics or a GPU. A laptop with internet access is enough.
syllabus:
- title: Retrieval
  modules:
  - week: 1
    title: Set up coding agents and a Python service on an LLM API.
    produce: A working coding-agent setup (day 1) and a small API that returns validated, structured answers.
  - week: 2
    title: Process, index and retrieve documents.
    produce: A one-command ingestion pipeline you can rerun safely and a knowledge assistant with sources.
  - week: 3
    title: Compare vector and hybrid search.
    produce: Three retrieval variants, with examples of where each fails.
  - week: 4
    title: Evaluate retrieval.
    produce: A first evaluation dataset, a retrieval evaluation and a justified configuration.
- title: Agents
  modules:
  - week: 5
    title: Run the agentic engineering workflow and the agent loop.
    produce: The full agent workflow on your project repo (spec to tasks, tests, diff review, CI) and an assistant that calls an API through a tool.
  - week: 6
    title: Use agent frameworks, MCP and context.
    produce: The assistant rebuilt on a framework, with one MCP tool.
  - week: 7
    title: Serve and deploy to the cloud.
    produce: A deployed assistant with cited answers and one tool (midterm).
  - week: 7
    title: Add human approval to agentic workflows.
    produce: A workflow action that waits for approval and handles refusal.
- title: Quality and Production
  modules:
  - week: 8
    title: Keep data fresh and build evaluation datasets.
    produce: A pipeline that keeps your assistant's index up to date, with a freshness report, and a versioned evaluation dataset for your project.
  - week: 8
    title: Test and evaluate answers and agents.
    produce: A regression suite running in CI and an evaluation report comparing two configurations.
  - week: 9
    title: Trace, monitor and control cost and latency.
    produce: Traces, dashboards that include data freshness, and a cost and latency report with a measured improvement.
  - week: 9
    title: Add guardrails, injection defenses and compliance.
    produce: Tested guardrails and a short compliance checklist.
capstone:
  heading: The Final Project
  modules:
  - week: 10
    title: Build the core of your assistant.
    produce: The 60-hour core of your final project, tested on real questions.
  - week: 11
    title: Deploy and defend it.
    produce: The deployed assistant with evaluation evidence, and its defense.
related:
  heading: Read next
  links:
  - label: 'AI Engineering vs Agentic Engineering: Which One Should an Experienced Developer Learn'
    href: /academy/guides/ai-engineering-vs-agentic-engineering/
  - label: 'Bildungsgutschein in English: How the Education Voucher Works for Developers in Germany'
    href: /academy/guides/bildungsgutschein-in-english/
  - label: How to Get Hired as an Experienced Developer in an AI Job Market
    href: /academy/guides/getting-hired-with-ai/
schema:
  start_date: 2027-04
  course_modes:
  - full-time
  - Online
  - Onsite
  location: Berlin
  country: DE
  instructor: Alexey Grigorev
  provider: DataTalks.Club
  provider_url: https://datatalks.club
---
