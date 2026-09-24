# LangVis

**A speaking language course in your browser.**
You pick a topic and talk. LangVis thinks about every sentence before it
answers, corrects it, makes it one level richer, has you say both versions,
and takes you from **A2 to B2** inside every topic.

> LangVis is not a chatbot or an assistant. It does not open apps, control
> your computer or search the web. It has one job: to make you speak better.

| | |
|---|---|
| **Languages** | English (active) · Slovak (planned) |
| **Course** | 6 stages × 4 units = 24 grammar units, A2.1 → B2.2, climbed in every topic |
| **Topics** | 13 ready topics + your own, each with a fixed A2 / B1 / B2 word list |
| **Voice** | real-time two-way audio through the Gemini Live API |
| **Platform** | Python server + any modern browser · Windows, macOS, Linux |

---

## Contents

- [Quick start](#quick-start)
- [The screen](#the-screen)
- [One sentence, step by step](#one-sentence-step-by-step)
- [Topics](#topics)
- [The dictionary](#the-dictionary)
- [Hesab - your account](#hesab---your-account)
- [The course](#the-course)
- [What it tracks](#what-it-tracks)
- [Project structure](#project-structure)
- [Extending LangVis](#extending-langvis)
- [Limits and privacy](#limits-and-privacy)

---

## Quick start

```bash
python setup.py   # installs the dependencies
python main.py    # starts LangVis and opens http://localhost:8765
```

1. Paste a free [Gemini API key](https://aistudio.google.com/apikey) when the
   page asks for it.
2. Open **⚙ Settings**: your level, your own language, the pace, how strictly
   to correct, the tutor's voice.
3. Pick a **topic** in the header, press **Start lesson**, allow the
   microphone, and talk.

`python main.py --no-open` starts the server without opening a browser tab.

---

## The screen

```
┌ LangVis  A2 · 31/100 → B2  [A2.1 · Unit 3/24 Past simple · 90%]   (💬 Work ▾)  Lesson  Dictionary  Hesab  ⚙ ┐
├──────────────────────────────────────────────────────────────┬──────────────────────┤
│ WORK · A2.1 · UNIT 3/24                        Your turn    │ TOPIC WORDS │ TRANSCRIPT│
│ YOU SAID    Yesterday I go① to office②                       │ B1 · 3/12 learned     │
│ CORRECTED   Yesterday I went to the office.                  │ run late   phrasal ●●○○│
│    (tutor)  ① past simple - yesterday = past                 │ deal with  phrasal ●○○○│
│ SAY IT BETTER   I headed to the office early yesterday.      │ heavy traffic colloc. │
│             head to · phrasal verb · B1 - go to · getmək     │ OLD WORDS - USE AGAIN │
│ YOUR GRAMMAR    ▼ past simple 72 → 65                        │ make a decision       │
│ ▌LANGVIS  Did you mean: Yesterday I went to the office? Say it.                      │
├──────────────────────────────────────────────────────────────┴──────────────────────┤
│ ( Type a sentence and press Enter…                ➤ )  Fluency · 2 min  Interrupt  🎤 │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

| Area | What it shows |
|---|---|
| **Header** | Your level, where this topic is in the course (click it for all 24 units and your progress), the topic select, the pages, ⚙ settings. |
| **Board** | Your sentence as the analyser heard it - mistakes kept, never smoothed over - then the corrected sentence, the richer version with each new item explained and translated, and which grammar went up or down. |
| **The tutor** | The LangVis face, drawn at runtime. It walks across the board and stands under the word it is explaining, with a speech bubble. Click anything on the board and it goes there and explains it. Rim colour: green listening, mustard thinking, terracotta speaking, rose mic off. |
| **Subtitles** | What the tutor is saying, at the bottom of the board. |
| **Topic words** | The topic's fixed list, one level above you, with how often and on how many different days you used each item. |
| **Transcript** | The conversation, to read back. |

---

## One sentence, step by step

LangVis **thinks before it answers**. A live voice model normally replies the
instant you stop talking - before anything has checked what you said. Here the
server decides when your turn ends, holds the tutor's reply, and while the face
shows it is thinking your own voice is transcribed (mistakes kept) and
analysed. Only then does the tutor speak, told exactly what to say.

```
you speak ──▶ thinking (1-3 s) ──▶ mistake?  "Did you mean: …? Say it."        ──▶ you repeat ✓
                                                                                       │
                                   correct?  "Better: … Now you say it."  ◀─────────────┘
                                                                         ──▶ you repeat ✓
                                   "Good." + an answer + the next question, built so that
                                   the answer needs one of your topic words or old words
```

- **A repeat is checked by the system**, not by the model: it must match the
  sentence and contain the part that matters - the corrected words, or the new
  phrase. "Almost - missing *running late*" is shown on the board.
- A repeat is asked for at most twice, then the lesson moves on.
- **"Better"** always lifts the sentence one level: a phrasal verb, a
  collocation, a stronger word - never a different meaning.
- **I didn't say that** takes the last sentence back if it was misheard.
- **Fluency · 2 min** - you talk without being stopped; the feedback comes at
  the end.
- Typed sentences go through exactly the same steps.

---

## Topics

Pick one in the header: Daily life, Work, Home, Food, Shopping and money,
Travel, Health, Free time, Family and friends, Technology, City and transport,
Education, Opinions and society - or **your own** (football, programming…).

- **Every topic climbs the whole course, A2 → B2.** The topic stays the same;
  the questions grow up with the grammar: describing at A2, experiences and
  stories at B1, opinions and "what would have happened if…" at B2.
- Grammar belongs to you, not to a topic: a unit whose skills are already
  strong passes after a short check in a new topic, so later topics climb
  faster and focus on words.
- Each topic's word list is **written once**, the first time you open it, in
  three tiers (A2 / B1 / B2) of phrasal verbs, collocations, stronger words and
  ready expressions - then it never changes. You always see the tier one level
  above you; when most of it is learned the next tier opens.

---

## The dictionary

Every item you meet - the topic lists and every upgrade the board showed you -
is kept for good.

| Status | Means | Comes back |
|---|---|---|
| new | not used yet | in its topic, until you use it |
| learning | used on 1-2 different days | after 1, then 3 days |
| learned | used on 3+ different days | after 7 or 14 days |
| strong | used on 5+ different days | every 30 days, forever |

Two uses in one conversation prove nothing, so the ladder counts **different
days**. A wrong use drops the item a step and brings it back the same day. Due
items come back in **whatever topic you are in** - the tutor builds a question
that needs them (at most five per lesson).

The **Dictionary** page lists everything: uses, wrong uses, days, last use,
next review, and your own sentences with each item. Filter by topic, kind or
status.

---

## Hesab - your account

- **Level over time**, **dictionary growth**, **mistakes per day** and **where
  the mistakes are** (by grammar) - as charts with hover values.
- **Grammar syllabus** - all ~36 skills by level with mastery, right and wrong
  uses; click one for the rule and your own mistakes.
- **Course** in the current topic, and how far **every topic** has come.
- **All my mistakes** - every correction ever made, filterable by grammar.

---

## The course

| Stage | Title | Units |
|---|---|---|
| **A2.1** | Everyday forms | Present simple & questions · Present continuous · Past simple · Articles, prepositions & word order |
| **A2.2** | Talking beyond now | Future: going to & will · Comparatives & quantity · Modals: can, must, should · Linking a story together |
| **B1.1** | Perfect and past | Present perfect · Past continuous & used to · Perfect vs past simple · First conditional & possibility |
| **B1.2** | Longer sentences | Second conditional · Verb patterns: -ing or to · Relative clauses & word forms · Passive voice |
| **B2.1** | Precision in the past | Past perfect · Third conditional & wishes · Reported speech · Modals of deduction |
| **B2.2** | Range and control | Advanced passive · Future continuous & perfect · Discourse markers · Collocation & natural choice |

A unit passes when you have spoken enough in it and its target grammar is
strong. A stage passes when your measured level reaches the stage goal. The
grammar is taught through conversation about your topic, not through drills -
a short drill runs only when the same mistake keeps coming back, or when you
ask for one.

---

## What it tracks

| Tracked | Meaning |
|---|---|
| **Level** | rolling CEFR score over your recent sentences |
| **Skills** | ~36 grammar skills, each with mastery, real mistakes and a review date |
| **Mistakes** | every correction: what you said, the fix, the grammar, the topic |
| **Course** | the unit and stage of every topic |
| **Dictionary** | every item: uses, days, your sentences, next review |
| **Missing words** | things you said in your own language, until you say them in English |

Progress is saved per language, for example in `english/`:

- `level.json` - the raw numbers (source of truth)
- `progress.md` - a readable summary, regenerated from `level.json`
- `topics/*.json` - each topic's fixed word list

---

## Project structure

```
main.py                     starts the server and opens the browser
setup.py                    installs dependencies
requirements.txt

web/
  server.py                 aiohttp server: page, WebSocket, JSON for the pages
  bridge.py                 WebUI - the session's messages to every open tab
  static/                   the page: board, tutor, dictionary, account (no build step)
    app.js                  socket, header, pages, settings
    board.js                the board and the tutor's walk across it
    tutor.js                the LangVis face (SVG) and its movement
    pages.js                dictionary and account pages, charts
    audio.js                microphone out, voice in
    mic-worklet.js          microphone → 16 kHz PCM

core/
  live.py                   the Gemini Live session: turns, thinking, voice, tools
  prompt.txt                the tutor's core instructions
  plugin_loader.py          finds plugins: tools, observers, prompt blocks
  selflog.py                keeps a log of LangVis's own output and errors

tutor/
  curriculum.py             skills, rules, stages, units, methods
  topics.py                 topics, question depth, the fixed word lists
  progress.py               learner state: level, skills, course, dictionary, account
  analysis.py               per-sentence analysis (from text or from your voice)

plugins/
  language_tutor.py         the tutor: think → correct → enrich → record
  _template.py              starting point for a new plugin

memory/                     settings and what LangVis remembers about you
config/                     your local API key
```

---

## Extending LangVis

### Plugins

Any file in `plugins/` with a `PLUGIN` dict and a `run()` function becomes a
tool the tutor can call. Start from `plugins/_template.py`. Optional hooks:

| Hook | Use |
|---|---|
| `observe(text, player)` | see every sentence |
| `format_for_prompt()` | add standing instructions to every session |
| `PLUGIN_SETTINGS` | fields in the ⚙ settings form |
| `status_for_ui()` / `syllabus_for_ui()` / `coaching_for_ui()` | appear in the page |
| `gate_audio()` / `gate_text()` | decide the tutor's reply before it speaks |

### Adding a language (e.g. Slovak)

1. Write its skills, stages and model sentences in `tutor/curriculum.py`.
2. Add a word-level detector for it in `tutor/analysis.py`.
3. Set `LANGUAGES["slovak"]["enabled"] = True`.

---

## Limits and privacy

- A **free Gemini key** has daily limits. The per-sentence analysis uses the
  fast model, which has the larger allowance; when a limit is reached the tutor
  keeps talking and the board says why it is quiet.
- The server listens on `127.0.0.1` only, and only its own page may connect to
  it.
- Your API key, settings, memory and all progress files (`english/`,
  `slovak/`) stay on your computer and are git-ignored. Audio is sent only to
  the Gemini API during a lesson.

---

## Author

**Taleh Rzayev** - design, code and curriculum.
