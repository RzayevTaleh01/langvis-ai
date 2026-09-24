"""
tutor/curriculum.py - what is taught, in which order.

THE SHAPE OF THE COURSE
    Six stages take a learner from A2 to B2. Each stage has four units, and
    each unit teaches one or two grammar skills inside one everyday theme, with
    a speaking task that forces those skills to be used out loud.

        A2.1 → A2.2 → B1.1 → B1.2 → B2.1 → B2.2 → (course done, B2)

    Units are layered: a later unit assumes the skills of every earlier one, so
    a mistake on an old skill is never "out of scope" - it goes back on the
    focus list and is reviewed until it is strong again.

HOW A UNIT IS PASSED
    Not by time, and not by vocabulary: a unit is a grammar unit. It is done
    when the learner has spoken enough in it (UNIT_MIN_PRACTICE substantial
    sentences) AND every target skill has been used correctly at least
    SKILL_MIN_CORRECT times with mastery at or above SKILL_PASS. A stage is done when all its units are done AND the measured
    level has reached the stage's exit score. Until then the stage stays open
    in a "consolidation" layer: free conversation at that level, aimed at the
    weakest skills.

GRAMMAR HERE, VOCABULARY ELSEWHERE
    This file is the grammar base and nothing else: the ladder of forms, each
    unit's model sentences, the rule behind every skill (SKILL_TIPS) and the
    techniques it is drilled with. A fixed word list per unit would fight the
    learner - they talk about their own day, their own work - so vocabulary is
    not in the course at all. It is a live dictionary, grown from whatever they
    are actually talking about, suggested per sentence by the analyser and
    tracked in tutor/progress.py.

HOW IT IS TAUGHT
    A unit is not just its grammar and its sentences: it also names the
    techniques it is practised with (METHODS below) - substitution drills,
    dictogloss, 4/3/2 fluency, information gaps, role play, pushed output,
    spaced review. The tutor is handed those instructions with the unit, so
    the lesson has a method and not only a topic.

LANGUAGES
    English is the only active course. Slovak is declared so the mode exists in
    settings and on screen, but it is disabled until its curriculum is written.
"""
from __future__ import annotations

UNIT_MIN_PRACTICE = 12     # substantial sentences spoken while the unit is active
SKILL_PASS        = 70     # mastery a target skill needs to pass the unit
SKILL_MIN_CORRECT = 3      # …and this many correct uses as evidence

BAND_ORDER = ("A1", "A2", "B1", "B2", "C1", "C2")


# ── Skills ───────────────────────────────────────────────────────────────────
# id -> (name, band, one-line hint the tutor can say to explain it)

ENGLISH_SKILLS: dict[str, tuple[str, str, str]] = {
    # A2
    "present_simple":         ("present simple", "A2",
                               "habits and facts: I work, she works"),
    "present_continuous":     ("present continuous", "A2",
                               "now: I am working, they are eating"),
    "past_simple":            ("past simple", "A2",
                               "finished past: I went, I didn't go, did you go?"),
    "future_forms":           ("future (going to / will)", "A2",
                               "plans: I'm going to…; decisions now: I'll…"),
    "questions":              ("question forms", "A2",
                               "do/does/did + subject + verb: Where do you live?"),
    "word_order":             ("word order", "A2",
                               "subject + verb + object + place + time"),
    "subject_verb_agreement": ("subject-verb agreement", "A2",
                               "he/she/it + -s; people are, a person is"),
    "articles":               ("articles (a / an / the)", "A2",
                               "a = one of many, the = the one we know"),
    "plurals_quantity":       ("plurals and quantity", "A2",
                               "some/any, much/many, a lot of, countable nouns"),
    "prepositions":           ("prepositions of time and place (in / on / at)", "A2",
                               "in/on/at for time and place, to/from"),
    "pronouns_possessives":   ("pronouns and possessives", "A2",
                               "I/me/my/mine, Taleh's car"),
    "comparatives":           ("comparatives and superlatives", "A2",
                               "bigger than, more expensive, the best"),
    "modals_basic":           ("can / must / should", "A2",
                               "can + verb, should + verb - no 'to'"),
    "linking_words":          ("linking words", "A2",
                               "and, but, because, so, then, although"),
    "word_choice":            ("word choice", "A2",
                               "the right word for the meaning"),
    # B1
    "present_perfect":        ("present perfect", "B1",
                               "experience and results: I have been, have you ever…?"),
    "perfect_vs_past":        ("present perfect vs past simple", "B1",
                               "yesterday → past simple; ever/already/yet → perfect"),
    "past_continuous":        ("past continuous", "B1",
                               "I was walking when it started to rain"),
    "used_to":                ("used to", "B1",
                               "past habits: I used to play football"),
    "first_conditional":      ("first conditional", "B1",
                               "If it rains, I will stay home"),
    "modals_possibility":     ("might / could / have to", "B1",
                               "possibility and obligation"),
    "second_conditional":     ("second conditional", "B1",
                               "If I had money, I would travel"),
    "gerund_infinitive":      ("-ing or to + verb", "B1",
                               "enjoy doing, want to do, stop to / stop doing"),
    "phrasal_verbs":          ("phrasal verbs", "B1",
                               "get up, look for, find out, give up"),
    "relative_clauses":       ("relative clauses", "B1",
                               "the man who…, the place where…, the thing that…"),
    "passive_simple":         ("passive (simple)", "B1",
                               "It is made in… / It was built in…"),
    "word_forms":             ("word forms", "B1",
                               "happy/happiness/happily - noun, adjective, adverb"),
    # B2
    "past_perfect":           ("past perfect", "B2",
                               "the earlier past: When I arrived, he had left"),
    "third_conditional":      ("third conditional", "B2",
                               "If I had known, I would have come"),
    "wish_regret":            ("wish / if only", "B2",
                               "I wish I had more time; I wish I had studied"),
    "reported_speech":        ("reported speech", "B2",
                               "She said (that) she was tired"),
    "modals_deduction":       ("must have / might have / can't have", "B2",
                               "speculating about the past"),
    "passive_advanced":       ("passive (advanced)", "B2",
                               "It is said that…, has been done, will be done"),
    "future_advanced":        ("future continuous / perfect", "B2",
                               "I'll be working; I'll have finished by then"),
    "discourse_markers":      ("discourse markers", "B2",
                               "however, on the other hand, in fact, as a result"),
    "collocations":           ("collocations", "B2",
                               "make a decision, do homework, heavy rain"),
}


# ── Stages and units ─────────────────────────────────────────────────────────

