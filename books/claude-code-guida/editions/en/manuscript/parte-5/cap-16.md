# Chapter 16. A landing page from idea to Firebase deploy

::: {.chapter-goals}
[What you'll learn]{.callout-title}

- Use the Superpowers visual companion to settle the design on HTML mockups before you write a line of React.
- Turn the approved mockups into a spec and a plan of atomic tasks, then run it one task at a time with a review and a commit after each.
- Rebuild an existing design, for example a page made with Lovable, starting from a screenshot.
- Publish the landing page on Firebase Hosting, going through a preview channel before production.

[Prerequisites]{.callout-title}

Node.js 20 or later, a Google account for the Firebase console, and the Superpowers plugin installed (chapter 8). We'll install the Firebase CLI along the way.

:::

A landing page is the right project for putting together everything you've seen so far for the first time. It's frontend only: no backend, no database, no authentication. Deploying it is simple. The structure is predictable (hero, features, pricing, testimonials, FAQ, footer), yet it has enough pieces to call for a plan, a breakdown into components and a few rounds of design iteration.

The product is called FluentAiPro: a made-up language-learning app with an AI tutor, conversations in more than 50 languages, pronunciation feedback and adaptive learning paths. The product stays imaginary. What we build is the page that presents it and sends visitors to sign up, in React, Vite and Tailwind CSS, deployed on Firebase Hosting.

The code lives in the companion repo `github.com/hidran/fluentaipro-claude-landingpage`. Each branch is a snapshot of the project at the end of a section: `book/cap-10-1-mockups`, `book/cap-10-2-spec`, `book/cap-10-3-execution`, `book/cap-10-5-deploy-ready`. The 10 comes from the first edition, where this was chapter 10. The branches kept their names so the links already out there don't break. The repo's actual stack is React 19, Vite 6, Tailwind CSS 4.2 and Vitest 4.

The chapter is long because it covers the whole path, from the idea to a public URL. Read it with a terminal open.

## 16.1 The visual companion, from "I want a landing page" to a mockup

### Why mockups before code

The visual companion is part of the Superpowers `brainstorming` skill. It generates HTML and CSS drafts, serves them from a small local server and shows them to you in the browser. You comment in plain language, Claude updates the draft, you reload the page.

You already know the problem it solves. You describe an interface to Claude ("a dark hero, big headline, two buttons, an image on the right") and you get code that follows the description to the letter. The result can be correct and ugly. To fix it you have to read the components, work out what Claude did, correct it and wait for HMR. Every round costs time and tokens.

With the visual companion that round happens earlier, on static HTML files: no dependencies to install, no React project to start. Once the mockup looks right, you move on to code. It's the same split between deciding and building that you'll find in the Spec Driven Development of chapters 17-19, applied to design.

### Setup

Create an empty folder and start Claude Code inside it:

```bash
mkdir fluent-ai-landing && cd fluent-ai-landing
git init
claude
```

Running `git init` right away pays off later: every task in the plan will become a commit. Check with `/status` that you're on the right account.

Then switch to Plan Mode: press `Shift+Tab` until the status bar shows `plan mode on`, or use `/plan`. In Plan Mode Claude explores and proposes, but doesn't change any file until you approve.

### The opening prompt

```text
I want to build a landing page for FluentAiPro,
a web app for learning languages with the help of AI.
Users can:
- practice conversation with an AI tutor in more than 50 languages
- get real-time feedback on pronunciation and grammar
- follow adaptive learning paths
- listen to themed podcasts in a foreign language

Start by exploring the project and propose a plan.
I want you to use the visual companion to show me visual
drafts before you touch the code.
```

Claude looks at the folder (empty), loads the `brainstorming` skill and asks whether you want to use the companion in the browser. Say yes. It then runs the skill's `start-server.sh` script: in auto mode it usually goes through on its own, in Manual mode you approve it.

The server listens on `localhost` on a random port, and Claude gives you the full address to open, session key included. The drafts land in the project folder, under `.superpowers/brainstorm/<session-id>/`. The `book/cap-10-1-mockups` branch has the ones from my session: `sections.html`, `approaches.html`, `hero-design.html` and `hero-design-v2.html`, `features-design.html` and `features-design-v2.html`, `social-pricing.html`, `pricing-v2.html`. They open with a double click, no build needed. The server shuts itself down after four hours of inactivity. If you pick the work up the next day, Claude restarts it on the same port.

### The brainstorming questions

Before drawing anything, the skill asks questions, one at a time. Some come up in the terminal, others as a clickable page in the browser. These are the answers I gave (adjust them to taste):

- Main call to action: "Start for free". The goal is direct sign-up, no waitlist.
- Audience: students and professionals, weighted equally. The tone mustn't shut out either group.
- Sections: the `sections.html` page offers eight (Hero, Features, Social proof, Pricing, Language showcase, App demo, FAQ, Footer with a final CTA). I picked all of them.

Right after that comes `approaches.html` with three visual directions: A, Glassmorphism (dark background, frosted-glass cards, a violet-to-cyan gradient, a glow behind everything), which Claude recommended; B, Deep Space + Gold (midnight blue with a gold accent); C, Stark Minimal (near-black, white type, no decoration at all). For an AI app I went with A.

### Three rounds of iteration

From here Claude draws one section at a time, and every draft is a starting point. The `-v2` suffix in the file names matches my comments.

The first round covers the hero and the navbar. The structure was right, the proportions weren't:

```text
Looks good, but the menu links need to be bigger
and highlighted when their section is active.
The hero headline needs to be bigger: it's the main message.
```

Claude rewrites the HTML in a few seconds, you reload and see `hero-design-v2.html`. These are CSS changes: no components, no bundle.

The second round deals with features and pricing. The cards had small text and weak contrast, and the prices were placeholders:

```text
Feature cards: bigger text and more contrast
between title and description.
Pricing: use these real plans:
- Free: €0/month, 10 AI conversations per month, 1 language
- Silver: €12.99/month, unlimited conversations, 3 languages
- Gold: €24.99/month, all 50+ languages, priority support
Add a monthly/yearly toggle with 20% off the yearly plan.
```

The toggle shows up right away, but in the mockup it's just graphics. The logic comes with React.

The third round locks in the colors. Claude sums up the palette that came out of the earlier rounds: background `#0a0a0f`, gradient from `#7c3aed` (violet) to `#06b6d4` (cyan), white text, secondary text in white at 65% opacity. You confirm it and Claude records it as design tokens for the spec:

```text
The palette is fine. Confirm it and save the design tokens.
```

At this point you have a clickable mockup with the sections, palette and hierarchy settled. Claude hasn't created a `package.json`, hasn't run `npm install`, hasn't written a single `.jsx` file. It worked in a scratch folder kept apart from the code, so throwing a draft away costs nothing.

::: {.callout .callout-tip}
[Tip]{.callout-title}

In the companion repo the `.superpowers/` folder is committed on purpose, so you can look at the mockups. In your own projects you can add it to `.gitignore`: whatever matters in the design ends up in the spec anyway.
:::

## 16.2 From mockup to a plan of atomic tasks

### Closing the design phase

When the mockup looks right, close the phase with an explicit message:

```text
The mockup is approved. Now let's build the real project
in React + Vite + Tailwind CSS (latest version).
First generate the complete specifications, then the
implementation plan with atomic tasks.
```

From here on Claude plans concrete work: project structure, components, dependencies, deploy. Anything you want on the page has to be said now.

### The spec

Superpowers wraps up brainstorming by writing a spec. In the repo it's `docs/superpowers/specs/2026-03-25-fluentaipro-landing-page-design.md`, on the `book/cap-10-2-spec` branch. Without Superpowers you ask for it yourself:

```text
Before writing any code, create a docs/ folder and
write the complete project specifications: stack,
structure, components, design tokens, accessibility.
```

The real spec covers the stack (React 19 with Vite, Tailwind CSS v4 through the `@tailwindcss/vite` plugin, no routing, Firebase Hosting, CSS-only animations), the palette's design tokens, the type scale with the Inter font, the order of the nine sections and, for each one, copy, layout and responsive behavior. It closes with an accessibility section (computed contrast ratios, `aria-expanded` on the FAQ, `prefers-reduced-motion`) and a final verification checklist. It's in English, like the landing page copy: the product speaks to an international audience.

Two details show how much later work a well-written spec saves. The navbar turns "glass" when a `<div id="nav-sentinel">` placed just below it leaves the viewport, watched with `IntersectionObserver`. The yearly prices are written out in full (€10.39 Silver, €19.99 Gold) instead of leaving the math to the component. Without a spec, Claude would make those calls on its own halfway through execution.

::: {.callout .callout-warning}
[Warning]{.callout-title}

Read the spec before you approve it. It's the last moment when adding a requirement, dropping a section or changing some copy costs one line of Markdown. After that, every change is a fix task on code that's already written.
:::

### The plan

Once the spec is approved, Superpowers hands over to the `writing-plans` skill and generates the implementation plan: a numbered list of tasks, each with the files it touches, the tasks it depends on and a completion criterion you can check. In my session there were ten tasks. You can see the titles in the figure; I rebuilt the files and criteria below from the spec, because the plan file isn't in the repo.

```text
Task 1: Project Scaffolding
  Files: package.json, vite.config.js, vitest.config.js, index.html,
         src/main.jsx, src/App.jsx, src/index.css, tests/setup.js
  Depends on: none
  Done: npm run dev starts with no errors, npx vitest run is green

Task 2: Shared UI Components
  Files: src/components/ui/Badge.jsx, Button.jsx, GlassCard.jsx,
         GradientText.jsx, tests/ui/Button.test.jsx, GlassCard.test.jsx
  Depends on: Task 1
  Done: components render with their main props, tests green

Task 3: Navbar
  Files: src/components/sections/Navbar.jsx, tests/sections/Navbar.test.jsx
  Depends on: Task 2
  Done: sticky navbar, glass effect after scrolling via the sentinel

Task 4: Hero Section
  Files: src/components/sections/Hero.jsx, tests/sections/Hero.test.jsx
  Depends on: Task 2
  Done: headline, subtitle, two CTAs, stats bar; h1 at 40px on mobile

Task 5: Features Section
  Files: src/components/sections/Features.jsx
  Depends on: Task 2
  Done: wide card with the chat mockup plus 4 cards; one column below 768px

Task 6: Demo, Languages, Testimonials
  Files: src/components/sections/Demo.jsx, Languages.jsx, Testimonials.jsx
  Depends on: Task 2
  Done: animated mockup (static with prefers-reduced-motion), 18 languages
        plus the "+32 more" chip, 3 testimonials

Task 7: Pricing Section
  Files: src/components/sections/Pricing.jsx, tests/sections/Pricing.test.jsx
  Depends on: Task 2
  Done: monthly/yearly toggle, yearly at 10.39 (Silver) and 19.99 (Gold)

Task 8: FAQ Section
  Files: src/components/sections/FAQ.jsx, tests/sections/FAQ.test.jsx
  Depends on: Task 2
  Done: accordion with aria-expanded, animation on maxHeight

Task 9: Footer + Full Assembly
  Files: src/components/sections/Footer.jsx, src/App.jsx, tests/App.test.jsx
  Depends on: Task 3-8
  Done: 9 sections in spec order, correct layout at 375, 768, 1280 px

Task 10: Firebase Deployment
  Files: firebase.json, .firebaserc
  Depends on: Task 9
  Done: npm run build is clean, firebase deploy --only hosting succeeds
```

![The ten-task plan in the VS Code terminal, next to the freshly generated package.json](figures/cap-16/fig-01.png)

### Why such small tasks

An atomic task moves the project from one consistent state to the next with the least work possible. "Build the Hero section" is atomic, "build the landing page" isn't.

The payoff shows up in three places during execution. If every task is a commit, `git log` becomes the project's diary and a bug traces back to one specific commit. If Task 7 breaks the pricing, you `git revert` that commit without losing the Hero and the Features. And you can review a 60-line component carefully; 1,200 new lines, you can't.

If you're not using Superpowers, ask Claude to save the plan to a file and commit it first:

```text
Save the plan to docs/PLAN.md and commit it as the
project's first commit.
```

With the plan on disk you can `/clear` whenever you like: Claude rereads the file and knows where you left off.

## 16.3 Execution, one task at a time

### Subagent driven

When you say "run the plan" you have two options. The first is inline execution: Claude works in the main context and you see everything in the conversation, but the context window fills up fast. The second is the Superpowers subagent-driven mode (the `subagent-driven-development` skill): each task gets a subagent with a clean context, which reads the task, writes the files, runs the commands and reports back only the outcome. Files read, build output and test logs stay in the subagent's context.

For this landing page, pick the second:

```text
Now run the plan in subagent-driven mode.
One subagent per task. Wait for my confirmation
after each task before moving on to the next.
```

You have to spell out the confirmation request: without it, the skill runs the whole plan in one go and stops only when it hits a blocker. With it, you set the pace: look at the diff, open the browser, then give the go-ahead for the next task. Here the tasks run in sequence, one after another. In chapter 20 you'll see how to run independent tasks in parallel, each in its own worktree, once the project is big enough to justify it.

### Task 1, scaffolding

The Task 1 subagent creates the Vite project and adds Tailwind and Vitest:

```bash
npx create-vite@latest . --template react
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

Tailwind v4 no longer has a `tailwind.config.js`: you turn it on with the Vite plugin and one line of CSS. This is the repo's `vite.config.js`:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

In `src/index.css` the first line is `@import "tailwindcss";`, followed by the spec's design tokens, declared both in `:root` and in `@theme`. At the end the subagent reports the files it created, how `npm run dev` went and the commit. Open `http://localhost:5173`, check that the Vite page shows up and reply:

```text
Task 1 ok. Go ahead with Task 2.
```

### Task 2, shared components

Task 2 creates, in `src/components/ui/`, the four building blocks every section reuses: `Badge` (the pill label), `Button` (`primary` and `secondary` variants, a link or a button depending on whether it gets an `href`), `GlassCard` (the glass container) and `GradientText` (the text with the violet-cyan gradient). They're tiny components. The whole of `GlassCard` fits in seven lines:

```jsx
export default function GlassCard({ children, className = '', ...props }) {
  return (
    <div className={`glass-card ${className}`} {...props}>
      {children}
    </div>
  )
}
```

The styling lives in BEM classes inside `index.css` (`.glass-card`, `.btn-primary`), and the `CLAUDE.md` that Claude wrote for the repo says so plainly: no inline Tailwind utilities for structural or brand styles.

The components come with the first tests, in Vitest and React Testing Library, under `tests/` with the same structure as `src/`. This isn't TDD in the strict sense, just a minimal safety net that warns you before the deploy if a refactoring breaks `Button`.

![The App renders without crashing test and the task list while execution moves along](figures/cap-16/fig-02.png)

### Task 4, the Hero

The Hero is the most visible task. Keep the browser open while it runs: with Vite's HMR the page refreshes on every saved file. This is the component on the `book/cap-10-3-execution` branch:

```jsx
import React from 'react'
import Badge from '../ui/Badge'
import GradientText from '../ui/GradientText'
import Button from '../ui/Button'
import { APP_URL } from '../../constants.js'

const STATS = [
  { number: '50+', label: 'Languages' },
  { number: '10M+', label: 'Conversations' },
  { number: '98%', label: 'Accuracy Rate' },
  { number: '4.9★', label: 'User Rating' },
]

export default function Hero() {
  return (
    <section id="hero" className="hero">
      <div className="hero__glow hero__glow--violet" aria-hidden="true" />
      <div className="hero__glow hero__glow--cyan" aria-hidden="true" />

      <Badge>AI-Powered Language Learning</Badge>

      <h1 className="hero__title">
        Learn any language<br />
        with your <GradientText>AI tutor</GradientText>
      </h1>

      <p className="hero__subtitle">
        Practice real conversations in 50+ languages. Get instant pronunciation
        feedback and a learning path that adapts to you.
      </p>

      <div className="hero__actions">
        <Button href={APP_URL} variant="primary">Start for free →</Button>
        <Button href="#features" variant="secondary">▶ See how it works</Button>
      </div>

      <div className="hero__stats" role="list">
        {STATS.map(({ number, label }, i) => (
          <React.Fragment key={label}>
            {i > 0 && <div className="hero__stats-divider" aria-hidden="true" />}
            <div className="hero__stat" role="listitem">
              <span className="hero__stat-number gradient-text">{number}</span>
              <span className="hero__stat-label">{label}</span>
            </div>
          </React.Fragment>
        ))}
      </div>
    </section>
  )
}
```

The headline, subtitle and stats come from the spec word for word. The colored glows are two decorative `div`s with `aria-hidden`, and the CTA's URL comes from `src/constants.js`, so you change it in one place. The stats are marketing placeholders to replace with real data before launch.

### Don't run the whole plan in one shot

The most common mistake with an approved plan is writing "run everything without asking me". You end up with dozens of new files in a single wave. If the pricing toggle is broken you have to figure out which of thirty files is to blame, the review turns into skimming, and the Git history is one big lump.

One task at a time looks slower. In practice it's faster, because you catch each mistake right after it's made. For each task a glance at the diff and a check in the browser are enough.

### Task 7, pricing with the toggle

Pricing is the section with the most logic. In the mockup the toggle only changed the look; here it becomes React state. This is an excerpt of `Pricing.jsx` (Silver and Gold have the same shape as the Free plan):

```jsx
import { useState } from 'react'
import GlassCard from '../ui/GlassCard'
import { APP_URL } from '../../constants.js'

const PLANS = [
  {
    icon: '🌱', name: 'Free',
    monthly: '0', yearly: '0', yearlyTotal: null,
    desc: 'Try it out, no strings attached',
    features: [
      { label: '1 language', included: true },
      { label: '10 AI conversations / month', included: true },
      { label: 'Basic pronunciation feedback', included: true },
      { label: 'Adaptive learning path', included: false },
      { label: 'Progress analytics', included: false },
      { label: 'Priority support', included: false },
    ],
    cta: 'Get started free', ctaVariant: 'outline',
  },
  // Silver: monthly '12.99', yearly '10.39', yearlyTotal '124.70', featured: true
  // Gold:   monthly '24.99', yearly '19.99', yearlyTotal '239.88'
]

export default function Pricing() {
  const [cycle, setCycle] = useState('monthly')
  const isYearly = cycle === 'yearly'

  return (
    <section id="pricing" className="section section--centered">
      {/* ... title and subtitle ... */}
      <div className="pricing__toggle-row">
        <button
          className={`pricing__toggle-label${!isYearly ? ' pricing__toggle-label--active' : ''}`}
          onClick={() => setCycle('monthly')}
        >
          Monthly
        </button>
        <button
          className="pricing__toggle-track"
          onClick={() => setCycle(isYearly ? 'monthly' : 'yearly')}
          role="switch"
          aria-checked={isYearly}
          aria-label={isYearly ? 'Switch to monthly billing' : 'Switch to yearly billing'}
        >
          <span className={`pricing__toggle-knob${isYearly ? ' pricing__toggle-knob--right' : ''}`} />
        </button>
        <button
          className={`pricing__toggle-label${isYearly ? ' pricing__toggle-label--active' : ''}`}
          onClick={() => setCycle('yearly')}
        >
          Yearly
        </button>
        {isYearly && <span className="pricing__save-badge">Save 20%</span>}
      </div>
      {/* ... the three GlassCards: price = isYearly ? yearly : monthly ... */}
    </section>
  )
}
```

Click and the prices change. The state is a string, `'monthly'` or `'yearly'`, as the spec asked, and the toggle has `role="switch"` with `aria-checked`, so a screen reader announces it for what it is. The yearly prices are written into the data rather than computed, so the test can check them directly:

```jsx
test('shows yearly prices after toggling to yearly', async () => {
  const user = userEvent.setup()
  render(<Pricing />)
  await user.click(screen.getByRole('button', { name: /yearly/i }))
  expect(screen.getByText('10.39')).toBeInTheDocument()
  expect(screen.getByText('19.99')).toBeInTheDocument()
})
```

### Code review

In subagent-driven mode the review doesn't wait for the end. In my session, in March 2026, Superpowers ran two checks after every task: one verified that the code followed the spec, the other (the `superpowers:code-reviewer` subagent) looked at quality. In the figure Task 2 is under review while Task 3 is starting. Since version 6 of the plugin the two checks have merged into a single reviewer per task, plus a review of the whole branch at the end.

![The Superpowers code-reviewer subagent reviews Task 2 while Task 3 starts](figures/cap-16/fig-03.png)

Once all the sections are ready, before the deploy, do an overall review anyway. Some problems only show up when you look at the sections side by side:

```text
Now run a code review on the components in src/components/sections/.
Check for:
- hardcoded colors that should go through the design tokens
- CSS duplicated across sections
- accessibility (aria-label, contrast, focus states)
- consistent naming conventions
- files that shouldn't be in Git (dist/, .env.local)
```

On a project like this the typical findings are a color like `#7c3aed` typed by hand in a component instead of `var(--color-grad-from)`, the same padding repeated in seven sections, `dist/` missing from `.gitignore`, a button with no accessible name. The final code in the repo shows the result of the fixes: the shared `.section` class in `index.css`, `dist/` in `.gitignore`, `aria-label` on the toggle. Ask Claude to fix the findings and commit them separately, with a message like `fix: code review, design token, gitignore, accessibilità`.

Claude Code now also has a built-in command, `/code-review`, that reviews unpushed changes looking for correctness bugs: it's covered in chapter 22. The checklist above is still useful for tokens, duplication and accessibility, and chapter 19 comes back to review on a bigger project.

## 16.4 Rebuilding an existing design, the Lovable case

### When the design already exists

So far you've started from scratch. The opposite happens a lot: the design already exists. It might be a landing page made on Lovable, a Figma mockup or a competitor's site you like, and you want to rebuild it in your own stack.

Lovable (`lovable.dev`) generates React interfaces from a description, inside a visual editor. The result is polished, but the code lives on the platform and is awkward to bring into a normal development workflow. The FluentAiPro landing page had also been built on Lovable earlier, and comparing it with the Claude Code version is instructive.

### Rebuilding from a screenshot

Claude Code reads images, so you can show it a screen and ask it to rebuild it.

Step one: capture the page. If it's long, take a screenshot of each main section and save them in the project:

```bash
mkdir -p docs/design-reference
# copy the screenshots here
```

Step two: give the image to Claude. You can paste it into the prompt with `Ctrl+V` (on macOS too, not `Cmd+V`), drag it into the terminal or reference it with `@`:

```text
Look at @docs/design-reference/lovable-landing.png

Rebuild this landing page in React + Vite + Tailwind CSS.
Style specs:
- Dark mode, near-black background
- Violet accent color (#7c3aed)
- Bold condensed type for headings
- Glassmorphism effects on the cards
- Subtle animations (fade-in on scroll)
```

Step three: Claude analyzes the image. It works out the layout, palette, typography and number of blocks, then generates the components. Copy, prices and section names that can't be read clearly from the screenshot become placeholders to update.

### Four rounds of visual iteration

The first rebuild is rarely perfect. A static image doesn't give you exact spacing, hover states, animations or breakpoints. You iterate with precise comments, one theme per round.

Overall proportions:

```text
The structure of the rebuild is good, but:
- The hero's vertical padding is too tight
- The feature cards are taller in the original
- The main headline font should be bolder
```

Interactive details:

```text
Add:
- Hover state on the cards: a light violet glow on the border
- Smooth transition on the pricing toggle (0.3s ease)
- Smooth scroll behavior on the menu's anchor links
```

Animations:

```text
Add fade-in on scroll animations to the features,
testimonials and pricing sections. Use IntersectionObserver
or a lightweight library like framer-motion.
Nothing over the top: just opacity from 0 to 1 with a small
translate-y (20px), duration 0.5s.
```

Mobile:

```text
Go over the mobile version (375px):
- The navbar should collapse into a hamburger menu
- The features grid should be 1 column on mobile
- The prices should be readable without horizontal scrolling
```

After four rounds you have a faithful rebuild in standard React and Tailwind, in your own repo, that you can maintain with any tool.

### Rebuild or start from scratch

A rebuild makes sense when the design is already validated: you've tried the Lovable prototype with users, the client has signed off on it, or it's the classic SaaS landing layout and reinventing it gains you nothing. Start from scratch with the visual companion when you have no reference, when the brand still needs an identity, or when the client hasn't seen anything yet and you have room to propose.

For many commercial landing pages a rebuild saves time: the structure, hierarchy and CTAs already work, and you customize the details. The two tools get along fine: Lovable to show a client an idea in a few minutes, Claude Code to take it to production with versioned, tested code.

## 16.5 Commits, Firebase deploy and a live URL

### The history before the deploy

If you went one task at a time, you already have a series of commits. Check before the deploy:

```bash
git log --oneline
```

You should see something like this, one commit per task plus the review one:

```text
a7b3c2d fix: code review, design token, gitignore, accessibilità
f1e9d8c feat: Footer e assemblaggio delle 9 sezioni
2d4e5f6 feat: FAQ accordion con aria-expanded
3f2e1d0 feat: Pricing con toggle mensile/annuale
9c8b7a0 feat: Demo, Languages, Testimonials
8a7b6c5 feat: Features con card larga e mockup chat
4d3c2b1 feat: Hero con statistiche e glow
7e6f5d4 feat: Navbar sticky con effetto vetro
b9a8c7d feat: componenti UI Badge, Button, GlassCard, GradientText
1f0e9d8 feat: scaffolding Vite + React + Tailwind + Vitest
0c1b2a3 docs: spec e piano di implementazione
```

Each line can be read, reviewed and reverted on its own. The companion repo's branches are snapshots with a single commit each, so you won't find this history there: you build it yourself.

### The Firebase project

If you don't have a Firebase project yet:

1. Go to `console.firebase.google.com` and create a new project.
2. Give it a name, for example `fluent-ai-pro-landing`. Firebase derives the project ID from it, and you can edit the ID now: once the project is created it can't be changed.
3. Skip the optional steps, AI assistance and Google Analytics: a static landing page doesn't need them.
4. Confirm with Create project.

Write down the project ID. It often matches the name, sometimes it has a suffix. You'll need it in the CLI.

### The Firebase CLI

You can install it globally:

```bash
npm install -g firebase-tools
firebase login
```

or run it on the fly with `npx firebase-tools`, as Claude did in my session. If you go with `npx`, use `npx firebase-tools` in place of `firebase` in every command in this section. `firebase login` opens the browser for Google authentication. Then check:

```bash
firebase projects:list
```

The project you just created should be in the list.

### firebase init hosting

From the project folder:

```bash
firebase init hosting
```

The CLI asks a few questions:

- Project: use the existing one and pick it from the list.
- Public directory: `dist`, the folder `npm run build` produces.
- Single-page app: yes. Every URL gets rewritten to `index.html`, which you'll need if you ever add React Router.
- Automatic builds and deploys with GitHub: no, for now.
- If `dist/index.html` already exists and the CLI asks to overwrite it, answer no.

The result is the `firebase.json` on the `book/cap-10-5-deploy-ready` branch:

```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [{ "source": "**", "destination": "/index.html" }]
  }
}
```

Plus a `.firebaserc` that ties the folder to the project. In the repo the ID is `fluentapipro`; you'll see yours:

```json
{
  "projects": {
    "default": "fluentapipro"
  }
}
```

![Claude writes firebase.json and .firebaserc during the deploy task](figures/cap-16/fig-04.png)

Commit the configuration:

```bash
git add firebase.json .firebaserc
git commit -m "chore: Firebase Hosting configuration"
```

The same branch also has `.github/workflows/deploy.yml` and `docs/ci-cd-vercel.md`: a GitHub Actions pipeline that runs the tests and publishes to Vercel, with a preview deploy for every PR. It's an alternative to Firebase, and you can ignore it to follow the chapter.

### Preview channels, before going live

Firebase Hosting has preview channels: temporary URLs, valid for 7 days by default, for showing a version to a client or a colleague without touching the production site.

```bash
npm run build
firebase hosting:channel:deploy preview-v1
```

The output ends with the channel URL and its expiry date:

```text
✔  hosting:channel:deploy complete!

Channel URL (fluent-ai-pro-landing):
https://fluent-ai-pro-landing--preview-v1-xyz123.web.app

[expires 2026-05-23 14:32:10]
```

Open the URL and check everything: navigate with the menu links, try the pricing toggle and check the yearly prices, open and close the FAQ items, shrink the window to 375px, make sure the CTAs point to the right URL. If something needs changing, deploy to the channel again: you don't touch the production site.

### The production deploy

Once the preview is approved:

```bash
npm run build
firebase deploy --only hosting
```

Firebase reads `firebase.json`, uploads the contents of `dist/` to its CDN and publishes the new version:

```text
=== Deploying to 'fluent-ai-pro-landing-a1b2c'...

i  deploying hosting
i  hosting[fluent-ai-pro-landing]: beginning deploy...
i  hosting[fluent-ai-pro-landing]: found 18 files in dist
✔  hosting[fluent-ai-pro-landing]: file upload complete
i  hosting[fluent-ai-pro-landing]: finalizing version...
✔  hosting[fluent-ai-pro-landing]: version finalized
i  hosting[fluent-ai-pro-landing]: releasing new version...
✔  hosting[fluent-ai-pro-landing]: release complete

✔  Deploy complete!

Project Console: https://console.firebase.google.com/project/...
Hosting URL: https://fluent-ai-pro-landing-a1b2c.web.app
```

The landing page is online, with HTTPS and a CDN, without configuring a server or paying for hosting: Firebase's free plan is plenty for a static page.

### After the deploy

For a custom domain, go to the console, Hosting section, and add the domain. Firebase gives you the DNS records to enter at your registrar and issues the HTTPS certificate by itself. DNS propagation can take anywhere from a few hours to a day; in the meantime the site stays reachable at `.web.app`.

Firebase keeps a history of releases. If a deploy introduces a problem, you can roll back to a previous version with one click from the Hosting console. If instead the approved preview is exactly what you want in production, you can copy it to the live channel without rebuilding:

```bash
firebase hosting:clone fluent-ai-pro-landing:preview-v1 fluent-ai-pro-landing:live
```

If you ever move the landing page to Next.js, turn on static export in `next.config.js`:

```javascript
const nextConfig = {
  output: 'export',
  trailingSlash: true,
};
```

`next build` then produces static HTML in the `out/` folder instead of `dist/`, with no Node.js server needed. Remember to change `public` in `firebase.json`.

One last case, and a very common one. While trying the preview you might notice that the active menu item doesn't follow the scroll. A scrollspy fixes it:

```text
Add a scrollspy to the Navbar: use IntersectionObserver
to detect which section is visible and apply the
active class to the matching link in the menu.
```

In the repo's `Navbar.jsx` you'll find it in the second `useEffect`: an `IntersectionObserver` with a 0.3 threshold tracks the topmost visible section. Claude implements it, you commit and deploy again:

```bash
npm run build
firebase deploy --only hosting
```

With the deploy cycle already set up, a change like this is live in a couple of minutes.

## 16.6 What you've done and what's left out

In this chapter you've lined up almost everything from Parts I-IV: Superpowers with brainstorming and the visual companion, Plan Mode, a spec written before the code, a plan of atomic tasks, subagents, a review after every task, one commit per task and a deploy with a preview.

To be honest, a landing page leaves out a lot of what a real product needs:

- no backend and no API: the page calls no endpoints and stores no data;
- no database;
- no authentication: "Start for free" leads to an external app, and sign-up happens there;
- no serious forms: there's no contact form with validation, CAPTCHA and email delivery;
- no state shared across pages, because there's only one page;
- no analytics or A/B tests, which a real landing page needs to measure conversions;
- a single language, English.

That's on purpose: a small project lets you learn the rhythm of the workflow without infrastructure getting in the way, and if something goes wrong, nothing bad happens.

| Project | Stack | Size |
|---|---|---|
| Landing page (chapter 16) | React 19, Vite 6, Tailwind CSS v4, Firebase Hosting | 1 page, 10 tasks |
| Photogallery (chapters 17-23) | Laravel 13, Filament v5, React 19, Vite 6, Tailwind CSS v4, AWS | REST API and admin, 124 tasks in 14 phases |

Part VI builds the Photogallery: a Laravel 13 REST API under `/api/v1`, a Filament v5 admin panel, a React frontend with login through Sanctum tokens, queued jobs for photo resizing and EXIF extraction, and a deploy on AWS with CloudFormation. The method is the same as in this chapter (spec, atomic tasks, review, commit), with requirements, design and tasks in three separate documents, execution in waves and reviews done with other models too. What changes is the scale: here you had 10 tasks, there you'll have 124.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

For your next landing page, adapt this template:

```text
I want to build a landing page for [PRODUCT NAME].

Product description:
[2-3 sentences describing the product and its main value]

Audience:
[who the target users are]

Main call to action:
[e.g. "Start for free", "Book a demo", "Download the app"]

Sections to include:
- Hero with headline, subtitle, CTA and image/video
- Features (4-6 main features with icons)
- [optional section, e.g. "How it works" with 3 steps]
- Social proof (testimonials or customer logos)
- Pricing (N plans, with a monthly/yearly toggle if there is one)
- FAQ (6-8 most frequent questions)
- Footer with a final CTA

Style:
[e.g. "dark mode, violet accent, bold type, tech forward"
 or "light, warm colors, friendly, consumer startup"]

Stack:
React + Vite + Tailwind CSS (latest version)

Deploy target:
Firebase Hosting

Workflow:
1. Use the visual companion to show me 3 layout variants
2. Once the layout is approved, generate the specs in docs/SPEC.md
3. Create the plan in docs/PLAN.md with atomic tasks and done criteria
4. Run one task at a time and wait for my confirmation
5. Code review after all the components, before the deploy
6. Build + firebase deploy --only hosting

Start in Plan Mode. Don't write any code until the specs are approved.
```

With manual confirmations, budget 60-90 minutes of session time, a bit less in subagent-driven mode.
:::

## Summary {.unlisted}

- Before writing React, settle the design with the visual companion: the HTML drafts in `.superpowers/brainstorm/` are cheap and you can throw them away without regret.
- Reread the spec before approving it. Copy, prices and behavior decided there don't turn into fix tasks later.
- Run the plan one task at a time, with a confirmation, a look at the diff and a check in the browser. One commit per task makes every mistake easy to find and to revert.
- Do an overall review across all the sections before the deploy, even if Superpowers has already reviewed each task.
- To publish, all you need is `firebase init hosting` with `dist` as the public directory, then `npm run build` and `firebase deploy --only hosting`. Go through a preview channel when someone has to sign off.
- If the design already exists, rebuild it from a screenshot and iterate one theme at a time.

## Exercise {.unlisted}

Build your own landing page, not FluentAiPro's: a side project, your portfolio, an open source project that deserves a better page.

1. Create a new folder, run `git init` and start Claude Code in Plan Mode.
2. Have the visual companion propose three visual directions, pick one and iterate on the sections.
3. Have Claude generate the spec and the atomic-task plan, and read both before approving them.
4. Run one task at a time and commit after each one.
5. Do an overall review before the deploy and commit the fixes separately.
6. Publish to a preview channel, then to production.

Start small, with hero, features and footer, and add sections later. Growing a minimal structure is easier than cutting back an overambitious one. To compare your work with mine, the finish line is the `book/cap-10-5-deploy-ready` branch.

The exercise is done when your `.web.app` URL answers over HTTPS, `npx vitest run` is green and `git log --oneline` shows one commit for every task in the plan.
