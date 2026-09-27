"""
tutor/english_small_talk.py - the English small talk course: A2 to B1 in 5 weeks.

A second English course, next to the phrasal verbs one: English learned
through SMALL TALK - the short, friendly chats of every day with a neighbour,
a colleague, a barista, a classmate or a stranger on a train.

The method is one rule, practised in every lesson: never give a one-word
answer. React first (Really? That's great! Oh no!), answer, add one small
detail and send the question back (How about you?). The "Longer sentences"
part of each lesson shows one short answer growing into that full small talk
turn; in "Build sentences" the learner makes such turns themselves.

Weeks 1-2 are A2 (the basics and everyday chats), weeks 3-5 are B1 (news,
plans, university, work and small talk anywhere). Everything is explained in
simple English, with the Azerbaijani translation on the board. The learner is
a man from Baku who lives in Bratislava.
"""
from __future__ import annotations


def _items(rows: list[tuple]) -> list[dict]:
    return [{"text": t, "meaning": m, "native": az, "example": ex} for t, m, az, ex in rows]


def _lesson(lid: str, week: int, day: int, band: str, title: str, goal: str,
            words: list, phrases: list, grammar: dict, partner_role: str,
            dialogue: list, extend: list, build: list, questions: list, speak: str,
            skills: list[str] | None = None) -> dict:
    return {
        "id": lid, "week": week, "day": day, "band": band, "title": title, "goal": goal,
        "words": _items(words),
        "phrases": [{"text": t, "meaning": m, "native": az} for t, m, az in phrases],
        "grammar": dict(grammar, skills=skills or []),
        "partner_role": partner_role,
        "dialogue": [{"who": who, "text": text, "meaning": ""} for who, text in dialogue],
        # One short answer, growing into a full small talk turn: (the sentence now, what was added).
        "extend": [[{"text": text, "how": how} for text, how in extend]],
        "translate": [],
        "build": [{"task": task, "answer": answer} for task, answer in build],
        "questions": [{"q": q, "meaning": "", "example": ex} for q, ex in questions],
        "speak": speak,
    }