ENGLISH_STAGES: list[dict] = [
    {
        "id": "A2.1", "band": "A2", "title": "Everyday forms", "exit_score": 26,
        "units": [
            {"id": "en-01", "title": "Present simple & questions",
             "skills": ["present_simple", "questions"],
             "can_do": "talk about habits and ask simple questions",
             "examples": ["I get up at seven every day.",
                          "She works in a hospital.",
                          "What time do you start work?"]},
            {"id": "en-02", "title": "Present continuous",
             "skills": ["present_continuous", "subject_verb_agreement"],
             "can_do": "tell 'I work' from 'I am working'",
             "examples": ["I am cooking dinner now.",
                          "They are waiting outside.",
                          "What are you doing this week?"]},
            {"id": "en-03", "title": "Past simple",
             "skills": ["past_simple"],
             "can_do": "talk about finished past events",
             "examples": ["I went there on Saturday.",
                          "We ate fish and drank tea.",
                          "I didn't work last weekend."]},
            {"id": "en-04", "title": "Articles, prepositions & word order",
             "skills": ["articles", "prepositions", "word_order"],
             "can_do": "put a/the and in/on/at in the right places",
             "examples": ["There is a park near my house.",
                          "I live in a flat on the third floor.",
                          "I read a book at home every evening."]},
        ],
    },
    {
        "id": "A2.2", "band": "A2", "title": "Talking beyond now", "exit_score": 38,
        "units": [
            {"id": "en-05", "title": "Future: going to & will",
             "skills": ["future_forms"],
             "can_do": "talk about plans and decisions",
             "examples": ["I am going to visit my family next month.",
                          "I think it will rain tomorrow.",
                          "I'll call you later."]},
            {"id": "en-06", "title": "Comparatives & quantity",
             "skills": ["comparatives", "plurals_quantity"],
             "can_do": "compare things and talk about how much there is",
             "examples": ["This one is cheaper than that one.",
                          "It is the best in the city.",
                          "I don't have much time today."]},
            {"id": "en-07", "title": "Modals: can, must, should",
             "skills": ["modals_basic", "pronouns_possessives"],
             "can_do": "give advice and talk about rules and ability",
             "examples": ["You should sleep more.",
                          "I can speak a little English.",
                          "You must not park here."]},
            {"id": "en-08", "title": "Linking a story together",
             "skills": ["linking_words", "past_simple"],
             "can_do": "join sentences into a story",
             "examples": ["First I called him, then I went home.",
                          "I was tired, so I slept early.",
                          "I wanted to go out, but it was raining."]},
        ],
    },
    {
        "id": "B1.1", "band": "B1", "title": "Perfect and past", "exit_score": 46,
        "units": [
            {"id": "en-09", "title": "Present perfect",
             "skills": ["present_perfect"],
             "can_do": "talk about experience without saying when",
             "examples": ["I have never been to Italy.",
                          "Have you ever eaten sushi?",
                          "I have already finished."]},
            {"id": "en-10", "title": "Past continuous & used to",
             "skills": ["past_continuous", "used_to"],
             "can_do": "set the background of a story and describe old habits",
             "examples": ["I was walking home when it started to rain.",
                          "I used to play football every day.",
                          "We used to live in a small village."]},
            {"id": "en-11", "title": "Perfect vs past simple",
             "skills": ["perfect_vs_past"],
             "can_do": "choose between 'I did' and 'I have done'",
             "examples": ["I have lived here for three years.",
                          "I moved here in 2021.",
                          "I haven't seen him since Monday."]},
            {"id": "en-12", "title": "First conditional & possibility",
             "skills": ["first_conditional", "modals_possibility"],
             "can_do": "talk about real possibilities and what follows from them",
             "examples": ["If I have time tomorrow, I will call you.",
                          "It might rain later.",
                          "I have to finish this today."]},
        ],
    },
    {
        "id": "B1.2", "band": "B1", "title": "Longer sentences", "exit_score": 56,
        "units": [
            {"id": "en-13", "title": "Second conditional",
             "skills": ["second_conditional"],
             "can_do": "talk about imaginary situations",
             "examples": ["If I had more money, I would travel.",
                          "If I were you, I would take it.",
                          "What would you do if you lost it?"]},
            {"id": "en-14", "title": "Verb patterns: -ing or to",
             "skills": ["gerund_infinitive", "phrasal_verbs"],
             "can_do": "say what you enjoy doing and what you want to do",
             "examples": ["I enjoy learning languages.",
                          "I want to improve my speaking.",
                          "I gave up drinking coffee."]},
            {"id": "en-15", "title": "Relative clauses & word forms",
             "skills": ["relative_clauses", "word_forms"],
             "can_do": "add detail with who, which, that and where",
             "examples": ["The man who lives next door is a doctor.",
                          "This is the book that I told you about.",
                          "She speaks English fluently."]},
            {"id": "en-16", "title": "Passive voice",
             "skills": ["passive_simple"],
             "can_do": "describe how something is done",
             "examples": ["Bread is made from flour.",
                          "This house was built in 1980.",
                          "English is spoken all over the world."]},
        ],
    },
    {
        "id": "B2.1", "band": "B2", "title": "Precision in the past", "exit_score": 63,
        "units": [
            {"id": "en-17", "title": "Past perfect",
             "skills": ["past_perfect"],
             "can_do": "put two past events in the right order",
             "examples": ["When I arrived, the film had already started.",
                          "She had never seen snow before.",
                          "They had finished before I got there."]},
            {"id": "en-18", "title": "Third conditional & wishes",
             "skills": ["third_conditional", "wish_regret"],
             "can_do": "talk about the past that did not happen",
             "examples": ["If I had studied, I would have passed.",
                          "I wish I had more time.",
                          "I wish I hadn't said that."]},
            {"id": "en-19", "title": "Reported speech",
             "skills": ["reported_speech"],
             "can_do": "report what other people said",
             "examples": ["He said he was busy that day.",
                          "She told me she would call later.",
                          "They asked where I lived."]},
            {"id": "en-20", "title": "Modals of deduction",
             "skills": ["modals_deduction"],
             "can_do": "speculate about what happened",
             "examples": ["He must have forgotten.",
                          "She might have missed the bus.",
                          "It can't have been easy."]},
        ],
    },
    {
        "id": "B2.2", "band": "B2", "title": "Range and control", "exit_score": 70,
        "units": [
            {"id": "en-21", "title": "Advanced passive",
             "skills": ["passive_advanced"],
             "can_do": "speak impersonally and formally",
             "examples": ["It is said that prices will rise.",
                          "The decision has already been made.",
                          "The report will be published next week."]},
            {"id": "en-22", "title": "Future continuous & perfect",
             "skills": ["future_advanced"],
             "can_do": "say what will be happening and what will be finished",
             "examples": ["This time next year I'll be working abroad.",
                          "By June I'll have finished the course.",
                          "They will have moved by then."]},
            {"id": "en-23", "title": "Discourse markers",
             "skills": ["discourse_markers", "linking_words"],
             "can_do": "build an argument the listener can follow",
             "examples": ["However, there is one problem.",
                          "On the one hand it is cheaper; on the other it is slower.",
                          "As a result, many people left."]},
            {"id": "en-24", "title": "Collocation & natural choice",
             "skills": ["collocations", "phrasal_verbs", "word_choice"],
             "can_do": "pick the word a speaker would actually use",
             "examples": ["I need to make a decision this week.",
                          "We had heavy rain all night.",
                          "Let's keep in touch."]},
        ],
    },
]


# ── Grammar tips ─────────────────────────────────────────────────────────────
# Shown on screen the moment a mistake touches the skill, so the explanation
# arrives while the sentence is still in the learner's head. Written out here
# rather than generated: a rule the learner sees twice should read the same way
# both times, and it costs nothing to show.
#
# id -> (rule, [two examples])

