---
layout: article
path: /academy/guides/what-is-agentic-engineering/
title: "What Is Agentic Engineering? A Working Developer's Guide | DataTalks.Club Academy"
description: Agentic engineering means coding agents write most of the code while you decide what to build and check the result. How the work changes for developers.
og_image: images/academy/og/home.png
sitemap: 6
eyebrow: Guide
heading: 'What Is Agentic Engineering: How I Build Software with Coding Agents'
lead: Agentic engineering is using tools like Claude Code or Cursor to write most of the code, while you decide what to build and check the result. The developer writes the spec, splits it into small tasks, reviews every change and runs the tests before anything ships. It is still software engineering, and you answer for what goes to production.
author: Alexey Grigorev
published: '2026-11-24'
related:
  heading: Read next
  links:
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

The [Agentic Engineering program](/academy/agentic-engineering/) of DataTalks.Club Academy is a full-time live program in English for developers in Germany with 2+ years of experience. [Join the Waitlist](/academy/agentic-engineering/?utm_source=article&utm_medium=article&utm_campaign=what-is-agentic-engineering&utm_content=top#signup-hero).

## What Agentic Engineering Means

There are two ways a developer can use AI at work, and people often mix them up. In AI engineering, you put AI into the product: you call a model from your code and build a chatbot, a search feature or an agent for your users. In agentic engineering, you use AI to get more done as a software engineer. For the first you need to know how AI works, and for the second you need to know how to use AI.

The tools are coding agents like Claude Code, Codex, Cursor or GitHub Copilot's agent mode. They read your repository, edit files, run commands and tests, and keep going until the task is done. You give them the task and you check the result.

In agentic engineering, the questions are practical:

- How do I give tasks to an agent?
- How do I make sure it does them in a way that makes sense, and doesn't make things up?
- When the agent says the task is complete, how do I know it's complete?
- How do I keep it from getting expensive?
- How do I run many agents in parallel, 10 or 15 of them?

You may also hear it called AI native development or simply modern software engineering. For a side-by-side comparison, read [AI Engineering vs Agentic Engineering](/academy/guides/ai-engineering-vs-agentic-engineering/).

## How My Work Changed Since I Started Using Agents

I've been running coding agents 24/7 for the last year, and I write a lot about it on my [Substack](https://aishippingblog.com/). The biggest change is where my time goes. I spend it saying precisely what I want and checking what came back, not typing code.

This is how I usually work:

1. I write the spec first. I start with a vague idea and turn it into a plan before any code is written. I brainstorm the scope with a chat assistant, one question at a time, and save the result as a plan file in the repository.
2. I ask the agent to break the plan into a backlog of tasks, where each task fits one session and someone who hasn't read the others can pick it up. I review the list: merge tiny tasks, split big ones, remove what's outside the first version. The tasks go into GitHub issues.
3. For bigger projects, I give agents roles. One acts as a product manager and writes acceptance criteria for each issue, another acts as a software engineer and implements it with tests, and a third acts as a QA engineer and checks each criterion against what the code does. The main session coordinates them and does none of the work.
4. I run the agents in parallel, each in its own git worktree, and finished work goes into main one issue at a time.

I described this in detail in [AI Native Development: Specifications](https://aishippingblog.com/p/ai-native-development-specifications) and [Coding Agent Building Blocks](https://aishippingblog.com/p/coding-agent-building-blocks-reusable). I also made the slides for my first Hireable With AI session with Claude Code.

## What I Still Do Myself

The agent writes most of the code.

I still do these parts myself:

- I decide what to build: the scope, what goes into the first version and what doesn't.
- I choose the stack. I pick tools I know well enough to review what the agent writes with them, and in one recent project I chose Django for exactly that reason.
- I review the plan and the tasks. Fixing a misunderstanding in a paragraph is cheap. Fixing it in code isn't.
- I keep the instructions up to date, with the project rules in an `AGENTS.md` file and supporting docs next to it. When I correct an agent, I update the docs, so I don't have to make the same correction again.
- I commit often, after every meaningful decision, so I can always go back.
- I say when it's done. I don't call the work finished until it passes the checks.

## Where Agents Make Mistakes

Agents are capable, and that's part of the problem.

These are the mistakes I see most often:

- When I leave something out, they fill it in with assumptions. Once I gave an agent a vague idea for a feedback tool and got back a different product, a command line tool with 62 passing tests. It was my fault for not saying what I wanted. A capable agent can build the wrong thing efficiently.
- They stop too early or run forever. Agents often stop to ask for permission, and they need a stop condition they can check.
- They grade their own homework. An agent that reviews its own work is biased by what it just did and can skip checks. That's why I give testing to a separate agent with a fresh context.
- They forget. In a long session the agent starts to forget what happened at the beginning, so I start a new focused session for each task.
- They cost money. Running many agents in different roles takes time and tokens, and often a simple prompt or a loop is enough.

## How Agentic Engineering Differs from Vibe Coding

The difference is verification. In vibe coding, you describe what you want and accept what the tool produces. In agentic engineering, you write the spec, review every change and run the tests before anything ships.

Both use the same tools. Vibe coding is fine for a prototype you'll throw away, but for software that other people use, you need agentic engineering.

## What Companies Expect from Developers Who Use Agents

More and more job ads for software engineers name Claude Code, Copilot, Cursor or Codex. Even when an ad doesn't mention them, companies assume you know how to use these tools. We counted developer jobs in Germany on arbeitnow in the week of 7 to 14 November 2026: 86 of 588 ads named Claude Code, Cursor, Copilot, Codex or AI-assisted coding. It's an approximate count, since we just searched the ad texts for these terms.

The tools are already widely used. In the Stack Overflow Developer Survey 2026, 66% of respondents said they use coding assistants or coding agents. Nearly half said they trust AI when they can verify its work ([Stack Overflow, 6 October 2026](https://stackoverflow.co/company/press/archive/stack-overflow-annual-developer-survey-ai-trust-conditional/)). So companies need developers who can check the AI's work.

## What to Practise First

I'd practise these, in this order:

1. Take a feature, write a short spec and split it into tasks an agent can finish in one session.
2. Let an agent work in an existing codebase, a real repository with history and conventions, not only on a new project.
3. Make sure the agent writes tests and that they check what matters.
4. Read every diff before you merge it, and learn when to send a task back.
5. Set up CI, so the pipeline runs the checks on every change and "done" means the same thing every time.

## Where to Learn It

Start with [AI Dev Tools Zoomcamp](/courses/ai-dev-tools-zoomcamp), my free course on the basics of agentic engineering. It covers specification-driven development and how to set up a team of agents that work on tasks.

If you want to practise this full-time with a group, there's the [Agentic Engineering program](/academy/agentic-engineering/). I based it on AI Dev Tools Zoomcamp and my experience running coding agents 24/7 for the last year. You take an idea to production: specs, a local version, deployment, CI/CD, monitoring and running agents in parallel. The [AI Engineering program](/academy/ai-engineering/) also covers working with coding agents, as part of building products on LLMs.

Both programs run 3 months (13 weeks), Monday to Friday, 09:00 to 16:30 Berlin time, in Berlin or live online, with 15 seats. Both start in April 2027. Bildungsgutschein funding is coming soon, and the [German Bildungsgutschein guide](/academy/bildungsgutschein/) explains how it works.

## FAQ

### Is Agentic Engineering the Same as Vibe Coding?

No. In vibe coding you accept what the tool produces. In agentic engineering you write the spec, review every change and run tests before anything ships.

### Which Tools Count as Coding Agents?

Claude Code, Codex, Cursor and GitHub Copilot's agent mode. They read your repository, edit files, and run commands and tests until the task is done.

### Do I Need Experience with Coding Agents to Start Learning Agentic Engineering?

No. You need to be able to read and write code, use Git and the command line, and run tests.