LESSONS: list[dict] = [
    # ══ WEEK 1 - A2: the small talk basics ═══════════════════════════════════
    _lesson(
        "en-t01", 1, 1, "A2", "How's it going? - the small talk ping-pong",
        "answer 'How's it going?' with a detail and always ask back",
        words=[
            ("How's it going?", "an easy way to say 'How are you?'", "Necəsən? İşlər necədir?",
             "Hi Anna, how's it going?"),
            ("not bad", "OK, quite good", "pis deyil", "Not bad, thanks."),
            ("pretty good", "quite good", "xeyli yaxşı", "I'm pretty good, actually."),
            ("a bit tired", "a little tired", "bir az yorğun", "I'm a bit tired today."),
            ("busy", "with a lot to do", "məşğul", "Work is really busy this week."),
            ("How about you?", "and you?", "Bəs sən?", "I'm fine. How about you?"),
        ],
        phrases=[
            ("Hi! How's it going?", "a friendly hello", "Salam! Necəsən?"),
            ("Not bad, thanks. How about you?", "answer + ask back", "Pis deyil, sağ ol. Bəs sən?"),
            ("Pretty good, but I'm a bit tired.", "answer + a detail", "Yaxşıyam, amma bir az yorğunam."),
            ("Busy week?", "a short follow-up question", "Məşğul həftədir?"),
            ("See you later!", "an easy goodbye", "Sonra görüşərik!"),
        ],
        grammar={
            "name": "Answer + detail + ask back",
            "rule": ("Small talk is a ping-pong game. Never give only one word: answer, add ONE small "
                     "detail with 'but' or 'because', and send the question back: 'How about you?' or "
                     "'And you?'. The other person always has something to say."),
            "table": ["answer: Pretty good.", "+ detail: ...but I'm a bit tired.", "+ ask back: How about you?"],
            "examples": [("Not bad, thanks. How about you?", ""),
                         ("Pretty good, but I'm a bit tired today.", ""),
                         ("I'm great, because it's Friday! And you?", "")],
        },
        skills=["present_simple", "discourse_markers"],
        partner_role="neighbour on the stairs",
        dialogue=[
            ("partner", "Hi Taleh! How's it going?"),
            ("learner", "Hi! Pretty good, thanks. How about you?"),
            ("partner", "Not bad, but I'm a bit tired."),
            ("learner", "Oh, busy week?"),
            ("partner", "Yes, really busy. Anyway, see you later!"),
            ("learner", "See you! Have a nice day!"),
        ],
        extend=[
            ("Good.", "the one-word answer"),
            ("I'm pretty good, thanks.", "a full sentence"),
            ("I'm pretty good, thanks, but I'm a bit tired today.", "BUT + a small detail"),
            ("I'm pretty good, thanks, but I'm a bit tired today. How about you?", "the question back"),
        ],
        build=[
            ("Add a detail with 'but': I'm fine.", "I'm fine, but I'm really busy this week."),
            ("Add the question back: Not bad, thanks.", "Not bad, thanks. How about you?"),
            ("Add a reason with 'because': I'm great.", "I'm great, because it's the weekend tomorrow."),
            ("Answer and ask back: How's it going?", "Pretty good, thanks. How's it going with you?"),
        ],
        questions=[
            ("How's it going today?", "Pretty good, but I'm a bit tired. How about you?"),
            ("Busy week?", "Yes, very busy at work, but I'm OK. And you?"),
        ],
        speak=("Small talk ping-pong: the tutor greets you as different people (a friend, a neighbour, "
               "your boss). Answer, add one detail and always ask back."),
    ),
    _lesson(
        "en-t02", 1, 2, "A2", "Where are you from? - you and your city",
        "say where you are from and where you live, and react with interest",
        words=[
            ("originally", "where you were born or grew up", "əslən", "I'm originally from Baku."),
            ("grow up", "live as a child somewhere", "böyümək", "I grew up near the sea."),
            ("move", "go to live in another place", "köçmək", "I moved here two years ago."),
            ("What's it like?", "tell me about it", "Necədir?", "Baku? What's it like?"),
            ("by the sea", "next to the sea", "dəniz kənarında", "Baku is by the sea."),
            ("Really?", "a reaction: I'm surprised and interested", "Doğrudan?", "Really? I didn't know that."),
        ],
        phrases=[
            ("Where are you from?", "the classic question", "Haralısan?"),
            ("I'm originally from Baku, in Azerbaijan.", "your country and city", "Əslən Bakıdanam, Azərbaycandan."),
            ("But I live in Bratislava now.", "where you live today", "Amma indi Bratislavada yaşayıram."),
            ("How long have you lived here?", "a follow-up question", "Nə vaxtdan burada yaşayırsan?"),
            ("Oh really? What's it like?", "a reaction + a question", "Doğrudan? Necə yerdir?"),
        ],
        grammar={
            "name": "I'm from ... / I live in ... / I moved here ...",
            "rule": ("'I'm from' + your country or city. 'I live in' + where you live now (present simple). "
                     "'I moved here' + when (past simple): I moved here two years ago. "
                     "Ask: How long have you lived here?"),
            "table": ["I'm from Baku.", "I live in Bratislava.", "I moved here two years ago."],
            "examples": [("I'm originally from Baku, but I live in Bratislava now.", ""),
                         ("I moved here two years ago for work.", ""),
                         ("How long have you lived here?", "")],
        },
        skills=["present_simple", "past_simple", "prepositions"],
        partner_role="new colleague",
        dialogue=[
            ("partner", "So, where are you from, Taleh?"),
            ("learner", "I'm originally from Baku, in Azerbaijan. How about you?"),
            ("partner", "I'm from Košice. Baku? What's it like?"),
            ("learner", "It's a big city by the sea. It's windy, but really beautiful."),
            ("partner", "Oh really? And how long have you lived here?"),
            ("learner", "I moved here two years ago. I really like it here."),
        ],
        extend=[
            ("Baku.", "the one-word answer"),
            ("I'm from Baku.", "a full sentence"),
            ("I'm originally from Baku, but I live in Bratislava now.", "BUT + where you live now"),
            ("I'm originally from Baku, but I live in Bratislava now. How about you? Where are you from?",
             "the question back"),
        ],
        build=[
            ("Add WHEN: I moved here.", "I moved here two years ago."),
            ("Join with 'but': I'm from Baku. I live in Bratislava.", "I'm from Baku, but I live in Bratislava."),
            ("React and ask 'What's it like?': She is from Vienna.", "Oh really? What's it like?"),
            ("Describe your city in one long sentence: Baku - big - by the sea - windy.",
             "Baku is a big city by the sea, and it's very windy."),
        ],
        questions=[
            ("Where are you from originally?", "I'm originally from Baku, but I live in Bratislava now."),
            ("What's your city like?", "It's a big, busy city by the sea, and the food is amazing."),
        ],
        speak=("Meet three new people. Tell each one where you are from and where you live, react with "
               "'Oh really? What's it like?' and ask back."),
    ),
    _lesson(
        "en-t03", 1, 3, "A2", "What do you do? - work small talk",
        "say what you do and whether you like it, and ask about someone's job",
        words=[
            ("work as", "have the job of", "... kimi işləmək", "I work as a programmer."),
            ("work for", "have a job in a company", "... şirkətində işləmək", "I work for a small IT company."),
            ("be into", "like something a lot", "çox xoşlamaq", "I'm really into my job."),
            ("challenging", "hard, but interesting", "çətin, amma maraqlı", "My job is challenging."),
            ("in the end", "finally", "sonunda", "It's hard, but in the end I love it."),
            ("How do you like it?", "do you enjoy it?", "Xoşuna gəlir?", "A new job? How do you like it?"),
        ],
        phrases=[
            ("What do you do?", "What's your job?", "Nə işlə məşğulsan?"),
            ("I work as a programmer for an IT company.", "your job + where", "Bir IT şirkətində proqramçı işləyirəm."),
            ("How do you like it?", "do you enjoy it?", "Xoşuna gəlir?"),
            ("I love it, but it can be challenging.", "a feeling + a detail", "Çox xoşuma gəlir, amma bəzən çətin olur."),
            ("What about you? What do you do?", "the question back", "Bəs sən? Nə işlə məşğulsan?"),
        ],
        grammar={
            "name": "work as / work for / work in",
            "rule": ("'work as' + a job (work as a programmer), 'work for' + a company (work for Google), "
                     "'work in' + a place or field (work in an office, work in IT). "
                     "Use 'a' before a job: I'm a programmer."),
            "table": ["I work as + a job", "I work for + a company", "I work in + a place / a field"],
            "examples": [("I work as a programmer.", ""),
                         ("I work for a small IT company.", ""),
                         ("I work in an office in the city centre.", "")],
        },
        skills=["prepositions", "present_simple"],
        partner_role="guest at a party",
        dialogue=[
            ("partner", "So, what do you do, Taleh?"),
            ("learner", "I work as a programmer for an IT company. What about you?"),
            ("partner", "I'm a nurse. Programming! How do you like it?"),
            ("learner", "I love it, but it can be challenging sometimes."),
            ("partner", "Do you work from home?"),
            ("learner", "Two days a week. The other days I work in an office in the centre."),
        ],
        extend=[
            ("Programmer.", "the one-word answer"),
            ("I work as a programmer.", "WORK AS + your job"),
            ("I work as a programmer for a small IT company in the centre.", "WORK FOR + WHERE"),
            ("I work as a programmer for a small IT company in the centre, and I really love it. "
             "What do you do?", "a feeling + the question back"),
        ],
        build=[
            ("Use 'work for': I have a job in a bank.", "I work for a bank."),
            ("Add a feeling with 'but': I love my job.", "I love my job, but it can be stressful."),
            ("Ask back about the job: I'm a teacher.", "Oh nice! How do you like it?"),
            ("Make it longer: I work in an office. (where + how often)",
             "I work in an office in the centre three days a week."),
        ],
        questions=[
            ("What do you do?", "I work as a programmer for an IT company. What about you?"),
            ("How do you like your job?", "I really like it, but it can be challenging sometimes."),
        ],
        speak=("At a party the tutor asks about your work. Say what you do, where, and how you like it - "
               "then ask the tutor the same questions and react to their answers."),
    ),
    _lesson(
        "en-t04", 1, 4, "A2", "Lovely day, isn't it? - the weather",
        "start small talk with anyone about the weather, with a question tag",
        words=[
            ("lovely", "very nice", "çox gözəl", "It's a lovely day."),
            ("freezing", "very, very cold", "şaxtalı, çox soyuq", "It's freezing this morning!"),
            ("boiling", "very, very hot", "çox isti", "It's boiling in here."),
            ("pouring", "raining a lot", "leysan yağır", "It's pouring outside."),
            ("forecast", "what the weather will be", "hava proqnozu", "The forecast says rain tomorrow."),
            ("isn't it?", "a question at the end: do you agree?", "elə deyil?", "It's cold, isn't it?"),
        ],
        phrases=[
            ("Lovely day, isn't it?", "the easiest way to start", "Gözəl gündür, elə deyil?"),
            ("It's freezing this morning!", "about the cold", "Bu səhər dəhşətli soyuqdur!"),
            ("I know! And it's so windy.", "agree + add", "Elədir! Həm də çox küləklidir."),
            ("Did you see the forecast?", "a follow-up", "Hava proqnozuna baxdın?"),
            ("Let's hope it's sunny at the weekend.", "a friendly ending", "Ümid edək ki, həftəsonu günəşli olar."),
        ],
        grammar={
            "name": "Question tags: isn't it? wasn't it?",
            "rule": ("Add a short question at the end and the other person will agree and talk: "
                     "It's cold, isn't it? It was lovely yesterday, wasn't it? It isn't very warm, is it? "
                     "Positive sentence → negative tag. Negative sentence → positive tag."),
            "table": ["It's cold, isn't it?", "It was hot yesterday, wasn't it?", "It isn't warm, is it?"],
            "examples": [("It's a lovely day, isn't it?", ""),
                         ("It was really cold yesterday, wasn't it?", ""),
                         ("It isn't very warm today, is it?", "")],
        },
        skills=["word_order", "present_simple"],
        partner_role="neighbour at the bus stop",
        dialogue=[
            ("partner", "Morning! It's freezing today, isn't it?"),
            ("learner", "I know! And it's so windy."),
            ("partner", "Is it like this in your country too?"),
            ("learner", "In Baku it's very windy too, but the winters are warmer."),
            ("partner", "Lucky you! The forecast says snow tomorrow."),
            ("learner", "Oh no! Let's hope it's sunny at the weekend."),
        ],
        extend=[
            ("Cold.", "the one-word comment"),
            ("It's really cold today.", "a full sentence"),
            ("It's really cold today, and it's so windy.", "AND + one more detail"),
            ("It's really cold today, and it's so windy, isn't it?", "a TAG - now the other person answers"),
        ],
        build=[
            ("Add a tag: It's a lovely day.", "It's a lovely day, isn't it?"),
            ("Add a tag: It was hot yesterday.", "It was hot yesterday, wasn't it?"),
            ("Compare with Baku: It's cold here. (Baku - warmer)", "It's cold here, but in Baku it's much warmer."),
            ("React and add: It's pouring outside!", "Oh no! And I don't have an umbrella."),
        ],
        questions=[
            ("What's the weather like today?", "It's cold and windy today, but at least it's sunny."),
            ("What's the weather like in Baku in summer?", "It's boiling in summer, but there's always wind from the sea."),
        ],
        speak=("Start the small talk yourself: say something about today's weather with a tag, answer "
               "the tutor and compare it with Baku."),
    ),

    # ══ WEEK 2 - A2: everyday chats ══════════════════════════════════════════
    _lesson(
        "en-t05", 2, 1, "A2", "At the coffee shop",
        "order politely, ask the barista for a tip and chat with someone at the next table",
        words=[
            ("Can I get ...?", "a polite way to order", "... ala bilərəm?", "Can I get a latte, please?"),
            ("to go", "to take away", "aparmaq üçün", "A cappuccino to go, please."),
            ("for here", "to stay in the café", "burada", "For here, please."),
            ("recommend", "say something is good", "tövsiyə etmək", "What do you recommend?"),
            ("Is this seat taken?", "can I sit here?", "Bu yer tutulub?", "Excuse me, is this seat taken?"),
            ("cosy", "warm and comfortable", "rahat, isti", "This café is really cosy."),
        ],
        phrases=[
            ("Can I get a cappuccino, please?", "a polite order", "Bir kapuçino ala bilərəm?"),
            ("For here or to go?", "the barista's question", "Burada, yoxsa aparmaq üçün?"),
            ("What do you recommend?", "ask for a tip", "Nə tövsiyə edirsiniz?"),
            ("Excuse me, is this seat taken?", "before you sit", "Bağışlayın, bu yer tutulub?"),
            ("It's really cosy here, isn't it?", "start a chat", "Burada çox rahatdır, elə deyil?"),
        ],
        grammar={
            "name": "Can I get ...? / I'd like ... / Could you ...?",
            "rule": ("To order politely use 'Can I get ...?' or 'I'd like ...' (= I would like). To ask for "
                     "help: 'Could you ...?'. Always add 'please'. 'I want' can sound rude in a café."),
            "table": ["Can I get a latte, please?", "I'd like a piece of cake, please.",
                      "Could you warm it up, please?"],
            "examples": [("Can I get a cappuccino to go, please?", ""),
                         ("I'd like a piece of that chocolate cake.", ""),
                         ("Could you recommend something sweet?", "")],
        },
        skills=["modals_basic"],
        partner_role="barista, then a guest at the next table",
        dialogue=[
            ("partner", "Hi there! What can I get you?"),
            ("learner", "Hi! Can I get a cappuccino, please? And what do you recommend with it?"),
            ("partner", "Our apple cake is really good today. For here or to go?"),
            ("learner", "For here, please. ... Excuse me, is this seat taken?"),
            ("partner", "No, go ahead. Is it your first time here?"),
            ("learner", "Yes, it is. It's really cosy here, isn't it? And the coffee is great."),
        ],
        extend=[
            ("Cappuccino.", "the one-word order"),
            ("Can I get a cappuccino, please?", "CAN I GET - polite"),
            ("Can I get a cappuccino and a piece of apple cake, for here, please?", "what else + for here / to go"),
            ("Can I get a cappuccino and a piece of apple cake, for here, please? Do you have oat milk?",
             "a question for the barista"),
        ],
        build=[
            ("Make it polite: I want a tea.", "Can I get a tea, please?"),
            ("Ask for a tip: (something sweet)", "What do you recommend? Something sweet, maybe?"),
            ("Ask to sit: (the seat next to someone)", "Excuse me, is this seat taken?"),
            ("Start a chat with a tag: This café is cosy.", "This café is really cosy, isn't it?"),
        ],
        questions=[
            ("What do you usually order in a café?", "I usually get a cappuccino and something sweet."),
            ("What's your favourite café?", "It's a small café in the centre, because it's cosy and quiet."),
        ],
        speak=("Café role play: order from the tutor as the barista, ask for a tip, then sit next to a "
               "stranger and start small talk."),
    ),
    _lesson(
        "en-t06", 2, 2, "A2", "In a shop",
        "ask for help, ask about size and price, and chat at the till",
        words=[
            ("just looking", "not buying yet", "sadəcə baxıram", "I'm just looking, thanks."),
            ("look for", "try to find", "axtarmaq", "I'm looking for a winter jacket."),
            ("try on", "put on clothes to see if they fit", "geyinib yoxlamaq", "Can I try it on?"),
            ("fit", "be the right size", "ölçüsü uyğun olmaq", "It fits perfectly."),
            ("changing room", "a room to try on clothes", "paltar dəyişmə otağı", "The changing rooms are over there."),
            ("on sale", "cheaper than usual", "endirimdə", "These shoes are on sale."),
        ],
        phrases=[
            ("Can I help you with anything?", "the shop assistant's question", "Sizə kömək edə bilərəm?"),
            ("I'm just looking, thanks.", "a polite 'no'", "Sadəcə baxıram, sağ olun."),
            ("Do you have this in a medium?", "ask for a size", "Bunun orta ölçüsü var?"),
            ("Can I try it on?", "before you buy", "Geyinib yoxlaya bilərəm?"),
            ("Can I pay by card?", "at the till", "Kartla ödəyə bilərəm?"),
        ],
        grammar={
            "name": "this / that / these / those; it / them",
            "rule": ("One thing near you: this jacket. One thing far: that jacket. More things: these shoes, "
                     "those shoes. Then use 'it' for one thing and 'them' for more: Can I try it on? "
                     "Can I try them on? (NOT: try on it)."),
            "table": ["near: this jacket · these shoes", "far: that jacket · those shoes",
                      "Can I try it on? · Can I try them on?"],
            "examples": [("Do you have this jacket in black?", ""),
                         ("How much are those shoes?", ""),
                         ("I like them. Can I try them on?", "")],
        },
        skills=["pronouns_possessives", "phrasal_verbs"],
        partner_role="shop assistant",
        dialogue=[
            ("partner", "Hi! Can I help you with anything?"),
            ("learner", "Yes, please. I'm looking for a warm winter jacket."),
            ("partner", "These ones are new. What size are you?"),
            ("learner", "Medium, I think. Can I try this one on?"),
            ("partner", "Sure, the changing rooms are over there. ... How does it fit?"),
            ("learner", "It fits perfectly. I'll take it! Can I pay by card?"),
        ],
        extend=[
            ("A jacket.", "the one-word answer"),
            ("I'm looking for a jacket.", "LOOKING FOR + what"),
            ("I'm looking for a warm winter jacket, size medium.", "what kind + the size"),
            ("I'm looking for a warm winter jacket, size medium, because it's freezing here in winter. "
             "Do you have anything like that?", "BECAUSE + a question"),
        ],
        build=[
            ("Use 'them': I like these shoes. Can I try ... on?", "I like these shoes. Can I try them on?"),
            ("Ask for a size: (this shirt - large)", "Do you have this shirt in a large?"),
            ("Say no politely: (the assistant offers help)", "I'm just looking, thanks."),
            ("Make it longer: It fits. (perfectly + I'll take it)", "It fits perfectly, so I'll take it."),
        ],
        questions=[
            ("What do you usually buy in a clothes shop?", "I usually buy T-shirts and jeans, and a jacket in winter."),
            ("Do you prefer shopping online or in shops?", "I prefer shops, because I can try things on."),
        ],
        speak=("Shop role play: the tutor is a shop assistant. Say what you are looking for, ask about "
               "the size, colour and price, try it on and pay - with one small talk line at the till."),
    ),
    _lesson(
        "en-t07", 2, 3, "A2", "What are you into? - free time",
        "talk about what you like doing and find things in common",
        words=[
            ("be into", "like something a lot", "çox xoşlamaq", "I'm really into football."),
            ("hobby", "something you do for fun", "hobbi", "Cooking is my hobby."),
            ("work out", "do exercise", "məşq etmək", "I work out three times a week."),
            ("Me too!", "I agree, I do it too", "Mən də!", "I love hiking. - Me too!"),
            ("Me neither.", "I don't do it either", "Mən də yox.", "I don't like running. - Me neither."),
            ("in common", "the same for both people", "ortaq", "We have a lot in common."),
        ],
        phrases=[
            ("What are you into?", "What do you like doing?", "Nəyi xoşlayırsan?"),
            ("I'm really into cooking and travelling.", "your hobbies", "Yemək bişirməyi və səyahəti çox xoşlayıram."),
            ("How often do you do that?", "a follow-up", "Bunu nə qədər tez-tez edirsən?"),
            ("Me too! / Me neither.", "agree", "Mən də! / Mən də yox."),
            ("We should go together some time!", "make a plan", "Nə vaxtsa birlikdə getməliyik!"),
        ],
        grammar={
            "name": "like / love / be into + -ing",
            "rule": ("After like, love, enjoy, hate and 'be into' a verb takes -ing: I like cooking, I'm "
                     "into hiking, I hate getting up early. To agree: Me too! (positive) / Me neither. "
                     "(negative)."),
            "table": ["I like / love / enjoy + cooking", "I'm into + hiking", "I don't like running. - Me neither."],
            "examples": [("I really enjoy cooking for my friends.", ""),
                         ("I'm into hiking, especially in the mountains.", ""),
                         ("I don't like getting up early. - Me neither!", "")],
        },
        skills=["like_ing", "gerund_infinitive"],
        partner_role="new friend",
        dialogue=[
            ("partner", "So, what are you into, Taleh?"),
            ("learner", "I'm really into cooking and travelling. How about you?"),
            ("partner", "I love hiking. Do you like hiking?"),
            ("learner", "Yes! I don't do it very often, but I love the mountains."),
            ("partner", "Me too! I go to the Tatras every summer."),
            ("learner", "Really? We should go together some time!"),
        ],
        extend=[
            ("Cooking.", "the one-word answer"),
            ("I'm really into cooking.", "BE INTO + -ing"),
            ("I'm really into cooking, especially Azerbaijani food.", "ESPECIALLY + a detail"),
            ("I'm really into cooking, especially Azerbaijani food, and I cook for my friends every weekend. "
             "What are you into?", "HOW OFTEN + the question back"),
        ],
        build=[
            ("Use -ing: I like (read) books.", "I like reading books."),
            ("Agree: I don't like running.", "Me neither."),
            ("Add 'especially': I love travelling.", "I love travelling, especially to the mountains."),
            ("Make a plan: We both like football.", "We both like football - we should watch a match together!"),
        ],
        questions=[
            ("What are you into?", "I'm really into cooking, and I also like hiking at the weekend."),
            ("What don't you like doing?", "I don't like cleaning the flat, but I do it every Saturday."),
        ],
        speak=("Find three things you and the tutor both like. Say what you're into, answer with 'Me "
               "too!' or 'Me neither.' and make a plan together."),
    ),
    _lesson(
        "en-t08", 2, 4, "A2", "No way! - reactions that keep the talk going",
        "react to good and bad news, ask a follow-up and ask again when you don't understand",
        words=[
            ("No way!", "I can't believe it! (surprise)", "Ola bilməz!", "You won? No way!"),
            ("That's great!", "good news reaction", "Bu əladır!", "A new job? That's great!"),
            ("Oh no!", "bad news reaction", "Ay aman! Vay!", "Oh no! What happened?"),
            ("sorry to hear that", "I feel bad for you", "buna təəssüf edirəm", "I'm sorry to hear that."),
            ("What happened?", "tell me the story", "Nə olub?", "Oh no! What happened?"),
            ("Sorry, could you say that again?", "I didn't understand", "Bağışla, təkrar deyə bilərsən?",
             "Sorry, could you say that again?"),
        ],
        phrases=[
            ("Really? That's great! When did you hear?", "good news + a question", "Doğrudan? Əladır! Nə vaxt bildin?"),
            ("Oh no, I'm sorry to hear that.", "bad news", "Vay, buna təəssüf edirəm."),
            ("No way! Are you serious?", "big surprise", "Ola bilməz! Ciddisən?"),
            ("Sorry, could you say that again?", "not understood", "Bağışla, təkrar deyə bilərsən?"),
            ("So what happened next?", "keep the story going", "Bəs sonra nə oldu?"),
        ],
        grammar={
            "name": "React first, then ask",
            "rule": ("A good small talker reacts BEFORE answering, then asks ONE follow-up question with "
                     "what, when, where, how or why. Good news: That's great! Bad news: Oh no, I'm sorry "
                     "to hear that. Surprise: No way! Really?"),
            "table": ["good news → That's great! + When ...?", "bad news → Oh no! + What happened?",
                      "surprise → No way! + Are you serious?"],
            "examples": [("That's great! When do you start?", ""),
                         ("Oh no, I'm sorry to hear that. Are you OK?", ""),
                         ("No way! How did you do that?", "")],
        },
        skills=["discourse_markers"],
        partner_role="friend with news",
        dialogue=[
            ("partner", "Guess what? I got a new job!"),
            ("learner", "No way! That's great! Where is it?"),
            ("partner", "In Vienna, so I have to travel a lot."),
            ("learner", "Sorry, could you say that again? Where?"),
            ("partner", "In Vienna. It's an hour by train."),
            ("learner", "Oh, that's not too far. So when do you start?"),
        ],
        extend=[
            ("Great.", "a one-word reaction"),
            ("Really? That's great!", "surprise + reaction"),
            ("Really? That's great! Where is the new job?", "a question about it"),
            ("Really? That's great! Where is the new job, and when do you start?", "one more question - keep it going"),
        ],
        build=[
            ("React and ask: I passed my driving test!", "No way! That's great! Was it difficult?"),
            ("React and ask: I lost my phone yesterday.", "Oh no! I'm sorry to hear that. What happened?"),
            ("Ask again politely: (you didn't hear)", "Sorry, could you say that again?"),
            ("Keep the story going: ...and then the lights went out.", "Really? So what happened next?"),
        ],
        questions=[
            ("It's my birthday today!", "Really? Happy birthday! Are you doing anything special?"),
            ("I can't come tomorrow, I'm ill.", "Oh no, I'm sorry to hear that. Get well soon!"),
        ],
        speak=("The tutor tells you five pieces of news, good and bad. React first (No way! That's great! "
               "Oh no!), then ask one question to keep the talk going."),
    ),

    # ══ WEEK 3 - B1: weekends, plans and news ════════════════════════════════
    _lesson(
        "en-t09", 3, 1, "B1", "How was your weekend? - the Monday chat",
        "tell a colleague about your weekend in the past simple and ask about theirs",
        words=[
            ("relaxing", "calm and restful", "dincəldirici", "It was a relaxing weekend."),
            ("nothing much", "nothing special", "xüsusi heç nə", "Nothing much, I just stayed in."),
            ("stay in", "stay at home", "evdə qalmaq", "On Saturday I stayed in and watched films."),
            ("go out", "leave home to have fun", "çölə çıxmaq, əylənməyə getmək", "On Friday we went out for dinner."),
            ("day trip", "a trip there and back in one day", "bir günlük səfər", "We went on a day trip to Vienna."),
            ("in the end", "finally, after all", "sonunda", "It rained, but in the end it was fun."),
        ],
        phrases=[
            ("How was your weekend?", "the Monday question", "Həftəsonun necə keçdi?"),
            ("It was really nice, thanks.", "a short answer", "Çox yaxşı keçdi, sağ ol."),
            ("Nothing much, I just stayed in.", "a quiet weekend", "Xüsusi heç nə, sadəcə evdə qaldım."),
            ("We went on a day trip to the mountains.", "a busy weekend", "Dağlara bir günlük səfərə getdik."),
            ("What about yours? Did you do anything fun?", "ask back", "Bəs səninki? Maraqlı bir şey etdin?"),
        ],
        grammar={
            "name": "Past simple for your weekend",
            "rule": ("For finished time (yesterday, on Saturday, last weekend) use the past simple: "
                     "regular verbs + -ed (stayed, watched), many irregular (go → went, have → had, "
                     "see → saw). Question: Did you ...? - Yes, I did. / No, I didn't."),
            "table": ["stay → stayed · watch → watched", "go → went · have → had · see → saw",
                      "Did you do anything fun? - Yes, I did."],
            "examples": [("On Saturday I stayed in and watched a film.", ""),
                         ("On Sunday we went on a day trip to Vienna.", ""),
                         ("Did you have a good weekend?", "")],
        },
        skills=["past_simple"],
        partner_role="colleague on Monday morning",
        dialogue=[
            ("partner", "Morning, Taleh! How was your weekend?"),
            ("learner", "Morning! It was really nice, thanks. We went on a day trip to the mountains."),
            ("partner", "Oh, lovely! Where did you go?"),
            ("learner", "To the High Tatras. It rained on Sunday, but in the end it was great."),
            ("partner", "Sounds amazing. I just stayed in, nothing much."),
            ("learner", "That's nice too. Did you watch anything good?"),
        ],
        extend=[
            ("Good.", "the one-word answer"),
            ("It was good, thanks. I went to the mountains.", "WHERE you went"),
            ("It was good, thanks. On Saturday I went to the mountains with some friends.", "WHEN + WHO WITH"),
            ("It was good, thanks. On Saturday I went to the mountains with some friends, but it rained on Sunday. "
             "How about yours?", "BUT + the question back"),
        ],
        build=[
            ("Past simple: On Saturday I (go) to the cinema.", "On Saturday I went to the cinema."),
            ("Add WHO WITH: I went for dinner.", "I went for dinner with my colleagues."),
            ("Ask about their weekend: (anything fun)", "Did you do anything fun at the weekend?"),
            ("Quiet weekend, but longer: Nothing much.", "Nothing much, I just stayed in and cooked a big dinner."),
        ],
        questions=[
            ("How was your weekend?", "It was nice. I stayed in on Saturday and went out with friends on Sunday."),
            ("What did you do on Sunday evening?", "I watched a film and went to bed early."),
        ],
        speak=("It is Monday morning. Tell the tutor about your weekend: a short answer first, then "
               "where, when, who with - and ask about theirs with 'Did you ...?'."),
    ),
    _lesson(
        "en-t10", 3, 2, "B1", "Any plans for the weekend?",
        "talk about sure plans and 'maybe' plans, and make a plan together",
        words=[
            ("be going to", "a plan you decided", "... etmək niyyətində olmaq", "I'm going to visit my cousin."),
            ("might", "maybe", "bəlkə", "I might go to the cinema."),
            ("not sure yet", "I haven't decided", "hələ bilmirəm", "I'm not sure yet."),
            ("fancy", "want (informal)", "istəmək (danışıq)", "Do you fancy a drink on Friday?"),
            ("be up for", "want to join", "razı olmaq, həvəsli olmaq", "I'm up for it!"),
            ("free", "not busy", "boş, məşğul olmayan", "Are you free on Saturday?"),
        ],
        phrases=[
            ("Any plans for the weekend?", "the Friday question", "Həftəsonu üçün planın var?"),
            ("I'm meeting some friends on Saturday.", "a fixed plan", "Şənbə dostlarla görüşürəm."),
            ("I'm not sure yet. I might go to the cinema.", "a maybe plan", "Hələ bilmirəm. Bəlkə kinoya gedəm."),
            ("Are you free on Sunday?", "invite", "Bazar günü boşsan?"),
            ("Sounds good, I'm up for it!", "say yes", "Yaxşı fikirdir, razıyam!"),
        ],
        grammar={
            "name": "Plans: I'm meeting / I'm going to / I might",
            "rule": ("A plan with a time and people (arranged): present continuous - I'm meeting Anna on "
                     "Saturday. A plan you decided: be going to - I'm going to clean the flat. Not sure: "
                     "might - I might go out."),
            "table": ["arranged: I'm meeting Anna at seven.", "decided: I'm going to relax.",
                      "not sure: I might go to the cinema."],
            "examples": [("I'm meeting my cousin on Saturday afternoon.", ""),
                         ("I'm going to have a quiet Sunday.", ""),
                         ("I might go hiking if the weather is nice.", "")],
        },
        skills=["future_forms", "first_conditional"],
        partner_role="friend on Friday",
        dialogue=[
            ("partner", "Hey! Any plans for the weekend?"),
            ("learner", "I'm not sure yet. I might go to the cinema. How about you?"),
            ("partner", "It's my birthday on Saturday, so I'm having a small party. Are you free?"),
            ("learner", "Really? Happy early birthday! Yes, I'm free on Saturday."),
            ("partner", "Great! We're starting at seven. Do you fancy coming?"),
            ("learner", "Sounds good, I'm up for it! Should I bring anything?"),
        ],
        extend=[
            ("Nothing.", "the one-word answer"),
            ("I'm going to stay at home on Saturday.", "a plan + WHEN"),
            ("I'm going to stay at home on Saturday, but on Sunday I'm meeting some friends.", "BUT + an arranged plan"),
            ("I'm going to stay at home on Saturday, but on Sunday I'm meeting some friends, and we might go hiking. "
             "What about you?", "MIGHT + the question back"),
        ],
        build=[
            ("Arranged plan: (meet - my cousin - Saturday)", "I'm meeting my cousin on Saturday."),
            ("Not sure: I will go to the cinema. (make it 'maybe')", "I might go to the cinema."),
            ("Invite: (a drink - Friday - fancy)", "Do you fancy a drink on Friday?"),
            ("Add IF: I might go hiking. (the weather is nice)", "I might go hiking if the weather is nice."),
        ],
        questions=[
            ("Any plans for the weekend?", "I'm meeting some friends on Saturday, and on Sunday I might go to the gym."),
            ("Are you free tomorrow evening?", "Sorry, I'm working late tomorrow, but I'm free on Thursday."),
        ],
        speak=("Friday small talk: tell the tutor your weekend plans (arranged ones, decided ones and "
               "'might' ones), then make a plan together."),
    ),
    _lesson(
        "en-t11", 3, 3, "B1", "What's new? - catching up",
        "catch up with an old friend: your news, their news, and 'Have you heard...?'",
        words=[
            ("catch up", "talk about news after a long time", "xəbərləşmək", "Let's catch up soon!"),
            ("ages", "a very long time", "çoxdan, uzun müddət", "I haven't seen you for ages!"),
            ("just", "a very short time ago", "indicə, təzəcə", "I've just moved."),
            ("yet", "until now (questions, negatives)", "hələ", "Have you found a new flat yet?"),
            ("move", "change your home", "köçmək", "We've moved to a bigger flat."),
            ("same old", "nothing is different", "hər şey köhnə qaydada", "Oh, same old, same old."),
        ],
        phrases=[
            ("Long time no see!", "we haven't met for a long time", "Çoxdandır görüşmürük!"),
            ("What's new with you?", "tell me your news", "Nə var, nə yox?"),
            ("Not much, same old really.", "no news", "Elə bir şey yox, hər şey köhnə qaydada."),
            ("I've just moved to a new flat.", "your news", "Təzəcə yeni mənzilə köçmüşəm."),
            ("Have you heard that Anna's got a new job?", "share news", "Eşitmisən ki, Annanın yeni işi var?"),
        ],
        grammar={
            "name": "Present perfect for news",
            "rule": ("News without a time: have / has + past participle - I've moved, she's got a new job, "
                     "I've just started. With a time (last month, in May) use the past simple: I moved "
                     "last month. Question: Have you heard ...? Have you ... yet?"),
            "table": ["news: I've just moved. She's found a job.", "with a time: I moved in May.",
                      "Have you heard ...? · Have you ... yet?"],
            "examples": [("I've just started a Slovak course.", ""),
                         ("Have you heard that Mark is getting married?", ""),
                         ("We moved last month, and I love the new flat.", "")],
        },
        skills=["present_perfect", "past_simple"],
        partner_role="old friend on the street",
        dialogue=[
            ("partner", "Taleh! Long time no see! How are you?"),
            ("learner", "Hi! I know, it's been ages! I'm great. What's new with you?"),
            ("partner", "Not much, same old really. Still at the same company. And you?"),
            ("learner", "I've just moved to a new flat in Petržalka."),
            ("partner", "Oh nice! Have you heard that Anna's moved to London?"),
            ("learner", "No way! I haven't talked to her for ages. We should all catch up soon!"),
        ],
        extend=[
            ("I moved.", "the news"),
            ("I've just moved to a new flat.", "PRESENT PERFECT + JUST"),
            ("I've just moved to a new flat in Petržalka, because the old one was too small.", "WHERE + BECAUSE"),
            ("I've just moved to a new flat in Petržalka, because the old one was too small. "
             "What's new with you?", "the question back"),
        ],
        build=[
            ("News with 'just': I (start) a new course.", "I've just started a new course."),
            ("With a time: I (move) last month.", "I moved last month."),
            ("Share news: (Mark - get - a new car)", "Have you heard that Mark's got a new car?"),
            ("Ask with 'yet': (find a new job)", "Have you found a new job yet?"),
        ],
        questions=[
            ("What's new with you?", "Not much, but I've just started learning Slovak, and I love it."),
            ("Have you been anywhere nice recently?", "Yes, I've just been to Vienna for the weekend."),
        ],
        speak=("You meet an old friend. Tell them two pieces of news (with 'just' and with a time) and "
               "ask what is new with them - react to every answer."),
    ),
    _lesson(
        "en-t12", 3, 4, "B1", "You should try it! - tips and recommendations",
        "ask for and give tips about places, food and films, and say why",
        words=[
            ("recommend", "say something is good to try", "tövsiyə etmək", "I can recommend this place."),
            ("worth it", "good enough for the time or money", "dəyər", "It's a bit expensive, but it's worth it."),
            ("Have you been to ...?", "did you ever visit ...?", "... olmusan?", "Have you been to the castle?"),
            ("must-see", "something you have to see", "mütləq görülməli yer", "The old town is a must-see."),
            ("overrated", "not as good as people say", "şişirdilmiş", "Honestly, that restaurant is overrated."),
            ("definitely", "for sure", "mütləq", "You should definitely try it."),
        ],
        phrases=[
            ("Do you know any good places to eat around here?", "ask for a tip", "Buralarda yeməyə yaxşı yer bilirsən?"),
            ("You should definitely try the place by the river.", "give a tip", "Çayın yanındakı yeri mütləq sına."),
            ("Have you been to the old town?", "ask about experience", "Köhnə şəhərdə olmusan?"),
            ("It's a bit expensive, but it's worth it.", "a detail", "Bir az bahadır, amma dəyər."),
            ("Thanks for the tip!", "say thanks", "Məsləhət üçün sağ ol!"),
        ],
        grammar={
            "name": "You should ... / Have you been to ...?",
            "rule": ("Give advice with 'should' + verb: You should try the soup. Stronger: You should "
                     "definitely ... / You have to ... . Ask about experience with the present perfect: "
                     "Have you been to Baku? Have you tried plov?"),
            "table": ["You should try the soup.", "You should definitely see the old town.",
                      "Have you been to ...? · Have you tried ...?"],
            "examples": [("You should definitely try the goulash there.", ""),
                         ("Have you been to the Old City in Baku?", ""),
                         ("It's not cheap, but it's worth it.", "")],
        },
        skills=["advice_modals", "present_perfect"],
        partner_role="colleague who is new in the city",
        dialogue=[
            ("partner", "Do you know any good places to eat around here?"),
            ("learner", "Yes! You should definitely try the little restaurant by the river."),
            ("partner", "What kind of food do they have?"),
            ("learner", "Mostly Slovak food. It's a bit expensive, but it's worth it."),
            ("partner", "Great, thanks for the tip! Have you been to the castle yet?"),
            ("learner", "Yes, it's a must-see, especially at sunset. You should go this weekend."),
        ],
        extend=[
            ("The restaurant by the river.", "the short tip"),
            ("You should try the restaurant by the river.", "YOU SHOULD"),
            ("You should definitely try the restaurant by the river, because the food is amazing.", "BECAUSE + why"),
            ("You should definitely try the restaurant by the river, because the food is amazing. "
             "Have you been there yet?", "a question back"),
        ],
        build=[
            ("Give a tip: (try - the plov - in Baku)", "You should definitely try the plov in Baku."),
            ("Ask about experience: (be - to Vienna)", "Have you been to Vienna?"),
            ("Add 'but it's worth it': The museum is expensive.", "The museum is expensive, but it's worth it."),
            ("Disagree softly: That place is great. (overrated)", "Really? Honestly, I think it's a bit overrated."),
        ],
        questions=[
            ("What should a tourist see in Baku?", "You should definitely see the Old City, and walk on the Boulevard."),
            ("Can you recommend a good film?", "You should watch Interstellar - it's long, but it's worth it."),
        ],
        speak=("A colleague is new in the city. Recommend a restaurant, a place and a film, always say "
               "why - and ask about their favourite places too."),
    ),

    # ══ WEEK 4 - B1: university and work ═════════════════════════════════════
    _lesson(
        "en-t13", 4, 1, "B1", "First day at university",
        "meet other students: your subject, your year, and where things are",
        words=[
            ("major", "your main subject at university", "ixtisas", "My major is computer science."),
            ("first-year student", "a student in year one", "birinci kurs tələbəsi", "I'm a first-year student."),
            ("lecture", "a big class where a teacher talks", "mühazirə", "The first lecture is at nine."),
            ("timetable", "the plan of your classes", "dərs cədvəli", "Have you got the timetable yet?"),
            ("classmate", "a student in your class", "qrup yoldaşı", "We're classmates!"),
            ("campus", "the university area", "kampus", "The library is on the other side of the campus."),
        ],
        phrases=[
            ("What are you studying?", "the student question", "Nə oxuyursan?"),
            ("I'm studying computer science. I'm in my first year.", "subject + year", "İnformatika oxuyuram, birinci kursdayam."),
            ("Do you know where room B2 is?", "ask the way", "B2 otağının harada olduğunu bilirsən?"),
            ("Are you going to the maths lecture too?", "find a classmate", "Sən də riyaziyyat mühazirəsinə gedirsən?"),
            ("Shall we go together?", "an offer", "Birlikdə gedək?"),
        ],
        grammar={
            "name": "Indirect questions: Do you know where ...?",
            "rule": ("A polite question to a stranger starts with 'Do you know ...?' or 'Could you tell "
                     "me ...?', and then the normal sentence order: Where IS room B2? → Do you know where "
                     "room B2 IS? (NOT: where is room B2)."),
            "table": ["Where is the library? → Do you know where the library is?",
                      "When does it start? → Do you know when it starts?",
                      "Could you tell me where room B2 is?"],
            "examples": [("Do you know where the library is?", ""),
                         ("Do you know when the lecture starts?", ""),
                         ("Could you tell me where room B2 is?", "")],
        },
        skills=["word_order", "present_simple"],
        partner_role="student on the first day",
        dialogue=[
            ("partner", "Hi! Sorry, do you know where room B2 is?"),
            ("learner", "I think it's on the second floor. Are you going to the maths lecture too?"),
            ("partner", "Yes! So you're studying computer science?"),
            ("learner", "That's right, I'm in my first year. I'm Taleh, by the way."),
            ("partner", "Nice to meet you, I'm Mark. Shall we go together? We're classmates!"),
            ("learner", "Sure! Have you got the timetable yet? I haven't got it."),
        ],
        extend=[
            ("Computer science.", "the one-word answer"),
            ("I'm studying computer science.", "a full sentence"),
            ("I'm studying computer science at the Technical University, and I'm in my first year.", "WHERE + which year"),
            ("I'm studying computer science at the Technical University, and I'm in my first year. "
             "It's hard, but I love it. What are you studying?", "a feeling + the question back"),
        ],
        build=[
            ("Make it polite: Where is the library?", "Do you know where the library is?"),
            ("Make it polite: When does the lecture start?", "Do you know when the lecture starts?"),
            ("Subject + year: (economics - second year)", "I'm studying economics, and I'm in my second year."),
            ("Offer: (go to the lecture together)", "Shall we go to the lecture together?"),
        ],
        questions=[
            ("What did you study, or what are you studying?", "I studied computer science in Baku, and now I'm learning languages."),
            ("What was your favourite subject?", "My favourite subject was maths, because I like solving problems."),
        ],
        speak=("First day at university: the tutor is a new classmate. Ask the way politely, find out "
               "what they study and which year, and plan to go to the lecture together."),
    ),
    _lesson(
        "en-t14", 4, 2, "B1", "Exam stress - studying together",
        "talk about exams and how you feel, calm someone down and plan to study together",
        words=[
            ("stressed out", "very worried and tired", "çox stresli", "I'm so stressed out about the exam."),
            ("revise", "study again before an exam", "təkrar etmək (imtahana hazırlaşmaq)", "I need to revise tonight."),
            ("pass / fail", "get a good / bad result", "keçmək / kəsilmək", "I hope I pass."),
            ("notes", "what you wrote in class", "qeydlər, konspekt", "Can I borrow your notes?"),
            ("fingers crossed", "I hope it goes well", "uğurlar (ümid edirəm)", "Fingers crossed for tomorrow!"),
            ("You'll be fine.", "don't worry", "Hər şey yaxşı olacaq.", "Don't worry, you'll be fine."),
        ],
        phrases=[
            ("When's your exam?", "the question", "İmtahanın nə vaxtdır?"),
            ("On Friday. I'm so stressed out!", "a feeling", "Cümə günü. Çox stresliyəm!"),
            ("Have you started revising yet?", "a follow-up", "Artıq hazırlaşmağa başlamısan?"),
            ("Why don't we study together in the library?", "an offer", "Niyə kitabxanada birlikdə oxumayaq?"),
            ("Don't worry, you'll be fine. Fingers crossed!", "calm someone down", "Narahat olma, hər şey yaxşı olacaq. Uğurlar!"),
        ],
        grammar={
            "name": "If + present, will: If I revise, I'll pass.",
            "rule": ("For a real possibility in the future: If + present simple, will + verb. If I revise "
                     "tonight, I'll feel better. If you don't sleep, you won't remember anything. Suggest "
                     "with 'Why don't we ...?'"),
            "table": ["If I revise, I'll pass.", "If you don't sleep, you won't remember.",
                      "Why don't we study together?"],
            "examples": [("If we study together, it'll be easier.", ""),
                         ("If I pass this exam, I'll celebrate all weekend.", ""),
                         ("Why don't we meet in the library at ten?", "")],
        },
        skills=["first_conditional", "advice_modals"],
        partner_role="classmate before an exam",
        dialogue=[
            ("partner", "Hi! When's your maths exam?"),
            ("learner", "On Friday. I'm so stressed out! When's yours?"),
            ("partner", "Friday too. Have you started revising yet?"),
            ("learner", "A bit, but I don't understand everything. Can I borrow your notes?"),
            ("partner", "Sure. Why don't we study together in the library?"),
            ("learner", "Great idea! If we study together, it'll be much easier. Tomorrow at ten?"),
        ],
        extend=[
            ("I'm stressed.", "the short sentence"),
            ("I'm really stressed out about the exam.", "ABOUT + what"),
            ("I'm really stressed out about the maths exam, because I haven't revised much yet.", "BECAUSE + why"),
            ("I'm really stressed out about the maths exam, because I haven't revised much yet. "
             "Why don't we study together?", "an offer at the end"),
        ],
        build=[
            ("If + will: I revise tonight. I feel better.", "If I revise tonight, I'll feel better."),
            ("Suggest: (study - in the library)", "Why don't we study in the library?"),
            ("Calm them down: I'm so nervous!", "Don't worry, you'll be fine. Fingers crossed!"),
            ("Ask with 'yet': (start revising)", "Have you started revising yet?"),
        ],
        questions=[
            ("How do you usually prepare for an exam?", "I usually revise with my notes, and I study with a friend before the exam."),
            ("How do you feel before an exam?", "I usually feel stressed out, but if I revise well, I'm OK."),
        ],
        speak=("Exam week: the tutor is a nervous classmate. Talk about your exams and how you feel, "
               "calm them down and plan to study together with 'Why don't we ...?'."),
    ),
    _lesson(
        "en-t15", 4, 3, "B1", "New at work - the first day",
        "introduce yourself to colleagues, ask how long they've worked there and ask for help",
        words=[
            ("I've been here since ...", "from that time until now", "... bəri buradayam", "I've been here since Monday."),
            ("for", "a length of time", "... müddətində", "She's worked here for five years."),
            ("show someone around", "give a tour", "ətrafı göstərmək", "Can you show me around?"),
            ("department", "a part of a company", "şöbə", "I'm in the IT department."),
            ("settle in", "start to feel comfortable in a new place", "öyrəşmək, yerləşmək", "Are you settling in OK?"),
            ("so far", "until now", "hələlik", "So far, so good!"),
        ],
        phrases=[
            ("Hi, I'm Taleh. I'm new here.", "introduce yourself", "Salam, mən Talehəm. Burada yeniyəm."),
            ("Which department are you in?", "a work question", "Hansı şöbədəsən?"),
            ("How long have you worked here?", "the classic follow-up", "Nə vaxtdan burada işləyirsən?"),
            ("Could you show me where the kitchen is?", "ask for help", "Mətbəxin harada olduğunu göstərə bilərsən?"),
            ("So far, so good!", "the first days are OK", "Hələlik hər şey yaxşıdır!"),
        ],
        grammar={
            "name": "How long have you ...? - for / since",
            "rule": ("From the past until now: present perfect. How long have you worked here? I've worked "
                     "here FOR three years (a length of time). I've been here SINCE Monday (the start "
                     "point). NOT: I work here since three years."),
            "table": ["How long have you worked here?", "for: for three years · for a week",
                      "since: since Monday · since 2024"],
            "examples": [("I've worked here for three years.", ""),
                         ("I've only been here since Monday.", ""),
                         ("How long have you lived in Bratislava?", "")],
        },
        skills=["present_perfect", "present_perfect_continuous"],
        partner_role="colleague on your first day",
        dialogue=[
            ("partner", "Hi! Are you new here?"),
            ("learner", "Yes, I've been here since Monday. I'm Taleh, I'm in the IT department."),
            ("partner", "Welcome! I'm Zuzana, from marketing. Are you settling in OK?"),
            ("learner", "So far, so good! How long have you worked here?"),
            ("partner", "For three years now. Come on, I'll show you around."),
            ("learner", "Thanks, that's really kind. Could you show me where the kitchen is first?"),
        ],
        extend=[
            ("I'm new.", "the short sentence"),
            ("Hi, I'm Taleh, I'm new here.", "your name"),
            ("Hi, I'm Taleh, I'm new here - I've been in the IT department since Monday.", "WHERE + SINCE"),
            ("Hi, I'm Taleh, I'm new here - I've been in the IT department since Monday. "
             "How long have you worked here?", "the question back"),
        ],
        build=[
            ("for or since: I've worked here (two years).", "I've worked here for two years."),
            ("for or since: I've been here (Monday).", "I've been here since Monday."),
            ("Ask: (live - in Bratislava - how long)", "How long have you lived in Bratislava?"),
            ("Ask for help politely: Show me the printer.", "Could you show me where the printer is, please?"),
        ],
        questions=[
            ("How long have you worked in your job?", "I've worked there for two years, since I moved here."),
            ("How was your first day at your last job?", "It was a bit stressful, but my colleagues were really friendly."),
        ],
        speak=("First day at work: the tutor plays two colleagues. Introduce yourself, ask about their "
               "department and how long they've worked there, and ask them to show you around."),
    ),
    _lesson(
        "en-t16", 4, 4, "B1", "By the coffee machine - office chit-chat",
        "make light office small talk: busy days, lunch plans and Friday feelings",
        words=[
            ("swamped", "with far too much work", "işə qərq olmuş", "I'm swamped this week."),
            ("deadline", "the last day to finish work", "son tarix", "The deadline is on Friday."),
            ("grab lunch", "get lunch quickly", "tez nahar etmək", "Do you want to grab lunch?"),
            ("take a break", "stop working for a short time", "fasilə vermək", "Let's take a break."),
            ("Thank God it's Friday!", "happy that the week is over", "Şükür ki, cümədir!", "Thank God it's Friday!"),
            ("How's the project going?", "is the work OK?", "Layihə necə gedir?", "How's the new project going?"),
        ],
        phrases=[
            ("Busy day?", "the office opener", "Məşğul gündür?"),
            ("I'm swamped - the deadline is tomorrow.", "a detail", "İşə qərq olmuşam - son tarix sabahdır."),
            ("How's the project going?", "a follow-up", "Layihə necə gedir?"),
            ("Do you want to grab lunch later?", "an invitation", "Sonra nahar etməyə gedək?"),
            ("Thank God it's Friday! Any plans?", "end of the week", "Şükür ki, cümədir! Planın var?"),
        ],
        grammar={
            "name": "Present continuous for now: I'm working on ...",
            "rule": ("For what is happening now or these days use am / is / are + -ing: I'm working on a "
                     "new project. How's it going? It's going well. For every day use the present simple: "
                     "I usually have lunch at twelve."),
            "table": ["now / these days: I'm working on a new app.", "every day: I usually start at nine.",
                      "How's it going? - It's going well."],
            "examples": [("I'm working on a new project this month.", ""),
                         ("We're having a lot of meetings this week.", ""),
                         ("I usually take a break at eleven.", "")],
        },
        skills=["present_simple", "adverbs_frequency"],
        partner_role="colleague at the coffee machine",
        dialogue=[
            ("partner", "Hey, Taleh. Busy day?"),
            ("learner", "I'm swamped! The deadline is tomorrow. How about you?"),
            ("partner", "Not too bad. How's the new project going?"),
            ("learner", "It's going well, but we're having a lot of meetings this week."),
            ("partner", "Ugh, meetings! Do you want to grab lunch later?"),
            ("learner", "Sure, I need a break. Twelve thirty?"),
        ],
        extend=[
            ("Busy.", "the one-word answer"),
            ("I'm really busy today.", "a full sentence"),
            ("I'm really busy today, because I'm working on a new app.", "BECAUSE + present continuous"),
            ("I'm really busy today, because I'm working on a new app, and the deadline is tomorrow. "
             "How's your day going?", "AND + the question back"),
        ],
        build=[
            ("Now: I (work) on a new project this month.", "I'm working on a new project this month."),
            ("Every day: I (usually / start) at nine.", "I usually start at nine."),
            ("Invite: (grab lunch - later)", "Do you want to grab lunch later?"),
            ("Friday feeling: (it's Friday - plans?)", "Thank God it's Friday! Any plans for the weekend?"),
        ],
        questions=[
            ("What are you working on these days?", "I'm working on a new app, and it's going really well."),
            ("What do you usually do in your breaks?", "I usually grab a coffee and chat with my colleagues."),
        ],
        speak=("Coffee machine chat: the tutor is a colleague. Talk about your busy day, what you're "
               "working on, and invite them to lunch - then do the Friday version."),
    ),

    # ══ WEEK 5 - B1: small talk everywhere ═══════════════════════════════════
    _lesson(
        "en-t17", 5, 1, "B1", "At a party - meeting new people",
        "introduce yourself and others, find out how people know the host, and join a group",
        words=[
            ("host", "the person who gives the party", "ev sahibi", "How do you know the host?"),
            ("introduce", "tell people each other's names", "tanış etmək", "Let me introduce you to Mark."),
            ("go way back", "know each other for a long time", "çoxdankı tanış olmaq", "Anna and I go way back."),
            ("mutual friend", "a friend of both people", "ortaq dost", "We have a mutual friend."),
            ("mingle", "move and talk to many people", "hamı ilə ünsiyyət qurmaq", "I should mingle a bit."),
            ("I don't think we've met.", "a polite start", "Deyəsən, tanış deyilik.", "Hi, I don't think we've met."),
        ],
        phrases=[
            ("Hi, I don't think we've met. I'm Taleh.", "start with a stranger", "Salam, deyəsən tanış deyilik. Mən Talehəm."),
            ("So, how do you know Anna?", "the party question", "Bəs Annanı haradan tanıyırsan?"),
            ("We work together. / We go way back.", "answers", "Birlikdə işləyirik. / Çoxdankı tanışıq."),
            ("Let me introduce you to my friend Mark.", "introduce others", "Səni dostum Markla tanış edim."),
            ("Mind if I join you?", "join a group", "Qoşulsam, etirazın yoxdur?"),
        ],
        grammar={
            "name": "How do you know ...? - question words",
            "rule": ("Keep a party chat going with open questions (what, where, how, why), not yes / no "
                     "questions. NOT: Do you know Anna? (Yes.) → BETTER: How do you know Anna? How long "
                     "have you known her? What do you do?"),
            "table": ["yes / no: Do you know Anna? → Yes.", "open: How do you know Anna? → a story",
                      "How long have you known each other?"],
            "examples": [("How do you know the host?", ""),
                         ("How long have you known each other?", ""),
                         ("What brings you to Bratislava?", "")],
        },
        skills=["word_order", "present_perfect"],
        partner_role="guest at a party",
        dialogue=[
            ("partner", "Hi there!"),
            ("learner", "Hi, I don't think we've met. I'm Taleh."),
            ("partner", "Nice to meet you, I'm Lucy. So, how do you know Anna?"),
            ("learner", "We work together. How about you? How do you know her?"),
            ("partner", "Oh, we go way back - we were at school together."),
            ("learner", "That's lovely! Let me introduce you to my friend Mark - he's from London too."),
        ],
        extend=[
            ("From work.", "the short answer"),
            ("We know each other from work.", "a full sentence"),
            ("We know each other from work - we've been in the same team for a year.", "HOW LONG"),
            ("We know each other from work - we've been in the same team for a year. "
             "How do you know Anna?", "the open question back"),
        ],
        build=[
            ("Make it open: Do you know the host?", "How do you know the host?"),
            ("Start with a stranger: (not met - your name)", "Hi, I don't think we've met. I'm Taleh."),
            ("Introduce: (my friend Mark - from London)", "Let me introduce you to my friend Mark - he's from London."),
            ("Ask to join: (a group is talking)", "Hi, mind if I join you?"),
        ],
        questions=[
            ("How do you know your best friend?", "We go way back - we met at school in Baku twenty years ago."),
            ("What do you usually talk about at parties?", "Usually work, travel and food, and sometimes football."),
        ],
        speak=("At a party the tutor plays three guests. Introduce yourself, find out how each one knows "
               "the host with open questions, and introduce two of them to each other."),
    ),
    _lesson(
        "en-t18", 5, 2, "B1", "On the train - talking to a stranger",
        "start a polite conversation with a stranger on a trip and keep it going",
        words=[
            ("Do you mind if ...?", "is it OK if ...?", "Etirazınız yoxdur ki ...?", "Do you mind if I sit here?"),
            ("on business", "travelling for work", "iş üçün", "I'm travelling on business."),
            ("on holiday", "travelling for fun", "tətildə", "Are you here on holiday?"),
            ("delayed", "late", "gecikmiş", "The train is delayed by twenty minutes."),
            ("scenery", "the nature you can see", "mənzərə", "The scenery is beautiful."),
            ("heading", "going (to)", "(bir yerə) getmək", "Where are you heading?"),
        ],
        phrases=[
            ("Excuse me, do you mind if I sit here?", "ask for the seat", "Bağışlayın, burada otursam, etirazınız yoxdur?"),
            ("Where are you heading?", "the travel question", "Hara gedirsiniz?"),
            ("Are you travelling for work or pleasure?", "a follow-up", "İş üçün, yoxsa istirahət üçün səyahət edirsiniz?"),
            ("The scenery is amazing, isn't it?", "a comment", "Mənzərə möhtəşəmdir, elə deyil?"),
            ("Enjoy the rest of your trip!", "a nice ending", "Səfərinizin qalanından zövq alın!"),
        ],
        grammar={
            "name": "Polite requests: Do you mind if I ...? / Would you mind ...ing?",
            "rule": ("To ask for permission: Do you mind if I + present (Do you mind if I open the window?). "
                     "Answer 'No, not at all' = yes, it's OK! To ask someone to do something: Would you "
                     "mind + -ing (Would you mind moving your bag?)."),
            "table": ["Do you mind if I sit here? - No, not at all. (= OK!)",
                      "Would you mind moving your bag?", "Could you tell me when we get to Žilina?"],
            "examples": [("Do you mind if I open the window?", ""),
                         ("Would you mind watching my bag for a minute?", ""),
                         ("No, not at all - go ahead.", "")],
        },
        skills=["modals_basic", "gerund_infinitive"],
        partner_role="older passenger on a train",
        dialogue=[
            ("learner", "Excuse me, do you mind if I sit here?"),
            ("partner", "No, not at all, go ahead. Where are you heading?"),
            ("learner", "To Košice, on business. How about you?"),
            ("partner", "I'm going home to Poprad. You're not from Slovakia, are you?"),
            ("learner", "No, I'm from Azerbaijan, but I've lived here for two years. The scenery is amazing, isn't it?"),
            ("partner", "Wait until you see the Tatras - in about an hour!"),
            ("learner", "Really? I can't wait. I've heard they're beautiful."),
        ],
        extend=[
            ("Košice.", "the short answer"),
            ("I'm going to Košice.", "a full sentence"),
            ("I'm going to Košice on business, for two days.", "WHY + HOW LONG"),
            ("I'm going to Košice on business, for two days, and it's my first time there. "
             "Where are you heading?", "a detail + the question back"),
        ],
        build=[
            ("Ask politely: I want to open the window.", "Do you mind if I open the window?"),
            ("Ask someone: Move your bag.", "Would you mind moving your bag, please?"),
            ("Say yes politely: Do you mind if I sit here?", "No, not at all - go ahead."),
            ("Follow-up: (work or pleasure)", "Are you travelling for work or pleasure?"),
        ],
        questions=[
            ("Where did you travel last time?", "The last time I travelled was to Vienna, by train, for the weekend."),
            ("Do you like talking to strangers when you travel?", "Yes, if they're friendly - you can hear really interesting stories."),
        ],
        speak=("Train role play: the tutor is a stranger. Ask for the seat politely, find out where they "
               "are heading and why, talk about the scenery - and end nicely."),
    ),
    _lesson(
        "en-t19", 5, 3, "B1", "Compliments and light opinions",
        "give compliments with a detail, share a light opinion, agree and disagree softly",
        words=[
            ("suit", "look good on someone", "yaraşmaq", "That colour really suits you."),
            ("I love your ...", "a friendly compliment", "...-nı çox bəyənirəm", "I love your jacket!"),
            ("to be honest", "saying what I really think", "düzünü desəm", "To be honest, I didn't like the end."),
            ("I see what you mean, but ...", "a soft 'I disagree'", "Nə demək istədiyini başa düşürəm, amma ...",
             "I see what you mean, but I think it was too long."),
            ("fair point", "you are right about that", "haqlı fikirdir", "Fair point - the actors were great."),
            ("What did you think of ...?", "what's your opinion?", "... haqqında nə düşündün?", "What did you think of the film?"),
        ],
        phrases=[
            ("I love your jacket! Where did you get it?", "a compliment + a question", "Gödəkçəni çox bəyəndim! Haradan almısan?"),
            ("Thanks, that's really kind of you.", "take a compliment", "Sağ ol, çox naziksən."),
            ("What did you think of the film?", "ask an opinion", "Film haqqında nə düşündün?"),
            ("To be honest, I thought it was a bit long.", "an honest opinion", "Düzünü desəm, məncə bir az uzun idi."),
            ("I see what you mean, but the ending was great.", "disagree softly", "Nə demək istədiyini başa düşürəm, amma sonluq əla idi."),
        ],
        grammar={
            "name": "Soft opinions: I think / To be honest / I see what you mean, but",
            "rule": ("Small talk opinions are light and friendly. Start with 'I think' or 'To be honest'. "
                     "To disagree, first agree a little: 'I see what you mean, but ...' or 'Fair point, "
                     "but ...'. Avoid 'You're wrong.'"),
            "table": ["give: I think ... / To be honest, ...", "agree: Absolutely. / Fair point.",
                      "disagree softly: I see what you mean, but ..."],
            "examples": [("To be honest, I thought the film was a bit slow.", ""),
                         ("I see what you mean, but I really liked the music.", ""),
                         ("Fair point - the food there is expensive.", "")],
        },
        skills=["discourse_markers", "linking_words"],
        partner_role="friend after a film",
        dialogue=[
            ("partner", "Hey Taleh, I love your jacket! Is it new?"),
            ("learner", "Thanks, that's really kind of you! Yes, I got it last week. So, what did you think of the film?"),
            ("partner", "To be honest, I thought it was a bit long."),
            ("learner", "I see what you mean, but the ending was amazing, wasn't it?"),
            ("partner", "Fair point, the ending was great. And the actors were brilliant."),
            ("learner", "Absolutely. Let's watch the next one together!"),
        ],
        extend=[
            ("It was good.", "the short opinion"),
            ("I think it was a really good film.", "I THINK"),
            ("I think it was a really good film, especially the ending.", "ESPECIALLY + a detail"),
            ("I think it was a really good film, especially the ending, but to be honest it was a bit long. "
             "What did you think?", "BUT + the question back"),
        ],
        build=[
            ("Compliment + question: (nice bag)", "I love your bag! Where did you get it?"),
            ("Take a compliment: Your English is really good!", "Thanks, that's really kind of you!"),
            ("Disagree softly: The film was boring. (the music)", "I see what you mean, but I really liked the music."),
            ("Honest opinion: The restaurant was bad.", "To be honest, I didn't really like the restaurant."),
        ],
        questions=[
            ("What do you think of Bratislava?", "I think it's a lovely city - it's small, but there's a lot to do."),
            ("What did you think of the last film you saw?", "To be honest, it was a bit slow, but the actors were great."),
        ],
        speak=("The tutor gives you compliments and five opinions (a film, the city, food, the weather, "
               "sport). Take the compliments, give your own, and agree or disagree softly."),
    ),
    _lesson(
        "en-t20", 5, 4, "B1", "Anyway, I'd better go - ending the talk",
        "end a conversation politely with a reason, a kind word and a plan",
        words=[
            ("anyway", "a signal: the talk is ending", "neyse, hər halda", "Anyway, I'd better get going."),
            ("I'd better", "I should (now)", "yaxşısı budur ki ...", "I'd better go - my bus is coming."),
            ("get going", "leave", "yola düşmək, getmək", "I should get going."),
            ("It was nice talking to you.", "a kind goodbye", "Səninlə danışmaq xoş idi.", "It was nice talking to you!"),
            ("keep in touch", "stay in contact", "əlaqə saxlamaq", "Let's keep in touch!"),
            ("Say hi to ...", "give my hello to ...", "... salam söylə", "Say hi to your family!"),
        ],
        phrases=[
            ("Anyway, I'd better get going.", "the signal", "Neyse, yaxşısı budur gedim."),
            ("I've got a train at five.", "the reason", "Saat beşdə qatarım var."),
            ("It was really nice talking to you!", "a kind word", "Səninlə danışmaq çox xoş idi!"),
            ("Let's catch up properly soon.", "a plan", "Tezliklə yaxşıca görüşüb danışaq."),
            ("Take care! Say hi to your family!", "the goodbye", "Özünü qoru! Ailənə salam söylə!"),
        ],
        grammar={
            "name": "Ending a talk: signal + reason + kind word + plan",
            "rule": ("Don't just walk away. 1) A signal: Anyway, ... / Right, ... 2) A reason: I'd better "
                     "go, I've got a meeting. 3) A kind word: It was great to see you. 4) A plan: Let's "
                     "catch up soon / See you on Monday. 'I'd better' = I had better + verb."),
            "table": ["signal: Anyway, ... / Right, ...", "reason: I'd better go - I've got a meeting.",
                      "kind word + plan: It was great to see you. Let's catch up soon!"],
            "examples": [("Anyway, I'd better go - I've got a meeting at three.", ""),
                         ("It was really nice talking to you.", ""),
                         ("Let's keep in touch - send me a message!", "")],
        },
        skills=["modals_basic", "discourse_markers"],
        partner_role="friend you met in the city",
        dialogue=[
            ("partner", "...and then we spent the whole day in Vienna."),
            ("learner", "That sounds amazing! Anyway, I'd better get going - I've got a train at five."),
            ("partner", "Oh, of course! It was great to see you."),
            ("learner", "You too! It was really nice talking to you. Let's catch up properly soon."),
            ("partner", "Definitely. Say hi to your family!"),
            ("learner", "I will. Take care, and keep in touch!"),
        ],
        extend=[
            ("I have to go.", "the short sentence"),
            ("Anyway, I'd better get going.", "ANYWAY - the signal"),
            ("Anyway, I'd better get going - I've got a train at five.", "the reason"),
            ("Anyway, I'd better get going - I've got a train at five. It was really nice talking to you - "
             "let's catch up soon!", "a kind word + a plan"),
        ],
        build=[
            ("Signal + reason: (go - a meeting at three)", "Anyway, I'd better go - I've got a meeting at three."),
            ("A kind word: (nice - talking to you)", "It was really nice talking to you."),
            ("A plan: (catch up - next week)", "Let's catch up next week!"),
            ("The whole ending in one: (anyway - bus - nice to see you - keep in touch)",
             "Anyway, I'd better go - my bus is coming. It was nice to see you, let's keep in touch!"),
        ],
        questions=[
            ("How do you end a chat with a neighbour when you're in a hurry?",
             "Sorry, I'd better run - I'm late for work. Have a nice day!"),
            ("What do you say to a friend at the end of a meeting?",
             "It was great to see you! Let's catch up soon, and say hi to your family."),
        ],
        speak=("Final small talk: one whole conversation with the tutor from 'How's it going?' to "
               "'Take care!' - the weather, work, the weekend, plans, an opinion and a polite ending."),
    ),
]