SKILL_TIPS: dict[str, tuple[str, list[str]]] = {
    "present_simple": (
        "Habits and facts. Add -s only for he / she / it.",
        ["I work in an office.", "She works in a hospital."]),
    "present_continuous": (
        "Happening now or around now: am / is / are + verb-ing.",
        ["I am working right now.", "They are waiting for us."]),
    "past_simple": (
        "Finished past. Regular verbs take -ed; many common verbs are "
        "irregular. After didn't, use the base verb.",
        ["I went to the shop yesterday.", "I didn't go to work on Monday."]),
    "future_forms": (
        "Plans already made: going to. Decisions made now: will.",
        ["I'm going to visit my family.", "I'll call you later."]),
    "questions": (
        "Questions need an auxiliary first: do / does / did + subject + base verb.",
        ["Where do you live?", "Did you see the message?"]),
    "word_order": (
        "Subject + verb + object, then place, then time.",
        ["I read a book at home every evening.",
         "She started her new job last week."]),
    "subject_verb_agreement": (
        "The verb follows the subject: he / she / it takes -s; people are.",
        ["My brother works at a bank.", "The people here are friendly."]),
    "articles": (
        "a / an = one of many (first mention). the = the one we both know. "
        "No article for general plurals.",
        ["I bought a phone. The phone is fast.", "I like books."]),
    "plurals_quantity": (
        "Countable: many / a few. Uncountable: much / a little. "
        "some in statements, any in questions and negatives.",
        ["I don't have much time.", "There are a few people outside."]),
    "prepositions": (
        "Time: at 7, on Monday, in June. Place: at the office, on the table, "
        "in the room.",
        ["I start work at nine on Monday.", "The keys are in the drawer."]),
    "pronouns_possessives": (
        "I / me, my / mine. Use 's for people: Taleh's car.",
        ["She gave me her number.", "That coffee is mine."]),
    "comparatives": (
        "Short words: -er than. Long words: more … than. Superlative takes the.",
        ["This phone is cheaper than that one.",
         "It is the most expensive option."]),
    "modals_basic": (
        "can / must / should + base verb - never with to.",
        ["You should sleep more.", "I can speak a little English."]),
    "linking_words": (
        "because = reason, so = result, but = contrast, then = next.",
        ["I was tired, so I went home.",
         "I wanted to go out, but it was raining."]),
    "word_choice": (
        "Pick the word that carries the meaning: make / do, say / tell, "
        "watch / look / see.",
        ["I made a decision.", "He told me the news."]),
    "present_perfect": (
        "have / has + past participle: experience, or the past still touching "
        "now. No finished time word.",
        ["I have been to Italy twice.", "She has just finished work."]),
    "perfect_vs_past": (
        "Finished time (yesterday, in 2020) → past simple. "
        "ever / already / yet / since → present perfect.",
        ["I saw him yesterday.", "I haven't seen him since Monday."]),
    "past_continuous": (
        "was / were + verb-ing for the background; past simple for the "
        "interruption.",
        ["I was walking home when it started to rain.",
         "They were sleeping when I called."]),
    "used_to": (
        "used to + base verb for past habits that stopped.",
        ["I used to play football every day.",
         "We used to live in a small village."]),
    "first_conditional": (
        "Real future: If + present simple, will + base verb.",
        ["If I have time, I will call you.",
         "If it rains, we will stay home."]),
    "modals_possibility": (
        "might / could = maybe. have to = obligation from outside.",
        ["It might rain later.", "I have to finish this today."]),
    "second_conditional": (
        "Imaginary: If + past simple, would + base verb.",
        ["If I had more money, I would travel.",
         "If I were you, I would take the job."]),
    "gerund_infinitive": (
        "Some verbs take -ing (enjoy, finish, avoid), some take to + verb "
        "(want, decide, need).",
        ["I enjoy learning languages.", "I want to improve my speaking."]),
    "phrasal_verbs": (
        "Verb + particle with its own meaning. Many split around an object: "
        "pick it up, not pick up it.",
        ["I gave up coffee.", "Can you pick me up at eight?"]),
    "relative_clauses": (
        "who = people, which / that = things, where = places.",
        ["The man who lives next door is a doctor.",
         "This is the book that I told you about."]),
    "passive_simple": (
        "be + past participle, when the action matters more than who did it.",
        ["Bread is made from flour.", "This house was built in 1980."]),
    "word_forms": (
        "One idea, several forms: happy (adj), happiness (noun), happily (adv).",
        ["She speaks English fluently.", "Her fluency is impressive."]),
    "past_perfect": (
        "had + past participle for the earlier of two past events.",
        ["When I arrived, the film had already started.",
         "They had finished before I got there."]),
    "third_conditional": (
        "The past that did not happen: If + had + participle, "
        "would have + participle.",
        ["If I had studied, I would have passed.",
         "If we had left earlier, we wouldn't have missed it."]),
    "wish_regret": (
        "wish + past simple for now; wish + had + participle for the past.",
        ["I wish I had more time.", "I wish I hadn't said that."]),
    "reported_speech": (
        "Report one tense back: am → was, will → would, went → had gone.",
        ["He said he was busy.", "She told me she would call later."]),
    "modals_deduction": (
        "must have = I'm sure. might have = maybe. can't have = impossible.",
        ["He must have forgotten.", "She might have missed the bus."]),
    "passive_advanced": (
        "Impersonal and formal: It is said that…, has been done, will be done.",
        ["It is said that prices will rise.",
         "The decision has already been made."]),
    "future_advanced": (
        "will be + -ing for an action in progress; will have + participle for "
        "something finished by then.",
        ["This time next year I'll be working abroad.",
         "By June I'll have finished the course."]),
    "discourse_markers": (
        "Signposts for the listener: however, on the other hand, as a result, "
        "in fact.",
        ["However, there is one problem.",
         "As a result, many people left."]),
    "collocations": (
        "Words travel in pairs: make a decision, do homework, heavy rain, "
        "take a risk.",
        ["I need to make a decision this week.",
         "We had heavy rain all night."]),
}


# ── On the board ─────────────────────────────────────────────────────────────
# What the tutor draws when it explains a skill: the form as a formula, and a
# picture of what it means. The pictures are specs, drawn by the page
# (web/static/diagrams.js):
#   timeline  PAST - NOW - FUTURE with points, ranges, repeats and arrows (x: -1..1)
#   flow      boxes joined by arrows ("if + past" → "would + verb")
#   ladder    steps rising left to right (big → bigger → the biggest)
#   nest      rings from big to small (in → on → at)
#   split     two columns side by side, for two forms that get mixed up
#   blocks    the slots of a sentence, in order
#   shift     pairs that change, e.g. reported speech backshift

