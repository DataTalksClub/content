---
layout: article
path: /academy/sessions/ai-engineering-vs-agentic-engineering/
title: 'AI Engineering vs Agentic Engineering: Session 1 Recap and Answers | DataTalks.Club Academy'
description: 'Recap of Hireable With AI session 1 by Alexey Grigorev: the difference between AI engineering and agentic engineering, what companies ask for, and answers to attendee questions on hardware, funding and finding a job.'
og_image: images/academy/og/sessions.png
sitemap: 4
eyebrow: 'Hireable With AI, session 1'
heading: 'AI Engineering vs Agentic Engineering: Session 1 Recap and Answers'
lead: On 23 November 2026 I ran the first free Hireable With AI session for experienced developers. This is a short recap of the talk and my answers to the questions people asked.
author: Alexey Grigorev
published: '2026-11-23'
related:
  heading: Read Next
  links:
  - label: 'Guide: AI Engineering vs Agentic Engineering, Which One to Learn'
    href: /academy/guides/ai-engineering-vs-agentic-engineering/
  - label: 'Guide: How to Get Hired as an Experienced Developer in an AI Job Market'
    href: /academy/guides/getting-hired-with-ai/
  - label: The Agentic Engineering program
    href: /academy/agentic-engineering/
  - label: The AI Engineering program
    href: /academy/ai-engineering/
  - label: Questions about the Academy
    href: /academy/faq/
  - label: The next free sessions
    href: /academy/sessions/
join:
  heading: Join the Waitlist
  text: 'Start: April 2027. Join the waitlist and you hear first when applications open.'
# The session recording: paste its public YouTube URL here (youtube.com/watch?v=... or youtu.be/...).
# Empty shows "Recording coming soon" in the same frame.
recording: https://youtu.be/roiT85s5vxA
slides: images/academy/slides/session-1.pdf
---

## The Audience for This Session

I'm preparing a full-time course for experienced developers who already know how to program and want to learn AI skills. I'm based in Germany, and I want to run it for people who live and work in Germany.

Many courses funded through the Bildungsgutschein teach the basics, like installing Git or Docker. Few assume you already have experience. Most of the material on AI engineering and agentic engineering is also written for people who are getting started. I don't want to focus on basics.

## Two Directions: AI Engineering and Agentic Engineering

People often confuse these two. They overlap, but they're two different ways you as a developer can use AI at work. If you're choosing between the two programs, the [comparison guide](/academy/guides/ai-engineering-vs-agentic-engineering/) puts them side by side.

AI engineering means you integrate AI into the product. Think of the shopping assistant in an online store or the assistant in your banking app. Another example is a marketplace where you upload a photo of something you want to sell and the system recognizes what it is. AI engineers make calls to OpenAI, Anthropic or other providers and build things around those calls. For this path you need an engineering background.

Agentic engineering means you use tools like Claude Code to be more effective at your work as a software engineer. I made the slides for this session with Claude Code.

For AI engineering you need to know how AI works, and for agentic engineering you need to know how to use AI. An AI engineer could build a tool like Claude Code, and a software engineer who works with agents may sometimes integrate AI into the product. Most of the time, though, you have a feature to implement and you want to do it with AI in the most effective way.

## Skills Companies Ask AI Engineers For

