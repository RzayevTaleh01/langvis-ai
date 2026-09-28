<p align="center"><img src="docs/logo.png" alt="langvis.ai" width="320"></p>

**An AI language teacher you talk to.**
LangVis teaches a language by voice, in your browser. You speak, it writes down
exactly what you said, checks it, shows your mistakes on a board, and answers -
like a patient teacher sitting next to you. It works for any level from your
first words (A1) to fluent speech (C1).

![A course lesson on the board](docs/screenshots/09-lesson-words.png)

| | |
|---|---|
| **Two ways to learn** | **Courses** - step-by-step lessons, week by week · **Tutor** - free conversation about anything |
| **Languages** | English and Slovak today (each with its own level and progress); new languages and courses can be added |
| **Courses** | English small talk (A2 → B1) · English phrasal verbs (A2 → B1+) · Slovak small talk (A1 → A2) · Slovak from zero (A1 → B1) |
| **Voice** | real-time two-way audio through the Gemini Live API |
| **Your progress** | level over time, every mistake, a dictionary of every word, 71 grammar rules |
| **Platform** | Python server + a Next.js page in any modern browser · Windows, macOS, Linux |

---

## Contents

- [Quick start](#quick-start)
- [A short tour](#a-short-tour)
- [Courses](#courses)
- [Tutor](#tutor)
- [Account, Dictionary and Grammar](#account-dictionary-and-grammar)
- [How the system works](#how-the-system-works)
- [The mascot](#the-mascot)
- [Languages and levels](#languages-and-levels)
- [What is saved](#what-is-saved)
- [Project structure](#project-structure)
- [Extending LangVis](#extending-langvis)
- [Limits and privacy](#limits-and-privacy)

---

## Quick start

```bash
docker compose up -d
```

```bash
python setup.py
```

```bash
python main.py
```

- `docker compose up -d` starts the database (PostgreSQL on port 5433, only
  reachable from this computer). The defaults work as they are; copy
  `.env.example` to `.env` to change them.
- `setup.py` installs the Python packages. `main.py` starts LangVis and opens
  http://localhost:8765 (`python main.py --no-open` starts only the server).
- The page is built with Next.js into `frontend/out`, and the Python server
  serves it. After changing the page, build it again:

```bash
cd frontend && npm install && npm run build
```

Then:

1. **Sign up** with your name, email and a password. Every account keeps its own
   level, courses, words, history and settings.
2. Paste a free [Gemini API key](https://aistudio.google.com/apikey) when the
   page asks for it.
3. In **Settings** (click your name at the top right) choose your own language
   (for translations), the speaking pace and how strictly to correct.
4. Open **Courses** and press **Start the lesson** - or open the **Tutor** and
   press **Start**. Allow the microphone and talk. You can also type.

---

## A short tour

The home page explains LangVis and shows the courses; the mascot walks beside
the text as you scroll. Signed in, it greets you and takes you back to your
course or to the Tutor.

| Home | The courses | Signed in |
|---|---|---|
| ![Home](docs/screenshots/01-home.png) | ![The courses on the home page](docs/screenshots/02-home-courses.png) | ![Home, signed in](docs/screenshots/06-home-signed-in.png) |

Signing up and logging in are friendly: the mascot says hello to your name,
watches your email being typed, and closes its eyes while you type your
password (it peeks now and then). When login works it is glad; when the
password is wrong it is sad.

| Sign up | Log in | Signed in |
|---|---|---|
| ![Sign up](docs/screenshots/03-sign-up.png) | ![Log in](docs/screenshots/04-log-in.png) | ![Signed in](docs/screenshots/05-signed-in.png) |

---

## Courses

A course is a fixed path of lessons for one language and level. The teacher
follows it step by step, never skips anything, and remembers exactly where you
stopped. A language can have more than one course; they show as tabs. The
syllabus shows every week and lesson: its words, grammar, parts and speaking task.

| The Courses page | The syllabus |
|---|---|
| ![The Courses page](docs/screenshots/07-courses.png) | ![The syllabus](docs/screenshots/08-syllabus.png) |

| Course | Levels | Size |
|---|---|---|
| **English · Small talk** - how are you, work, the weekend, plans, and chats in a café, a shop, at university, at work, at a party, on a train | A2 → B1 | 20 lessons, 5 weeks |
| **English · Phrasal verbs for daily speaking** - the phrasal verbs people really use, in longer and longer sentences | A2 → B1+ | 20 lessons, 5 weeks |
| **Slovak · Small talk** - the small talk method from the first words: greetings, weather, work, and then real places | A1 → A2 | 28 lessons, 7 weeks |
| **Slovak · From zero** - from "Ahoj!" to talking about your life, work, plans and opinions | A1 → B1 | 30 lessons, 6 weeks |

### One lesson

Every lesson has the same parts, each shown on the board: **words**, ready
**phrases**, one **grammar** point, **longer sentences**, a **dialogue**,
**translation** or **sentence building**, **questions about your own life**, and
at the end a **speaking task** where you just talk. The outline on the left
shows where you are.

The teacher asks you to say each item. It checks what you said: every word
must be there (small slips and accents are forgiven, names may be your own).
If it is not right, you hear it again once - then the lesson goes on, so you
never get stuck.

The **small talk method** is practised in every small talk lesson: never give
a one-word answer. React, answer, add one small detail, and ask back. The
"Longer sentences" part shows one answer growing step by step.

| A wrong repeat: "Again" | A grammar point | A sentence growing longer |
|---|---|---|
| ![A wrong repeat](docs/screenshots/10-lesson-again.png) | ![A grammar point](docs/screenshots/11-lesson-grammar.png) | ![A sentence growing longer](docs/screenshots/12-lesson-longer.png) |

**Every word is taught before it is asked for.** Each lesson's word list holds
every word the learner has to say in it; in the free speaking part the teacher
may only use what the course has taught so far - a new word is taught first.

---

## Tutor

The Tutor is free conversation - your own teacher, ready for whatever you
need: talk about anything, ask about a word or a rule, get ready for a trip or
an interview. Choose a **topic** at the top of the side panel - or write
**your own scenario** ("be a barista, I am the customer") and the tutor builds
the conversation around it. The topic's words fill the side panel once you start.

| The Tutor before Start | Topics and your own scenario |
|---|---|
| ![The Tutor before Start](docs/screenshots/13-tutor.png) | ![Topics](docs/screenshots/14-tutor-topics.png) |

A sentence with mistakes is corrected once, kindly: the board underlines the
mistakes, shows the corrected sentence and why, and offers a better way to say
it one level up; "You can say" gives ideas for your next answer. Ask about any
grammar ("Can you explain the past simple?") and the rule is drawn on the
board. Under the microphone you always see **exactly what the system heard**.

| A correction | Grammar on the board |
|---|---|
| ![A correction](docs/screenshots/15-tutor-correction.png) | ![Grammar on the board](docs/screenshots/16-tutor-grammar.png) |

---

## Account, Dictionary and Grammar

- **Account** - your level over time, how your dictionary grows, your mistakes
  per day, where they are, and every correction ever made.
- **Dictionary** - every word and phrase you met: how often and on how many
  different days you used it. A word comes back in your lessons until it is yours.
- **Grammar** - every rule from A1 to B2 and how well you know it, measured from
  what you actually say. Click a rule to see your own mistakes and the rule.

| Account | Dictionary | Grammar |
|---|---|---|
| ![Account](docs/screenshots/17-account.png) | ![Dictionary](docs/screenshots/18-dictionary.png) | ![Grammar](docs/screenshots/19-grammar.png) |

---

## How the system works

LangVis **checks before it answers**. A voice model on its own answers the
moment you stop, before anything has looked at what you said. Here the server
decides when your sentence ends, writes it down, checks it, decides the reply -
and only then lets the teacher speak.

```
you speak
   │
   ├─ the server hears where your sentence ends (a pause of 1.6 - 2.4 s, longer for beginners)
   │     the check already starts during the pause, to save time
   │
   ├─ 1. WRITE IT DOWN  - exactly your words, mistakes kept; no guessing
   │                      (noise, typing or silence give nothing at all)
   ├─ 2. CHECK IT       - mistakes, the grammar behind them, a better version
   ├─ 3. DECIDE         - "Good." / "Again: …" / a correction / the next step
   │
   └─ the teacher gets your sentence AS TEXT (what you see under the microphone)
      and the decided reply, and says it; its words appear with its voice
```

### Hearing you correctly

- **Only what you really said.** The transcriber knows nothing about the lesson,
  so it cannot "hear" a fitting answer in noise. Too many words for too little
  speech are thrown away. The teacher never gets the raw audio - only the text
  you see - so it cannot make its own guess.
- **Talk as long as you like.** The pause that ends a sentence is long for
  beginners (2.4 s at A1, 2.1 s at A2, 1.8 s at B1, 1.6 s above) and grows
  after a long stretch of talking. If you go on talking while your sentence is
  being checked, the check is dropped and the whole sentence is heard together.
  One turn may last a minute.
- **Repeating is not an echo.** The teacher's own voice coming back through
  the speakers is dropped, but you repeating the phrase you were asked to say -
  even quickly - counts.
- **Your facts stay yours.** If you say "I live in Prešov", a correction or a
  better version never turns it into the course's example city; the teacher
  remembers your fact for the rest of the lesson.

### Speed

- The checking calls ask the model not to think at length, have a short
  timeout, and when a model is slow a second one starts beside it - the first
  good answer wins.
- The check starts already during the pause that may end your sentence.
- The log shows each turn's timing: `[Speed] silence->checked … · checked->voice …`.

### The board and the teacher's voice

The teacher's words are sent to the page in step with its voice and typed out
as it speaks; its mouth takes the shape of the letter being said. When it
explains something on the board, it walks to it.

---

## The mascot

The LangVis face is also a small mascot that guides you through the pages:

- **Home, Courses, Account, Dictionary, Grammar** - it says what the page is
  about, then walks beside the headings as you scroll. It looks for the next
  part while you scroll and says "wow" when it finds it. It never covers the
  text and never blocks a click.
- **Log in and Sign up** - it sits on the form and reacts to each field.
- **Not in a lesson or the Tutor** - there the teacher itself is on the board.

---

## Languages and levels

| Language | Starts at | Explained in |
|---|---|---|
| English | A2 | simple English |
| Slovak | A1 | simple English at A1, simple Slovak from A2 |

Your own language (Azerbaijani, Turkish or Russian) is used for translations on
the board and in the dictionary. Each language keeps its own level, courses,
words and history. The level is measured from what you say and shown in the
header.

---

## What is saved

Everything is kept in the PostgreSQL database of `docker-compose.yml` - there
are no data files.

| Table | What it holds |
|---|---|
| `users` · `sessions` | the accounts (a scrypt hash of the password) and their signed-in browsers |
| `app_settings` | the Gemini keys, shared by all accounts on this computer |
| `user_settings` | the account's name, voice and tutor settings |
| `user_memory` | what LangVis remembers about the learner, and short lesson summaries |
| `learner_progress` | per language: level, skills, mistakes, dictionary - the source of truth |
| `learner_reports` | per language: a readable summary, made from the progress |
| `course_progress` | per course: the current lesson and step, and the finished lessons |
| `topic_materials` | each topic's word list and its first lesson |
| `conversation_lines` | every line of every conversation |

There is one microphone and one voice lesson, so one account uses LangVis at a
time: when another account signs in, the first one's lesson stops (its progress
is kept).

---

## Project structure

```
main.py                        starts the server and opens the browser
setup.py                       installs the Python packages
docker-compose.yml             the PostgreSQL database

web/
  server.py                    aiohttp server: the page, the WebSocket, JSON for the pages
  auth.py                      accounts: sign up, log in, sessions
  bridge.py                    the lesson's messages to every open tab

core/
  live.py                      the Gemini Live session: when a sentence ends, the check
                               before the reply, the voice, echo, speed
  prompt.txt                   the teacher's core instructions
  store.py                     every piece of data, in PostgreSQL
  plugin_loader.py · profile.py · selflog.py

tutor/
  analysis.py                  writing down and checking a sentence (Gemini, with fallbacks)
  curriculum.py · slovak.py    skills, rules and stages; the languages
  english_small_talk.py        English · Small talk (20 lessons)
  intensive_english.py         English · Phrasal verbs (20 lessons)
  slovak_small_talk.py         Slovak · Small talk (28 lessons)
  intensive_slovak.py          Slovak · From zero (30 lessons)
  topics.py                    the Tutor's topics and their word lists
  progress.py                  the learner's level, skills and dictionary

plugins/
  language_tutor.py            the teacher: taught steps, courses, the check,
                               corrections, the board, the pages' data

memory/                        settings and memory (stored through core/store.py)

frontend/                      the page (Next.js, built into frontend/out)
  src/app/                     Home, Courses, lesson, Tutor, Account, Dictionary, Grammar, Log in, Sign up
  src/components/              the header, the classroom, the mascot, dialogs, shadcn/ui
  src/legacy/                  the board, the teacher's face (tutor.js), diagrams, audio
  public/                      the logo, the pictures on the home page, the microphone worklet

docs/                          the logo and screenshots/ - the pictures in this file
```

---

## Extending LangVis

### A new course

1. Write a file like `tutor/english_small_talk.py`: a list of lessons, each with
   words, phrases, one grammar point, a dialogue, longer sentences, translation
   or building tasks, questions and a speaking task.
2. Make sure every word the learner has to say is taught in the lesson (or an
   earlier one) - add missing ones to its word list (`MORE_WORDS` in the
   Slovak courses shows how).
3. Register it in `INTENSIVE_COURSES` and `COURSE_CATALOG` in
   `plugins/language_tutor.py`. It appears on the Courses page, as a tab next
   to the other courses of its language.

### Plugins

Any file in `plugins/` with a `PLUGIN` dict and a `run()` function becomes a
tool the teacher can call. Start from `plugins/_template.py`.

| Hook | Use |
|---|---|
| `observe(text, player)` | see every sentence |
| `format_for_prompt()` | standing instructions for every session |
| `opening_note()` | the first thing the teacher says in a lesson |
| `gate_audio()` / `gate_text()` | hear and check a sentence, and decide the reply before the teacher speaks |
| `status_for_ui()` / `coaching_for_ui()` | what the page shows |
| `PLUGIN_SETTINGS` | fields in the settings form |

### Screenshots

The pictures in this file were taken with a demo account on this computer
(its test email and password are in `.env.example`) in a headless browser at
1440 × 900.

---

## Limits and privacy

- A **free Gemini key** has daily limits. When a model is busy or its limit is
  used up, the next model takes over; when all are spent, the page says why the
  teacher is quiet. More keys can be added in Settings.
- The server listens on this computer only, and only its own page may connect.
- Your API key, settings, memory and all progress stay on your computer, in the
  local database. Your voice is sent only to the Gemini API during a lesson.

---

## Author

**Taleh Rzayev** - design, code and curriculum.