SKILL_BOARD: dict[str, dict] = {
    "present_simple": {"formula": ["I / you / we / they + verb", "he / she / it + verb-s",
                                   "don't / doesn't + verb"],
                       "diagram": {"kind": "timeline", "items": [
                           {"type": "repeat", "from": -0.9, "to": 0.9, "n": 7, "label": "every day"}]}},
    "present_continuous": {"formula": ["am / is / are + verb-ing"],
                           "diagram": {"kind": "timeline", "items": [
                               {"type": "range", "from": -0.18, "to": 0.18, "label": "right now"}]}},
    "past_simple": {"formula": ["verb-ed / irregular (went, saw)", "didn't + verb",
                                "Did + subject + verb?"],
                    "diagram": {"kind": "timeline", "items": [
                        {"type": "point", "at": -0.55, "label": "yesterday - finished"}]}},
    "future_forms": {"formula": ["am / is / are going to + verb  (a plan)",
                                 "will + verb  (decided now)"],
                     "diagram": {"kind": "timeline", "items": [
                         {"type": "arrow", "from": 0, "to": 0.6, "label": "going to"},
                         {"type": "point", "at": 0.6, "label": "tomorrow"}]}},
    "questions": {"formula": ["(Wh-) + do / does / did + subject + verb?"],
                  "diagram": {"kind": "blocks", "items": ["Where", "do", "you", "live", "?"]}},
    "word_order": {"formula": ["subject + verb + object + place + time"],
                   "diagram": {"kind": "blocks", "items": ["I", "met", "my friend", "in the park",
                                                           "yesterday"]}},
    "subject_verb_agreement": {"formula": ["he / she / it works · they work", "a person is · people are"],
                               "diagram": {"kind": "split", "left": {"title": "one", "lines": ["she works", "it is", "a person is"]},
                                           "right": {"title": "many", "lines": ["they work", "we are", "people are"]}}},
    "articles": {"formula": ["a / an = one of many, new", "the = the one we both know"],
                 "diagram": {"kind": "split", "left": {"title": "a / an - new", "lines": ["I saw a dog.", "an apple"]},
                             "right": {"title": "the - known", "lines": ["The dog was big.", "the sun"]}}},
    "plurals_quantity": {"formula": ["many + countable (many books)", "much + uncountable (much water)",
                                     "a lot of + both"],
                         "diagram": {"kind": "split", "left": {"title": "countable", "lines": ["many books", "a few friends"]},
                                     "right": {"title": "uncountable", "lines": ["much water", "a little time"]}}},
    "prepositions": {"formula": ["in - big (years, months, cities)", "on - days, surfaces",
                                 "at - exact (times, points)"],
                     "diagram": {"kind": "nest", "items": [["in", "2026 · May · Baku"], ["on", "Monday · 5 May"],
                                                           ["at", "5 o'clock · the door"]]}},
    "pronouns_possessives": {"formula": ["I → me → my → mine", "Taleh's car"],
                             "diagram": {"kind": "blocks", "items": ["I", "me", "my", "mine"]}},
    "comparatives": {"formula": ["short: big → bigger → the biggest",
                                 "long: expensive → more expensive → the most expensive"],
                     "diagram": {"kind": "ladder", "items": ["big", "bigger", "the biggest"]}},
    "modals_basic": {"formula": ["can / must / should + verb  (no 'to')"],
                     "diagram": {"kind": "blocks", "items": ["You", "should", "rest", "(no to!)"]}},
    "linking_words": {"formula": ["and (add) · but (contrast) · because (reason) · so (result)"],
                      "diagram": {"kind": "flow", "items": ["I was tired", "so", "I went to bed"]}},
    "word_choice": {"formula": ["the word that carries the meaning", "make / do · say / tell · watch / look / see"],
                    "diagram": {"kind": "split", "left": {"title": "make", "lines": ["a decision", "a mistake"]},
                                "right": {"title": "do", "lines": ["homework", "the shopping"]}}},
    "present_perfect": {"formula": ["have / has + V3 (been, done, seen)"],
                        "diagram": {"kind": "timeline", "items": [
                            {"type": "arrow", "from": -0.7, "to": 0, "label": "from then until now"}]}},
    "perfect_vs_past": {"formula": ["yesterday / in 2020 → past simple", "ever / already / yet / since → present perfect"],
                        "diagram": {"kind": "split", "left": {"title": "past simple", "lines": ["I saw it yesterday.", "finished time"]},
                                    "right": {"title": "present perfect", "lines": ["I have seen it.", "no time - result now"]}}},
    "past_continuous": {"formula": ["was / were + verb-ing", "…when + past simple"],
                        "diagram": {"kind": "timeline", "items": [
                            {"type": "range", "from": -0.85, "to": -0.3, "label": "I was walking"},
                            {"type": "point", "at": -0.55, "label": "it started to rain"}]}},
    "used_to": {"formula": ["used to + verb  (not any more)"],
                "diagram": {"kind": "timeline", "items": [
                    {"type": "repeat", "from": -0.9, "to": -0.25, "n": 5, "label": "I used to play"},
                    {"type": "cross", "at": 0, "label": "not now"}]}},
    "first_conditional": {"formula": ["If + present, will + verb"],
                          "diagram": {"kind": "flow", "items": ["If it rains", "→", "I will stay home"]}},
    "modals_possibility": {"formula": ["might / could + verb  (maybe)", "have to + verb  (necessary)"],
                           "diagram": {"kind": "ladder", "items": ["might", "could", "will", "must"]}},
    "second_conditional": {"formula": ["If + past simple, would + verb  (imagined, now)"],
                           "diagram": {"kind": "flow", "items": ["If I had money", "→", "I would travel"]}},
    "gerund_infinitive": {"formula": ["enjoy / finish / stop + verb-ing", "want / decide / hope + to + verb"],
                          "diagram": {"kind": "split", "left": {"title": "+ -ing", "lines": ["I enjoy cooking.", "stop smoking"]},
                                      "right": {"title": "+ to", "lines": ["I want to cook.", "decide to go"]}}},
    "phrasal_verbs": {"formula": ["verb + particle = new meaning", "look for · find out · give up"],
                      "diagram": {"kind": "blocks", "items": ["give", "+", "up", "=", "stop trying"]}},
    "relative_clauses": {"formula": ["who (people) · which / that (things) · where (places)"],
                         "diagram": {"kind": "blocks", "items": ["the man", "who", "lives next door"]}},
    "passive_simple": {"formula": ["be + V3 (+ by …)", "It is made in… · It was built in…"],
                       "diagram": {"kind": "flow", "items": ["They built it", "→", "It was built"]}},
    "word_forms": {"formula": ["noun · adjective · adverb", "happiness · happy · happily"],
                   "diagram": {"kind": "blocks", "items": ["happiness (n)", "happy (adj)", "happily (adv)"]}},
    "past_perfect": {"formula": ["had + V3 - the EARLIER past"],
                     "diagram": {"kind": "timeline", "items": [
                         {"type": "point", "at": -0.75, "label": "he had left"},
                         {"type": "point", "at": -0.3, "label": "I arrived"}]}},
    "third_conditional": {"formula": ["If + had + V3, would have + V3  (imagined past)"],
                          "diagram": {"kind": "flow", "items": ["If I had known", "→", "I would have come"]}},
    "wish_regret": {"formula": ["wish + past  (now)", "wish + had + V3  (the past)"],
                    "diagram": {"kind": "split", "left": {"title": "now", "lines": ["I wish I had time."]},
                                "right": {"title": "past", "lines": ["I wish I had studied."]}}},
    "reported_speech": {"formula": ["said (that) + one tense back"],
                        "diagram": {"kind": "shift", "items": [["am", "was"], ["will", "would"],
                                                               ["can", "could"], ["went", "had gone"]]}},
    "modals_deduction": {"formula": ["must / might / can't + have + V3"],
                         "diagram": {"kind": "ladder", "items": ["can't have", "might have", "must have"]}},
    "passive_advanced": {"formula": ["has been + V3 · will be + V3", "It is said that…"],
                         "diagram": {"kind": "flow", "items": ["They have done it", "→", "It has been done"]}},
    "future_advanced": {"formula": ["will be + verb-ing  (in progress then)", "will have + V3  (finished by then)"],
                        "diagram": {"kind": "timeline", "items": [
                            {"type": "range", "from": 0.3, "to": 0.65, "label": "I'll be working"},
                            {"type": "point", "at": 0.85, "label": "I'll have finished"}]}},
    "discourse_markers": {"formula": ["however (contrast) · as a result (result)", "in fact (stronger) · on the other hand"],
                          "diagram": {"kind": "flow", "items": ["It was cheap", "however,", "it broke"]}},
    "collocations": {"formula": ["words that go together", "make a decision · heavy rain · take a risk"],
                     "diagram": {"kind": "split", "left": {"title": "yes", "lines": ["heavy traffic", "make a decision"]},
                                 "right": {"title": "no", "lines": ["big traffic", "do a decision"]}}},
}


def board_card(sid: str, skills: dict) -> dict:
    """Everything the board shows when the tutor explains one skill."""
    tip = skill_tip(sid, skills)
    board = SKILL_BOARD.get(sid, {})
    name, band, hint = skills.get(sid, (sid, "", ""))
    # The board is kept simple: one easy sentence, the form in at most two
    # lines, the picture, two examples.
    return {"skill": sid, "title": name, "band": band, "hint": hint,
            "rule": simple_rule(sid), "examples": tip.get("examples", [])[:2],
            "formula": board.get("formula", [])[:2], "diagram": board.get("diagram")}


def skill_tip(sid: str, skills: dict) -> dict:
    """{title, rule, examples} for the tip card - empty title if unknown."""
    rule, examples = SKILL_TIPS.get(sid, ("", []))
    name = skills.get(sid, (sid,))[0] if skills else sid
    return {"id": sid, "title": name, "rule": rule, "examples": list(examples)}


# ── How it is taught ─────────────────────────────────────────────────────────
# The sentences in a unit are what to practise; these are HOW. Each one is a
# real technique from language teaching, written as an instruction the tutor can
# run out loud with no materials, no screen and no preparation.
#
# id -> {"name": short name, "goal": why it works, "how": the steps}