Every month I collect job postings with the title "AI engineer" in Berlin, Amsterdam, London, New York and Los Angeles. I extract the responsibilities, use cases and skills from each posting, then publish the data in the [AI Engineering Field Guide](https://github.com/alexeygrigorev/ai-engineering-field-guide).

In these postings, companies ask again and again for RAG, prompt engineering, LLM evaluation and MCP. AI engineers build agents, build RAG systems and know how to evaluate the system once it's built. Most of them call a provider like OpenAI or Anthropic through an API. In some roles you train or fine-tune a model, but usually you use an API and build things around it.

## Agentic Engineering in Practice

I'm building a similar tracker for software engineering jobs. It's still work in progress, but I already see a growing number of postings that explicitly ask for Claude Code, Copilot, Cursor or Codex. Even when a posting doesn't mention them, employers assume you know how to use these tools.

In agentic engineering you do things like:

- giving tasks to AI
- making sure it does the work in a way that makes sense and doesn't make things up
- checking that a task the agent calls complete is actually complete
- organizing the process so the result is what you wanted and the cost stays reasonable
- scaling it to 10 or 15 agents running in parallel

Some people call this AI native development, or just modern software engineering.

## Funding Through the Bildungsgutschein

In Germany, the Agentur für Arbeit or the Jobcenter can fund training through the Bildungsgutschein. Bildungsgutschein funding for the full-time programs: coming soon.

You find a program, go to your adviser and explain why it's useful for your career. The adviser decides, and sometimes the answer is no.

Some advisers tell people to learn German first. German is a good investment of your time. But if the jobs you apply for are in English, you can explain why this program is more useful for you right now. Show the adviser which skills you're missing and how this course teaches them. I explain the details in the Bildungsgutschein guide, [in German](/academy/bildungsgutschein/) and [in English](/academy/guides/bildungsgutschein-in-english/).

## You Don't Need a Powerful Computer

Someone asked whether they need a machine that can run local LLMs. You don't, because a simple laptop with internet access is enough for both programs. A coding agent like Claude Code sends API requests to the model provider. An agent you build for a specific problem does the same.

In AI Engineering I want to spend at least one week on local models. We rent GPUs in the cloud for that, so you still only need a laptop and internet access. If you have a recent MacBook Pro, you can run some of these things locally, but you don't need to.

## Funding From Outside Germany

Someone from outside Germany asked how to get funding for the program. I don't know a simple way, and usually the employer covers the cost. If your country has a similar funding program, I doubt it pays for a course in Germany. The Bildungsgutschein is for people in Germany, and unfortunately I can't help with funding from other countries.

Someone else asked about a training budget through a Transfergesellschaft. I don't know yet whether it works for the full-time program, because it may require a specific certification. If this is your situation, write to me at [alexey@datatalks.club](mailto:alexey@datatalks.club) and I'll reply.

## Experienced, but Applications Go Nowhere

Someone with years of experience asked what to do now that job openings ask for AI experience and applications get no answers.

It's a tough market, and AI makes it harder. It also makes it easier to build things, so build as many as you can. Get a subscription to Claude or Codex. You can start with the cheapest plan, but in my experience it isn't enough. You get a lot more if you add a second low-cost plan like OpenCode Go.

Build a portfolio that shows AI experience and also shows that you know the domain of the companies you apply to. Then repeat the cycle: network and apply, build projects, interview and look back at what worked. I wrote this up in the [guide on getting hired as an experienced developer](/academy/guides/getting-hired-with-ai/).

## Outreach on LinkedIn That Gets Answers

Someone said people on LinkedIn don't answer them. It depends on how you approach them. If someone writes "here's my CV, can you refer me", I wouldn't answer either. Be curious and ask about their work, for example about a blog post they wrote. Then mention that you built something similar and show your project.

When I was a hiring manager, people who asked me questions on LinkedIn and then invited me for lunch always got a meeting. It didn't always end in a referral, but I met interesting people. Meetups work better than connection requests, so talk to the speaker after the talk and ask about their work.

Don't try to turn every conversation into a referral right away. Get to know the person instead. You build your network over years: you meet someone now, and in three years they work somewhere else and remember you. I'm an introvert and these events exhaust me, but it gets easier with practice.

## Program Length

Someone asked how long the program takes. It's three months, full-time, and every day you show up and build things, and I help you. On the published schedule, the program runs Monday to Friday, 09:00 to 16:30 Berlin time, for 13 weeks. Start: April 2027.

## A Skill List That Keeps Growing

Someone asked how to catch up when the skills employers want seem to grow faster than they can learn. Courses and projects don't count as experience, and they're too senior for junior roles.

I'd challenge the idea that it keeps growing. You do things and you build things, so the distance isn't infinitely large. Social media makes it feel that way, with a new framework every day and people sharing what they built.

Tools come and go, but you keep using the same fundamentals. You still send the same kind of request to OpenAI. RAG works the same way it did three years ago, and agents work the same way they did two years ago. You always have to evaluate your models: that was true in 2022 and it'll be true in 2027.

Focus on fundamentals first, then build projects right away. Find problems in job descriptions, engineering blogs or your own life, and solve them. If you keep doing that, what you're missing to be useful at work gets smaller and smaller.

You also don't need a junior position. Position yourself as a mid-level specialist and build on what you already have. If you worked in insurance, target insurance companies that need an AI engineer.

## Scraping the Job Postings

Someone asked what I use to scrape the job postings. Nothing special: the job site includes structured data in the page source, so a simple Python script sends a GET request and reads it. You can build a similar tracker for your own job title by describing it to Claude Code or Codex and letting the agent write it.

## Materials and Links

Leave your email on the [materials page](/academy/sessions/materials/) and I'll send you the slides, a summary and the links from this session.

These are the links I shared during the talk:

- [AI Engineering Field Guide](https://github.com/alexeygrigorev/ai-engineering-field-guide): AI engineer job postings, analyzed every month
- [Getting an AI Engineering Job](https://aishippingblog.com/p/getting-an-ai-engineering-job): networking, applying, projects and interviews
- [Choosing a Portfolio Project](https://aishippingblog.com/p/choosing-a-portfolio-project-the): how to pick projects from a target company's domain
- [AI Dev Tools Zoomcamp](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp): my free course on the basics of agentic engineering, and I build the Agentic Engineering program on it
- [AI Engineering Buildcamp: From RAG to Agents](https://maven.com/alexey-grigorev/from-rag-to-agents): the course I've taught for a year and a half, which the AI Engineering program is based on

In the next two sessions I go deeper, one only on agentic engineering and one only on AI engineering. You can register on the [sessions page](/academy/sessions/).
