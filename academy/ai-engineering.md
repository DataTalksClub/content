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
hero:
  eyebrow: Berlin or live online
  headline: Build and Evaluate LLM Applications
  lead: 'AI Engineering is a 3-month full-time live program in English for developers with 2+ years of experience in Germany. You learn to build and evaluate products that use LLMs, like chatbots, search over company documents and agents. Start: April 2027, 15 seats, designed for Bildungsgutschein funding (AZAV), coming soon.'
  basis: This program turns AI Engineering Buildcamp, the course I have taught for a year and a half, into a full-time bootcamp. It also builds on LLM Zoomcamp and my experience building AI products and putting them in production.
outcomes:
  heading: By the end you can build an AI application, and show where it works and where it fails.
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
  - Network, find projects to solve and build portfolio projects, with mock interviews. The program spends 2 to 3 weeks on this.
project: You build and deploy an AI assistant for a concrete company use case, for example one that answers questions from messy internal documents that keep changing, with sources and carries out actions after human approval. You show where it works, where it fails, and how you measured that.
fit_first: You program today, ideally in Python, and can use APIs and work in a repository.
prerequisites: You are comfortable programming, preferably in Python, and you can use the command line, Git and basic Docker. You don't need a machine-learning background, advanced mathematics or a GPU. A laptop with internet access is enough.
syllabus:
- weeks: Weeks 1 to 4
  title: Retrieval
  modules:
  - title: Agentic engineering basics and a Python service on an LLM API.
    produce: a working coding-agent setup (day 1) and a small API that returns validated, structured answers.
  - title: Retrieval, document processing and indexing.
    produce: a one-command ingestion pipeline you can rerun safely and a knowledge assistant with sources.
  - title: Vector and hybrid search.
    produce: three retrieval variants, with examples of where each fails.
  - title: Evaluating retrieval.
    produce: a first evaluation dataset, a retrieval evaluation and a justified configuration.
- weeks: Weeks 5 to 7
  title: Agents
  modules:
  - title: Agentic engineering workflow, tools and the agent loop.
    produce: the full agent workflow on your project repo (spec to tasks, tests, diff review, CI) and an assistant that calls an API through a tool.
  - title: Agent frameworks, MCP and context.
    produce: the assistant rebuilt on a framework, with one MCP tool.
  - title: Serving and cloud deployment.
    produce: a deployed assistant with cited answers and one tool (midterm).
  - title: Agentic workflows and human approval.
    produce: a workflow action that waits for approval and handles refusal.
- weeks: Weeks 8 to 9
  title: Quality and production
  modules:
  - title: Data Pipelines, Freshness and Evaluation Datasets
    produce: a pipeline that keeps your assistant's index up to date, with a freshness report, and a versioned evaluation dataset for your project.
    description: Most assistants work on the day you load the documents and get worse as the documents change. In this module you keep the data behind your assistant fresh and build the evaluation dataset you use for the rest of the program.
    topics:
    - 'Incremental ingestion: add, update and remove documents without rebuilding the index.'
    - 'Freshness: how old the index is, and what the assistant says when its data is stale.'
    - Building an evaluation dataset from real questions and documents, with synthetic cases for the gaps.
    - Versioning the evaluation dataset, and updating it when the documents change.
  - title: Testing and Evaluating Answers and Agents
    produce: a regression suite running in CI and an evaluation report comparing two configurations.
  - title: Tracing, monitoring, cost and latency.
    produce: traces, dashboards that include data freshness, and a cost and latency report with a measured improvement.
  - title: 'Safety: guardrails, injection and compliance.'
    produce: tested guardrails and a short compliance checklist.
- weeks: Weeks 10 to 13
  title: Capstone and interviews
  modules:
  - title: Technical interviews and hiring prep (full week, 30 hours).
    produce: algorithm coding drills without AI, a timed take-home, a project presentation and first peer mocks.
  - title: Capstone I and interview practice.
    produce: your 60-hour capstone assistant core alongside weekly coding drills and squad mock interviews.
  - title: Capstone II and interview practice.
    produce: evaluation evidence, improved assistant, mock interviews and project-talk rehearsals.
  - title: 'Capstone III: deploy, defence and career prep.'
    produce: the deployed assistant, defence, final 30 hours of interview practice and 3 individual 45-min career consultations plus written CV review.
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