METHODS: dict[str, dict] = {
    "ppp": {
        "name": "Present, practise, produce",
        "goal": "meet a new structure and get it into your own mouth",
        "how": ("Explain the form in ONE simple sentence with one example. Then "
                "five guided prompts where the answer must use it. Then let the "
                "learner use it freely in conversation. Never explain twice."),
    },
    "substitution": {
        "name": "Substitution drill",
        "goal": "make the form automatic, so it needs no thinking",
        "how": ("Give one sentence, then change a single word each turn ('I went "
                "to the shop' → park → school → work). Fast, 6-8 turns, no "
                "grammar talk. Speed matters more than variety."),
    },
    "transformation": {
        "name": "Transformation drill",
        "goal": "connect two forms so you can switch between them",
        "how": ("You say a sentence, the learner turns it into the target form: "
                "statement → question, present → past, active → passive. Six "
                "items, quick, correct on the spot with a recast."),
    },
    "minimal_contrast": {
        "name": "Form contrast",
        "goal": "stop two forms blurring into one",
        "how": ("Work in pairs ('I work' / 'I am working'). You describe a "
                "situation, the learner says which one fits and why in three "
                "words. Ten situations, mixed order."),
    },
    "recast_repeat": {
        "name": "Recast and repeat",
        "goal": "fix a mistake without breaking the conversation",
        "how": ("Say the corrected sentence once, have the learner repeat it "
                "once, then continue the topic immediately. No rule, no lecture."),
    },
    "elicit_self_repair": {
        "name": "Clarification request",
        "goal": "notice your own mistakes - the strongest kind of correction",
        "how": ("Instead of correcting, repeat their words back with a "
                "questioning tone, or ask 'again?'. Give them ONE chance to "
                "repair it themselves; correct only if they cannot."),
    },
    "retell": {
        "name": "Retelling",
        "goal": "turn what you heard into what you can say",
        "how": ("You tell a four-sentence story (or they tell theirs). Then they "
                "retell it from memory in their own words. Compare: what was "
                "missing, what was wrong."),
    },
    "four_three_two": {
        "name": "4/3/2 fluency",
        "goal": "speak faster and stop searching for words",
        "how": ("The learner tells the SAME story three times: two minutes, then "
                "ninety seconds, then sixty. You do not interrupt at all. All "
                "feedback comes after the third telling."),
    },
    "dictogloss": {
        "name": "Dictogloss",
        "goal": "hear the grammar in real speech, then rebuild it",
        "how": ("Say a short three-sentence text twice at their level. The "
                "learner rebuilds it aloud as closely as they can. Then fix ONE "
                "difference that matters."),
    },
    "information_gap": {
        "name": "Information gap",
        "goal": "real communication: you have to ask to find out",
        "how": ("You hold information the learner needs (two flats, two phones, "
                "two job offers). They must ask questions to choose. They talk, "
                "you only answer what they asked."),
    },
    "role_play": {
        "name": "Role play",
        "goal": "use the language where you will actually need it",
        "how": ("Set the place and the two roles (shop, doctor, interview, "
                "airport). Stay in character to the end, however many mistakes "
                "there are, then give two corrections."),
    },
    "shadowing": {
        "name": "Shadowing",
        "goal": "rhythm, stress and linking - sounding like a speaker",
        "how": ("Say a sentence at natural speed. The learner repeats it copying "
                "your rhythm, not just the words. Five short sentences, twice "
                "each."),
    },
    "personalise": {
        "name": "Personalisation",
        "goal": "language about your own life is the language you remember",
        "how": ("Rebuild every example with their real details - their job, "
                "their city, their family, what they did yesterday. Never drill "
                "a sentence about a stranger."),
    },
    "pushed_output": {
        "name": "Pushed output",
        "goal": "you only own a structure once you have produced it yourself",
        "how": ("Ask questions that cannot be answered without the target form, "
                "and count: the learner must produce it five times before the "
                "topic moves on."),
    },
    "collocation_push": {
        "name": "Chunk push",
        "goal": "sound natural by learning words in pairs, not alone",
        "how": ("Give three chunks ('make a decision', 'heavy rain', 'keep in "
                "touch'). Then require all three inside the next two minutes of "
                "conversation."),
    },
    "backchaining": {
        "name": "Backchaining",
        "goal": "say long sentences without falling apart in the middle",
        "how": ("Build a long sentence from the END backwards: '…in the morning' "
                "→ 'to work in the morning' → 'I usually go to work in the "
                "morning'. The learner repeats each piece."),
    },
    "l1_contrast": {
        "name": "Native-language contrast",
        "goal": "kill the mistakes that come from your own language",
        "how": ("For a mistake caused by their native word order or a false "
                "friend, show the two orders side by side ONCE, then three quick "
                "translations from their language. Then back to English only."),
    },
    "spaced_review": {
        "name": "Spaced review",
        "goal": "you forget on a curve; reviewing on the same curve beats it",
        "how": ("Open every lesson with three quick prompts on skills that are "
                "due for review - not on what was taught last, on what is about "
                "to be forgotten."),
    },
    "self_assess": {
        "name": "Can-do check",
        "goal": "prove the unit is finished instead of assuming it",
        "how": ("At the end of a unit the learner performs its can-do statement "
                "in one go, with no help and no corrections. Then you say what "
                "passed and what still wobbles."),
    },
}

# Run in every lesson, whatever the unit is.
STANDING_METHODS = ("spaced_review", "recast_repeat", "personalise", "self_assess")

# What each stage is mainly training. Accuracy first, then fluency, then
# precision: pushing for natural speed before the basic forms exist only
# produces confident mistakes.
STAGE_EMPHASIS = {
    "A2.1": "accuracy - the basic forms, said correctly and slowly",
    "A2.2": "accuracy and range - more to say, still simple",
    "B1.1": "fluency - keep talking, longer turns, fewer pauses",
    "B1.2": "complexity - two-clause sentences, opinions with reasons",
    "B2.1": "precision - the right tense and the right word",
    "B2.2": "naturalness - chunks, rhythm, argument",
}

# Which techniques each unit is practised with.
UNIT_METHODS = {
    "en-01": ["ppp", "personalise", "pushed_output"],
    "en-02": ["minimal_contrast", "substitution", "pushed_output"],
    "en-03": ["retell", "four_three_two", "personalise"],
    "en-04": ["l1_contrast", "substitution", "information_gap"],
    "en-05": ["ppp", "role_play", "personalise"],
    "en-06": ["information_gap", "transformation", "pushed_output"],
    "en-07": ["role_play", "transformation", "personalise"],
    "en-08": ["retell", "dictogloss", "four_three_two"],
    "en-09": ["pushed_output", "information_gap", "ppp"],
    "en-10": ["dictogloss", "retell", "personalise"],
    "en-11": ["minimal_contrast", "transformation", "elicit_self_repair"],
    "en-12": ["ppp", "role_play", "pushed_output"],
    "en-13": ["pushed_output", "personalise", "four_three_two"],
    "en-14": ["substitution", "collocation_push", "personalise"],
    "en-15": ["information_gap", "backchaining", "pushed_output"],
    "en-16": ["transformation", "dictogloss", "retell"],
    "en-17": ["retell", "backchaining", "dictogloss"],
    "en-18": ["pushed_output", "personalise", "elicit_self_repair"],
    "en-19": ["transformation", "role_play", "retell"],
    "en-20": ["information_gap", "pushed_output", "elicit_self_repair"],
    "en-21": ["dictogloss", "transformation", "shadowing"],
    "en-22": ["personalise", "pushed_output", "four_three_two"],
    "en-23": ["role_play", "collocation_push", "four_three_two"],
    "en-24": ["collocation_push", "shadowing", "four_three_two"],
}

# Every unit carries its own techniques, so a unit is self-describing wherever
# it travels - the prompt, the syllabus panel, the progress file.
for _stage in ENGLISH_STAGES:
    for _unit in _stage["units"]:
        _unit["methods"] = list(UNIT_METHODS.get(_unit["id"], ("ppp", "pushed_output")))


def method(mid: str) -> dict:
    return METHODS.get(mid, {"name": mid, "goal": "", "how": ""})


def methods_of(unit: dict) -> list[dict]:
    """[{id, name, goal, how}] for a unit, in the order they should be used."""
    out = []
    for mid in unit.get("methods", []):
        m = method(mid)
        out.append({"id": mid, "name": m["name"], "goal": m["goal"], "how": m["how"]})
    return out


# Free-text grammar topics written by the old english_coach, mapped onto skill
# ids so a learner's history is not thrown away when the course starts.
LEGACY_TOPIC_MAP: dict[str, str] = {
    "word order": "word_order", "adverb placement": "word_order",
    "prepositions": "prepositions", "prepositions of time": "prepositions",
    "prepositions of movement": "prepositions", "time expressions": "prepositions",
    "dependent prepositions": "dependent_prepositions",
    "verb + preposition": "dependent_prepositions",
    "articles": "articles",
    "collocations": "collocations", "lexical chunks": "collocations",
    "fixed expressions": "collocations",
    "subject-verb agreement": "subject_verb_agreement",
    "question formation": "questions", "direct questions": "questions",
    "auxiliary verbs": "questions",
    "modal verbs": "modals_basic",
    "plurals": "plurals_quantity", "countable nouns": "plurals_quantity",
    "countable and uncountable nouns": "plurals_quantity",
    "quantifiers": "plurals_quantity", "determiners": "plurals_quantity",
    "verb patterns": "gerund_infinitive", "infinitives": "gerund_infinitive",
    "gerunds": "gerund_infinitive", "gerunds and infinitives": "gerund_infinitive",
    "infinitive of purpose": "gerund_infinitive",
    "verb complementation": "gerund_infinitive",
    "present continuous": "present_continuous", "past simple": "past_simple",
    "past continuous": "past_continuous", "relative clauses": "relative_clauses",
    "phrasal verbs": "phrasal_verbs", "passive voice": "passive_simple",
    "possessive nouns": "pronouns_possessives",
    "pronoun agreement": "pronouns_possessives",
    "indefinite pronouns": "pronouns_possessives",
    "word forms": "word_forms", "parts of speech": "word_forms",
    "adjectives": "word_forms", "adverbs": "word_forms",
    "compound adjectives": "word_forms", "compound nouns": "word_forms",
    "nouns": "word_forms",
    "verb choice": "word_choice", "lexical choice": "word_choice",
    "vocabulary": "word_choice", "redundancy": "word_choice",
    "verb omission": "word_order", "conjunctions": "linking_words",
}