COURSE = {
    "id": "english_small_talk",
    "language": "english",
    "about": ("Learn English through small talk: the short, friendly chats of every day - how are you, "
              "the weather, work, the weekend, plans and news - in a café, a shop, at university, at "
              "work and on a train. A2 to B1 in five weeks."),
    "learner": ("The learner speaks basic English (A2) and learns to speak through SMALL TALK: short "
                "friendly conversations with neighbours, colleagues, classmates and strangers. The method "
                "is one rule: never a one-word answer. React first (Really? That's great! Oh no!), answer, "
                "add one small detail and send the question back (How about you?). Always push them to "
                "keep the talk going and to make short answers longer."),
    "title": "English · A2 → B1 · Small talk",
    "outcomes": [
        "Answer 'How's it going?' and any small talk question with a detail - and ask back",
        "Start a chat with anyone: the weather with a question tag, work, free time",
        "React to news naturally: No way! That's great! Oh no, I'm sorry to hear that.",
        "Talk about your weekend, your plans and your news (past simple, going to, present perfect)",
        "Chat anywhere: a café, a shop, university, a new job, a party, a train",
        "Give compliments and soft opinions, and end a conversation politely",
    ],
    "weeks": [
        {"week": 1, "title": "The small talk basics", "band": "A2"},
        {"week": 2, "title": "Everyday chats", "band": "A2"},
        {"week": 3, "title": "Weekends, plans and news", "band": "B1"},
        {"week": 4, "title": "University and work", "band": "B1"},
        {"week": 5, "title": "Small talk everywhere", "band": "B1"},
    ],
    "lessons": LESSONS,
}
