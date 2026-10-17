# Preface {.unnumbered}

## Why this book

The first time I built something serious with Claude Code, I spent three hours on Google.

The problem wasn't hard. I was looking for basic things: how to set up a project so Claude wouldn't lose track after fifty messages, why the command from a tutorial didn't exist in the version in front of me, how to get it to work across several files without pasting their contents every time. I went through outdated docs, Reddit threads and twelve-minute videos where the author's "method" was asking Claude to write code.

If someone had explained to me that evening what I worked out over the following months, I would have been done in half an hour. This book is the explanation I wish I'd had.

I've used Claude Code every day since, for work and for my own projects: Python scripts that build Excel reports for a client, landing pages, automations, internal tools, all the way to a full-stack application with authentication, uploads to S3, an admin panel and a deploy on AWS. I've used it with Python, JavaScript and PHP, on small repos and on codebases with hundreds of files, alone and on a team.

What I learned is that the jump from "I tried it a couple of times" to "I have a project in production" has little to do with commands. It has to do with how you work: how you set up a session, when you plan and when you don't, what goes into CLAUDE.md, when a task deserves its own agent, how you check what the agent did. Commands change almost every week. Those habits stay useful for much longer, and they're what this book keeps coming back to.

## Who it's for

For people who write code at least once a week, in any language: front-end and back-end developers, people who write scripts and automations, data analysts who build their own reports.

For people who have tried ChatGPT, Copilot or Cursor to rewrite a function or explain an error, but have never finished a whole project with an agent. They aren't sure how far to trust the output, or how to fit it into the way they already work.

For people who want a repeatable method. Tricks are everywhere online; a process that still works the tenth time, on a different project, is harder to find.

It's probably not the right book for three kinds of reader. The manager who wants to know whether Claude Code replaces developers: the answer is no, and this book is written for the people who write the code. Anyone looking for an academic analysis of language models or a rigorous comparison of agents: that book exists, but this isn't it. And anyone who has never opened a terminal: Claude Code assumes the basics, a variable, a loop, a shell command. If that's where you are, take an introductory Python or JavaScript course first, then come back.

## How it's organized

The book follows a deliberate curve: each part builds on the ones before it.

**Part I** (chapters 1-3) installs Claude Code, explains how an agent works inside the terminal and how to write prompts that get the result on the first or second try. Part II (chapters 4-6) applies all of it to real data: a CSV, an Excel report, charts, a dashboard and a PDF. Part III (chapters 7-10) extends Claude Code with CLAUDE.md, custom commands, skills and agents. Part IV (chapters 11-15) is new in this edition: permissions and the sandbox, hooks, MCP, plugins, managing context and memory. Part V (chapter 16) is the first complete project, a landing page from mockup to deploy on Firebase. Part VI (chapters 17-23) is the main project, the Photogallery: specs, Spec Driven Development, execution in waves, review, QA and a deploy on AWS with CloudFormation.

At the back you'll find five appendices to keep at hand: a glossary, troubleshooting, ready-made prompts, resources and a changelog.

## What's new in the second edition

The first edition, published in May 2026, described Claude Code with Claude Opus 4.7 and Sonnet 4.6. Five months later a lot is different: the default model is Claude Opus 5.5 with a one-million-token context, Claude Code starts in auto mode and asks for confirmation far less often, custom commands have been merged into skills, the `/agents` wizard is gone, code review is built in, and you can run several sessions in parallel on separate worktrees.

I updated every chapter to October 2026 and added seven: chapter 2 on how an agent works, the five chapters of Part IV and chapter 20 on running waves in parallel. Chapter 22 now compares Claude Code's built-in review with a review by a second model. I also rewrote the text from start to finish, cutting repetition and filler, because a technical book should save its reader time. The full list of changes is in Appendix E.

Many of the new topics I first recorded as lessons in my Claude Code course and then brought here. If you took the course, you'll recognize the lab project in Part IV.

## What will change while you read

Claude Code ships new versions almost every day. By the time you read this, some command will have been renamed, some option will be gone and others will have arrived. Where something is especially unstable, like the name of the default model, the text tells you how to check it on your own install instead of trusting the printed page.

The method holds: written specs, acceptance criteria you can verify, constraints enforced with permissions and hooks rather than recommendations, review before merge. New features slot into that flow.

## Acknowledgments

Thanks to Anthropic, for building a tool rich enough to deserve a whole book.

Thanks to Jesse Vincent and the Superpowers community for the plugin, the ideas and the discussions that shaped Part III.

Thanks to the students of my online course, who worked through early versions of these chapters, found the most embarrassing mistakes before you could, and asked the questions that convinced me to add sections I hadn't planned. And thanks to the readers of the first edition who wrote to me: many of the corrections in this edition come from them.

Thanks to my colleagues at Spryker for the afternoons of pair programming with AI, which produced more examples than I cite.

Thanks to my family, who for many evenings put up with my "five more minutes and I'll be there for dinner".

Hidran Arias, October 2026