LANGUAGES: dict[str, dict] = {
    "english": {
        "name": "English",
        "enabled": True,
        "data_dir": "english",
        "skills": ENGLISH_SKILLS,
        "stages": ENGLISH_STAGES,
    },
    # Declared so the mode exists; switched on once its course is written.
    "slovak": {
        "name": "Slovak",
        "enabled": False,
        "data_dir": "slovak",
        "skills": {},
        "stages": [],
    },
}

DEFAULT_LANGUAGE = "english"


def language(key: str) -> dict:
    return LANGUAGES.get(key) or LANGUAGES[DEFAULT_LANGUAGE]


def all_units(lang: dict) -> list[tuple[int, int, dict, dict]]:
    """Every unit in course order: (stage_index, unit_index, stage, unit)."""
    out = []
    for si, stage in enumerate(lang["stages"]):
        for ui, unit in enumerate(stage["units"]):
            out.append((si, ui, stage, unit))
    return out


def unit_number(lang: dict, stage_index: int, unit_index: int) -> int:
    """1-based position of a unit in the whole course."""
    n = 0
    for si, stage in enumerate(lang["stages"]):
        for ui, _ in enumerate(stage["units"]):
            n += 1
            if si == stage_index and ui == unit_index:
                return n
    return n


def total_units(lang: dict) -> int:
    return sum(len(s["units"]) for s in lang["stages"])


def band_index(band: str) -> int:
    return BAND_ORDER.index(band) if band in BAND_ORDER else 1


def skills_up_to(lang: dict, stage_index: int) -> list[str]:
    """Skills taught in every unit up to and including this stage - the ones a
    learner here is expected to get right, and so the ones worth focusing on."""
    seen: list[str] = []
    for si, stage in enumerate(lang["stages"]):
        if si > stage_index:
            break
        for unit in stage["units"]:
            for sk in unit["skills"]:
                if sk not in seen:
                    seen.append(sk)
    return seen


# ── The full grammar syllabus ────────────────────────────────────────────────
# The skills above were the course's. These complete the list of the grammar a
# speaker meets from A1 to B2, so that ANY rule the learner brings up - modal
# verbs today, the possessive 's tomorrow - is on the syllabus, measured from
# their own speech and explained on the board. Each entry: (name, band, hint),
# its rule and examples, and what the board draws.

_MORE_SKILLS: dict[str, tuple[str, str, str, str, list[str], dict]] = {
    # ── A1 ──
    "be_verb": ("to be (am / is / are)", "A1", "I am, she is, they are; isn't, aren't",
                "Use am with I, is with he / she / it, are with you / we / they.",
                ["I am from Baku.", "They aren't at home."],
                {"formula": ["I am · he / she / it is · you / we / they are", "not: am not · isn't · aren't"],
                 "diagram": {"kind": "split", "left": {"title": "one", "lines": ["I am", "she is", "it is"]},
                             "right": {"title": "many", "lines": ["we are", "you are", "they are"]}}}),
    "have_got": ("have / has got", "A1", "I have got a car; she has got two brothers",
                 "Have got = have (own). he / she / it has got.",
                 ["I've got a new phone.", "She hasn't got a car."],
                 {"formula": ["I / you / we / they have got", "he / she / it has got"],
                  "diagram": {"kind": "blocks", "items": ["She", "has got", "two brothers"]}}),
    "there_is_are": ("there is / there are", "A1", "there is a bank; there are two shops",
                     "There is + one thing, there are + many things - to say something exists.",
                     ["There is a park near my house.", "There are three people in my team."],
                     {"formula": ["there is + a / an + one", "there are + many"],
                      "diagram": {"kind": "split", "left": {"title": "there is", "lines": ["a bank", "some water"]},
                                  "right": {"title": "there are", "lines": ["two shops", "many cars"]}}}),
    "imperatives": ("imperatives", "A1", "Sit down. Don't go. Let's start.",
                    "Give an order or advice with the bare verb; don't + verb to stop someone.",
                    ["Open the window, please.", "Don't worry."],
                    {"formula": ["verb …!  ·  Don't + verb …!", "Let's + verb (us)"],
                     "diagram": {"kind": "blocks", "items": ["Don't", "forget", "your keys"]}}),
    "this_that": ("this / that / these / those", "A1", "this = near, that = far; these / those for many",
                  "this / these for things near you, that / those for things far away.",
                  ["This coffee is hot.", "Those people are my friends."],
                  {"formula": ["near: this (one) · these (many)", "far: that (one) · those (many)"],
                   "diagram": {"kind": "split", "left": {"title": "near", "lines": ["this book", "these books"]},
                               "right": {"title": "far", "lines": ["that book", "those books"]}}}),
    "can_ability": ("can / can't (ability)", "A1", "I can swim; can you drive?",
                    "can + verb (no to, no -s) for what you are able to do.",
                    ["I can speak three languages.", "Can you cook?"],
                    {"formula": ["can / can't + verb", "Can + subject + verb?"],
                     "diagram": {"kind": "blocks", "items": ["She", "can", "swim", "(no -s!)"]}}),
    "possessive_case": ("possessive 's", "A1", "Taleh's car, my parents' house",
                        "Add 's to show who owns something; after a plural -s, just add '.",
                        ["This is my brother's room.", "My parents' house is big."],
                        {"formula": ["one: name + 's (Taleh's car)", "plural -s: + ' (my parents' house)"],
                         "diagram": {"kind": "flow", "items": ["the car of Taleh", "→", "Taleh's car"]}}),
    "adverbs_frequency": ("adverbs of frequency", "A1", "always, usually, sometimes, never - before the main verb",
                          "always / usually / often / sometimes / never go before the main verb, after be.",
                          ["I usually get up at seven.", "She is never late."],
                          {"formula": ["subject + always / usually / never + verb", "be + always / never"],
                           "diagram": {"kind": "ladder", "items": ["never", "sometimes", "often", "usually", "always"]}}),
    "question_words": ("question words", "A1", "what, where, when, who, why, how, which, whose",
                       "Start a question with the word for what you want to know.",
                       ["Where do you work?", "Why are you tired?"],
                       {"formula": ["what (thing) · where (place) · when (time)", "who (person) · why (reason) · how (way)"],
                        "diagram": {"kind": "blocks", "items": ["Where", "do", "you", "work", "?"]}}),
    "like_ing": ("like / love / hate + -ing", "A1", "I like reading; she hates cooking",
                 "After like, love, hate, enjoy use verb-ing.",
                 ["I love swimming.", "He doesn't like waiting."],
                 {"formula": ["like / love / hate / enjoy + verb-ing"],
                  "diagram": {"kind": "blocks", "items": ["I", "enjoy", "reading", "(-ing)"]}}),
    # ── A2 ──
    # Not in / on / at: the small word that belongs to a verb or an adjective.
    # Without its own rule these mistakes got the in / on / at board.
    "dependent_prepositions": ("word + preposition (share with, listen to)", "A2",
                               "a verb or adjective takes its own preposition: share with, listen to, good at",
                               "Some words always take the same small word after them. Learn them together: "
                               "share with, listen to, wait for, good at.",
                               ["I want to share this with you.", "She is good at maths."],
                               {"formula": ["verb + its word: share with · listen to · wait for · depend on",
                                            "adjective + its word: good at · interested in · afraid of"],
                                "diagram": {"kind": "split",
                                            "left": {"title": "verb +", "lines": ["share with", "listen to", "wait for"]},
                                            "right": {"title": "adjective +", "lines": ["good at", "interested in", "afraid of"]}}}),
    "past_be": ("was / were", "A2", "I was tired; they were at home",
                "The past of be: was with I / he / she / it, were with you / we / they.",
                ["I was at work yesterday.", "Were you happy?"],
                {"formula": ["I / he / she / it was", "you / we / they were"],
                 "diagram": {"kind": "timeline", "items": [{"type": "point", "at": -0.5, "label": "I was tired"}]}}),
    "present_continuous_future": ("present continuous for plans", "A2", "I'm meeting him tomorrow",
                                  "Use am / is / are + -ing for a plan already arranged.",
                                  ["I'm flying to Istanbul on Friday.", "What are you doing tonight?"],
                                  {"formula": ["am / is / are + verb-ing + future time"],
                                   "diagram": {"kind": "timeline", "items": [
                                       {"type": "point", "at": 0.55, "label": "meeting him - arranged"}]}}),
    "would_like": ("would like", "A2", "I'd like a coffee; would you like to come?",
                   "would like = want, but polite. would like + noun / to + verb.",
                   ["I'd like a glass of water.", "Would you like to join us?"],
                   {"formula": ["would like + noun", "would like + to + verb"],
                    "diagram": {"kind": "flow", "items": ["I want a coffee", "→", "I'd like a coffee"]}}),
    "have_to": ("have to / don't have to", "A2", "I have to work; you don't have to come",
                "have to = it is necessary; don't have to = it is not necessary (you can choose).",
                ["I have to finish this today.", "You don't have to pay."],
                {"formula": ["have / has to + verb", "don't / doesn't have to + verb"],
                 "diagram": {"kind": "split", "left": {"title": "have to", "lines": ["necessary", "I have to go."]},
                             "right": {"title": "don't have to", "lines": ["not necessary", "You don't have to."]}}}),
    "too_enough": ("too / enough", "A2", "too hot; not old enough; enough money",
                   "too + adjective = more than OK; adjective + enough / enough + noun = as much as needed.",
                   ["It's too expensive.", "I don't have enough time."],
                   {"formula": ["too + adjective", "adjective + enough · enough + noun"],
                    "diagram": {"kind": "ladder", "items": ["not enough", "enough", "too much"]}}),
    "adverbs_manner": ("adverbs of manner", "A2", "quickly, carefully, well - how you do it",
                       "Most adverbs are adjective + -ly; good → well, fast → fast.",
                       ["She speaks English well.", "Drive carefully."],
                       {"formula": ["adjective + -ly (quick → quickly)", "good → well · fast → fast · hard → hard"],
                        "diagram": {"kind": "flow", "items": ["a careful driver", "→", "drives carefully"]}}),
    "could_past": ("could (past ability)", "A2", "I could swim when I was five",
                   "could / couldn't + verb = was able / wasn't able in the past.",
                   ["I could read when I was four.", "We couldn't find the hotel."],
                   {"formula": ["could / couldn't + verb (past)"],
                    "diagram": {"kind": "timeline", "items": [
                        {"type": "range", "from": -0.9, "to": -0.35, "label": "I could swim"}]}}),
    "some_any_compounds": ("something / anybody / nowhere", "A2", "something, anyone, nothing, everywhere",
                           "some- in positive sentences, any- in questions and negatives, no- = not any.",
                           ["I want something to eat.", "Is anybody home?"],
                           {"formula": ["some- (+) · any- (? / -) · no- (= not any)", "-thing · -body / -one · -where"],
                            "diagram": {"kind": "split", "left": {"title": "some-", "lines": ["something", "somebody"]},
                                        "right": {"title": "any- / no-", "lines": ["anything?", "nobody"]}}}),
    # ── B1 ──
    "present_perfect_continuous": ("present perfect continuous", "B1", "I have been working here for two years",
                                   "have / has been + -ing for an action that started in the past and is still going.",
                                   ["I've been learning English for a year.", "How long have you been waiting?"],
                                   {"formula": ["have / has been + verb-ing", "for + a period · since + a start"],
                                    "diagram": {"kind": "timeline", "items": [
                                        {"type": "range", "from": -0.75, "to": 0.02, "label": "been working - still"}]}}),
    "zero_conditional": ("zero conditional", "B1", "If you heat ice, it melts",
                         "If + present, present - for things that are always true.",
                         ["If I drink coffee late, I can't sleep.", "If you press this, it stops."],
                         {"formula": ["If + present, present  (always true)"],
                          "diagram": {"kind": "flow", "items": ["If you heat ice", "→", "it melts"]}}),
    "question_tags": ("question tags", "B1", "It's cold, isn't it? You don't smoke, do you?",
                      "Positive sentence → negative tag; negative sentence → positive tag, same auxiliary.",
                      ["You're a teacher, aren't you?", "She didn't call, did she?"],
                      {"formula": ["positive …, negative tag?", "negative …, positive tag?"],
                       "diagram": {"kind": "blocks", "items": ["It's cold,", "isn't", "it?"]}}),
    "reflexive_pronouns": ("reflexive pronouns", "B1", "myself, yourself, themselves",
                           "Use -self / -selves when the subject and object are the same person.",
                           ["I cut myself.", "They enjoyed themselves."],
                           {"formula": ["myself · yourself · himself · herself", "ourselves · yourselves · themselves"],
                            "diagram": {"kind": "flow", "items": ["I hurt", "→", "myself"]}}),
    "so_such": ("so / such", "B1", "so tired; such a long day",
                "so + adjective, such (a) + adjective + noun - to make it stronger.",
                ["I was so tired.", "It was such a nice day."],
                {"formula": ["so + adjective", "such (a / an) + adjective + noun"],
                 "diagram": {"kind": "split", "left": {"title": "so", "lines": ["so tired", "so fast"]},
                             "right": {"title": "such", "lines": ["such a long day", "such good food"]}}}),
    "indirect_questions": ("indirect questions", "B1", "Can you tell me where the station is?",
                           "After 'Can you tell me / Do you know', use normal word order: subject + verb.",
                           ["Do you know what time it is?", "Can you tell me where he lives?"],
                           {"formula": ["Can you tell me / Do you know + wh- + subject + verb?"],
                            "diagram": {"kind": "flow", "items": ["Where is the station?", "→", "…where the station is?"]}}),
    "both_either_neither": ("both / either / neither", "B1", "both of them; either one; neither of us",
                            "both = the two; either = one of the two; neither = not one and not the other.",
                            ["Both options are good.", "Neither of us was ready."],
                            {"formula": ["both (+ and) · either (+ or) · neither (+ nor)"],
                             "diagram": {"kind": "blocks", "items": ["both = 2", "either = 1 of 2", "neither = 0"]}}),
    "advice_modals": ("should / ought to / had better", "B1", "you should rest; you'd better go",
                      "should / ought to = good idea; had better = strong advice (or there is a problem).",
                      ["You should see a doctor.", "We'd better leave now."],
                      {"formula": ["should / ought to + verb", "had better ('d better) + verb"],
                       "diagram": {"kind": "ladder", "items": ["could", "should", "had better"]}}),
    # ── B2 ──
    "past_perfect_continuous": ("past perfect continuous", "B2", "I had been waiting for an hour when he came",
                                "had been + -ing for an action going on BEFORE another past moment.",
                                ["She had been working all day, so she was tired.", "We had been driving for hours."],
                                {"formula": ["had been + verb-ing"],
                                 "diagram": {"kind": "timeline", "items": [
                                     {"type": "range", "from": -0.9, "to": -0.4, "label": "had been waiting"},
                                     {"type": "point", "at": -0.4, "label": "he came"}]}}),
    "mixed_conditionals": ("mixed conditionals", "B2", "If I had studied, I would be a doctor now",
                           "Past condition → present result, or present condition → past result.",
                           ["If I had taken that job, I would live in London now.",
                            "If I were braver, I would have said something."],
                           {"formula": ["If + had + V3, would + verb (now)", "If + past, would have + V3"],
                            "diagram": {"kind": "flow", "items": ["If I had studied (past)", "→", "I would be… (now)"]}}),
    "causative": ("have / get something done", "B2", "I had my car repaired",
                  "have / get + object + V3 when someone else does it for you.",
                  ["I had my hair cut yesterday.", "We're getting the kitchen painted."],
                  {"formula": ["have / get + object + V3"],
                   "diagram": {"kind": "flow", "items": ["The mechanic repaired my car", "→", "I had my car repaired"]}}),
    "non_defining_relative": ("non-defining relative clauses", "B2", "My brother, who lives in Baku, is a doctor",
                              "Extra information between commas: who / which (never that).",
                              ["My phone, which I bought last year, is broken.", "Aysel, who works with me, is from Ganja."],
                              {"formula": ["noun, who / which + extra information,"],
                               "diagram": {"kind": "blocks", "items": ["My brother,", "who lives in Baku,", "is a doctor"]}}),
    "participle_clauses": ("participle clauses", "B2", "Feeling tired, I went home",
                           "Start with -ing (active) or V3 (passive) to join two actions with the same subject.",
                           ["Walking home, I met an old friend.", "Built in 1900, the house is very old."],
                           {"formula": ["Verb-ing …, subject + verb", "V3 …, subject + verb"],
                            "diagram": {"kind": "flow", "items": ["I felt tired, so I went home", "→", "Feeling tired, I went home"]}}),
    "be_used_to": ("be / get used to + -ing", "B2", "I'm used to getting up early",
                   "be used to = it is normal for me; get used to = it is becoming normal. + noun / -ing.",
                   ["I'm used to working at night.", "You'll get used to the weather."],
                   {"formula": ["be / get used to + noun / verb-ing", "≠ used to + verb (past habit)"],
                    "diagram": {"kind": "split", "left": {"title": "used to + verb", "lines": ["I used to smoke.", "past habit"]},
                                "right": {"title": "be used to + -ing", "lines": ["I'm used to waking early.", "normal now"]}}}),
    "past_modals": ("should have / needn't have", "B2", "I should have called; you needn't have come",
                    "modal + have + V3 to judge the past: should have (a mistake), needn't have (unnecessary).",
                    ["I should have studied more.", "You needn't have brought food."],
                    {"formula": ["should / shouldn't have + V3", "needn't have + V3"],
                     "diagram": {"kind": "timeline", "items": [
                         {"type": "point", "at": -0.5, "label": "I didn't call"},
                         {"type": "point", "at": 0, "label": "now: I should have called"}]}}),
    "future_in_past": ("was going to / would", "B2", "I was going to call you, but…",
                       "was / were going to + verb for a past plan that did not happen.",
                       ["I was going to phone you, but I forgot.", "He said he would help."],
                       {"formula": ["was / were going to + verb", "said (that) … would + verb"],
                        "diagram": {"kind": "timeline", "items": [
                            {"type": "point", "at": -0.7, "label": "the plan"},
                            {"type": "cross", "at": -0.3, "label": "it didn't happen"}]}}),
}

# Folded into the one catalogue, so everything - the analyser, the board, the
# syllabus - sees the full list. The course's own skills keep their ids, so a
# learner's measured progress carries straight over.
for _sid, (_name, _band, _hint, _rule, _examples, _board) in _MORE_SKILLS.items():
    ENGLISH_SKILLS[_sid] = (_name, _band, _hint)
    SKILL_TIPS[_sid] = (_rule, _examples)
    SKILL_BOARD[_sid] = _board

# The possessive 's has its own entry now.
ENGLISH_SKILLS["pronouns_possessives"] = ("pronouns (I / me / my / mine)", "A1",
                                          "subject, object and possessive: I / me / my / mine")

# Some course skills belong one level down on a real syllabus.
for _sid in ("present_simple", "questions", "articles", "plurals_quantity",
             "prepositions", "pronouns_possessives"):
    _name, _band, _hint = ENGLISH_SKILLS[_sid]
    ENGLISH_SKILLS[_sid] = (_name, "A1", _hint)

SYLLABUS_BANDS = ("A1", "A2", "B1", "B2")


def skills_by_band(skills: dict) -> dict[str, list[str]]:
    """The syllabus: every skill id, grouped by level, in teaching order."""
    out: dict[str, list[str]] = {b: [] for b in SYLLABUS_BANDS}
    for sid, (_name, band, _hint) in skills.items():
        out.setdefault(band, []).append(sid)
    return out


# ── The rule in one simple sentence ──────────────────────────────────────────
# What the board and the tutor say first: A2 words, one idea, no grammar terms
# the learner has not met. The longer rule (SKILL_TIPS) stays for the account
# page.

SIMPLE_RULES: dict[str, str] = {
    # A1
    "be_verb": "I am, he / she / it is, we / you / they are.",
    "have_got": "Have got means have. With he / she / it: has got.",
    "there_is_are": "There is for one thing, there are for many things.",
    "imperatives": "To tell someone to do something, start with the verb: Sit down!",
    "this_that": "This and these are near you. That and those are far.",
    "can_ability": "Can + verb says what you are able to do. No 'to', no -s.",
    "possessive_case": "Add 's to a name to show it is theirs: Taleh's car.",
    "adverbs_frequency": "Always, usually, never go before the main verb.",
    "question_words": "Start the question with the word for what you want to know.",
    "like_ing": "After like, love and hate, the verb takes -ing.",
    "present_simple": "For habits and facts. With he / she / it, add -s.",
    "questions": "In a question, do / does / did comes before the person.",
    "articles": "A for something new. The for something we both know.",
    "plurals_quantity": "Many for things you can count, much for things you can't.",
    "prepositions": "In for big times and places, on for days, at for exact points.",
    "dependent_prepositions": "Some words always take the same small word after them: share with, listen to, good at.",
    "pronouns_possessives": "I, me, my, mine - the same person in different jobs.",
    # A2
    "present_continuous": "For what is happening right now: am / is / are + -ing.",
    "past_simple": "For finished actions in the past: add -ed, or use the special past form.",
    "future_forms": "Going to for plans, will for things you decide now.",
    "word_order": "Who, then the action, then what, then where, then when.",
    "subject_verb_agreement": "One person: she works. Many people: they work.",
    "comparatives": "Short words add -er, long words use more.",
    "modals_basic": "Can, must, should + verb. Never 'to' after them.",
    "linking_words": "And adds, but shows the opposite, because gives the reason.",
    "word_choice": "Some words go together: make a decision, do homework.",
    "past_be": "The past of am / is is was; the past of are is were.",
    "present_continuous_future": "Am / is / are + -ing can also be a plan for the future.",
    "would_like": "Would like is a polite way to say want.",
    "have_to": "Have to: you must. Don't have to: it is not needed.",
    "too_enough": "Too means more than OK. Enough means as much as you need.",
    "adverbs_manner": "To say HOW you do something, add -ly: quick - quickly.",
    "could_past": "Could is the past of can.",
    "some_any_compounds": "Something in normal sentences, anything in questions and with not.",
    # B1
    "present_perfect": "Have + past participle: it happened before, it matters now.",
    "perfect_vs_past": "With a finished time (yesterday), use the past. Without a time, use have + done.",
    "past_continuous": "Was / were + -ing: something was going on when another thing happened.",
    "used_to": "Used to + verb: you did it often before, but not now.",
    "first_conditional": "If + now, will + verb: a real result in the future.",
    "modals_possibility": "Might and could mean maybe.",
    "second_conditional": "If + past, would + verb: an imagined situation now.",
    "gerund_infinitive": "Some verbs take -ing (enjoy cooking), some take to (want to cook).",
    "phrasal_verbs": "Verb + small word = a new meaning: give up = stop trying.",
    "relative_clauses": "Who for people, which or that for things - it says WHICH one.",
    "passive_simple": "Be + past participle, when the action is more important than who did it.",
    "word_forms": "One word, different jobs: happy (describes), happiness (a thing), happily (how).",
    "present_perfect_continuous": "Have been + -ing: it started before and it is still going on.",
    "zero_conditional": "If + now, now: something that is always true.",
    "question_tags": "A small question at the end: It's cold, isn't it?",
    "reflexive_pronouns": "Myself, yourself: when you do something to yourself.",
    "so_such": "So + describing word, such + a + describing word + thing.",
    "indirect_questions": "Can you tell me where the station is? - normal order after the start.",
    "both_either_neither": "Both = the two, either = one of two, neither = not one of them.",
    "advice_modals": "Should = a good idea. Had better = a strong warning.",
    # B2
    "past_perfect": "Had + past participle: the thing that happened FIRST in the past.",
    "third_conditional": "If + had done, would have done: imagining a different past.",
    "wish_regret": "Wish + past: you want now to be different.",
    "reported_speech": "When you tell what someone said, the verb goes one step back.",
    "modals_deduction": "Must have, might have, can't have: guessing about the past.",
    "passive_advanced": "Has been done, will be done: the passive in other tenses.",
    "future_advanced": "Will be doing: in the middle of it then. Will have done: finished by then.",
    "discourse_markers": "However, as a result, in fact: words that connect your ideas.",
    "collocations": "Words that go together: heavy rain, make a mistake.",
    "past_perfect_continuous": "Had been + -ing: it was going on before another past moment.",
    "mixed_conditionals": "A different past with a result now: If I had studied, I would be a doctor.",
    "causative": "Have / get something done: someone else does it for you.",
    "non_defining_relative": "Extra information between commas, with who or which.",
    "participle_clauses": "Start with -ing to join two actions: Feeling tired, I went home.",
    "be_used_to": "Be used to + -ing: it is normal for you now.",
    "past_modals": "Should have done: it was a mistake not to do it.",
    "future_in_past": "Was going to: a plan in the past that did not happen.",
}


def simple_rule(sid: str) -> str:
    return SIMPLE_RULES.get(sid) or SKILL_TIPS.get(sid, ("", []))[0]
