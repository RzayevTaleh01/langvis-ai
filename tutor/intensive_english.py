"""
tutor/intensive_english.py - the English course: phrasal verbs for daily
speaking, A2 to B1+ in 5 weeks.

One aim: to speak about everyday life the way people really do - with
phrasal verbs - and to make every sentence GROW. Each lesson gives the learner
a handful of everyday phrasal verbs, then shows how one short sentence with
them becomes a long, natural one: add when, where, who with, why, and what
happened next. Weeks 1-2 are A2 (my day, people), weeks 3-4 are B1 (problems,
stories, feelings, opinions), week 5 is B1+ (fluent daily speaking).
Everything is explained in simple English, with the Azerbaijani translation
on the board.

Every lesson has the same parts as the Slovak course, with two differences:
instead of translating, the learner BUILDS sentences (uses the phrasal verb,
makes a short sentence longer), and a "Longer sentences" part shows one
sentence growing step by step before they grow their own.
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
        # One short sentence, growing part by part: (the sentence now, what was added).
        "extend": [[{"text": text, "how": how} for text, how in extend]],
        "translate": [],
        "build": [{"task": task, "answer": answer} for task, answer in build],
        "questions": [{"q": q, "meaning": "", "example": ex} for q, ex in questions],
        "speak": speak,
    }


LESSONS: list[dict] = [
    # ══ WEEK 1 - A2: my day ══════════════════════════════════════════════════
    _lesson(
        "en-p01", 1, 1, "A2", "Morning: wake up, get up, put on",
        "say what you do every morning and add WHEN you do it",
        words=[
            ("wake up", "stop sleeping", "oyanmaq", "I wake up at seven."),
            ("get up", "leave your bed", "yataqdan qalxmaq", "I get up ten minutes later."),
            ("put on", "start wearing clothes", "geyinmək (paltarı)", "I put on my jacket."),
            ("turn off", "stop a machine or light", "söndürmək", "I turn off the alarm."),
            ("hurry up", "do it faster", "tələsmək", "Hurry up, the bus is coming!"),
            ("run late", "be in danger of being late", "gecikmək üzrə olmaq", "I'm running late today."),
        ],
        phrases=[
            ("I usually wake up at seven.", "your usual time", "Adətən saat yeddidə oyanıram."),
            ("I don't get up straight away.", "not at once", "Dərhal qalxmıram."),
            ("I put on my clothes and have breakfast.", "two actions", "Paltarımı geyinib səhər yeməyi yeyirəm."),
            ("Sorry, I'm running late.", "a short message", "Bağışla, gecikirəm."),
            ("I have to hurry up in the mornings.", "a need", "Səhərlər tələsməli oluram."),
        ],
        grammar={
            "name": "Phrasal verb + WHEN",
            "rule": ("A phrasal verb is a verb + a small word (up, on, off). The small word changes the "
                     "meaning: get = receive, get up = leave your bed. To make the sentence longer, add "
                     "WHEN at the end: at seven, early, every day, before work."),
            "table": ["I + phrasal verb + when", "I wake up + at seven.", "I get up + early on Mondays."],
            "examples": [("I wake up at seven every day.", ""),
                         ("I get up early on weekdays.", ""),
                         ("I put on my coat before I go out.", "")],
        },
        skills=["phrasal_verbs", "present_simple", "adverbs_frequency"],
        partner_role="friend",
        dialogue=[
            ("partner", "What time do you wake up?"),
            ("learner", "I usually wake up at seven."),
            ("partner", "Do you get up straight away?"),
            ("learner", "No, I turn off the alarm and sleep for five more minutes."),
            ("partner", "So you are always in a hurry?"),
            ("learner", "Yes, I often run late, so I have to hurry up."),
        ],
        extend=[
            ("I wake up.", "the short sentence"),
            ("I wake up at seven.", "WHEN"),
            ("I usually wake up at seven on weekdays.", "HOW OFTEN + which days"),
            ("I usually wake up at seven on weekdays, but I get up at nine on Sundays.", "BUT + a contrast"),
        ],
        build=[
            ("Make it longer with WHEN: I get up.", "I get up at half past six."),
            ("Use 'put on': I wear my jacket. I go out.", "I put on my jacket and go out."),
            ("Use 'turn off' and 'every morning': I stop the alarm.", "I turn off the alarm every morning."),
            ("Use 'run late' and 'so': I am late. I take a taxi.", "I'm running late, so I'm taking a taxi."),
        ],
        questions=[
            ("What time do you wake up, and when do you get up?", "I wake up at seven, but I get up at quarter past."),
            ("What do you do first in the morning?", "First I turn off the alarm, then I put on the kettle."),
        ],
        speak="Describe your morning in 5 sentences. Use a phrasal verb and WHEN in every sentence.",
    ),
    _lesson(
        "en-p02", 1, 2, "A2", "Going out: set off, get on, get off",
        "say how you go to work or school and add WHERE and HOW",
        words=[
            ("go out", "leave your home", "evdən çıxmaq", "I go out at eight."),
            ("set off", "start a trip", "yola düşmək", "We set off early."),
            ("get on", "enter a bus or train", "(avtobusa) minmək", "I get on the bus at the corner."),
            ("get off", "leave a bus or train", "(avtobusdan) düşmək", "I get off at the third stop."),
            ("pick up", "collect someone or something", "götürmək, dalınca getmək", "I pick up my son from school."),
            ("drop off", "take someone somewhere and leave them", "aparıb qoymaq, düşürmək", "I drop off my daughter at school."),
        ],
        phrases=[
            ("I set off for work at eight.", "starting the journey", "Saat səkkizdə işə yola düşürəm."),
            ("I get on the bus near my house.", "where you get on", "Evimin yaxınlığında avtobusa minirəm."),
            ("I get off at the last stop.", "where you get off", "Son dayanacaqda düşürəm."),
            ("Can you pick me up at six?", "a request", "Məni saat altıda götürə bilərsən?"),
            ("I drop the kids off on my way to work.", "on the way", "İşə gedərkən uşaqları düşürürəm."),
        ],
        grammar={
            "name": "Phrasal verb + WHERE + HOW",
            "rule": ("After the phrasal verb add WHERE (at the corner, near my house, at school) and HOW "
                     "(by bus, on foot, by car). Order: verb + where + how + when: "
                     "'I go to work by bus at eight.'"),
            "table": ["verb + where + how + when", "I get on the bus + near my house + at eight."],
            "examples": [("I set off for work by car at eight.", ""),
                         ("I get off the bus near the office.", ""),
                         ("I pick up my son from school at four.", "")],
        },
        skills=["phrasal_verbs", "prepositions", "word_order"],
        partner_role="new colleague",
        dialogue=[
            ("partner", "How do you get to work?"),
            ("learner", "I go by bus. I get on near my house."),
            ("partner", "Where do you get off?"),
            ("learner", "I get off at the stop next to the office."),
            ("partner", "Do you have children?"),
            ("learner", "Yes, I drop them off at school on my way to work."),
        ],
        extend=[
            ("I get on the bus.", "the short sentence"),
            ("I get on the bus near my house.", "WHERE"),
            ("I get on the bus near my house at eight.", "WHEN"),
            ("I get on the bus near my house at eight and get off next to the office.", "AND + the next action"),
        ],
        build=[
            ("Add WHERE: I get off the bus.", "I get off the bus near the park."),
            ("Use 'pick up' + WHERE + WHEN: I collect my son.", "I pick up my son from school at four."),
            ("Use 'set off' and 'by car': I start my trip to work.", "I set off for work by car."),
            ("Join with 'and': I drop off my kids. I go to the office.", "I drop off my kids and go to the office."),
        ],
        questions=[
            ("How do you get to work or school?", "I set off at eight and go by bus. I get off near the office."),
            ("Who picks you up when you need a lift?", "My brother picks me up after work on Fridays."),
        ],
        speak="Describe your trip from home to work or school, step by step, with at least four phrasal verbs.",
    ),
    _lesson(
        "en-p03", 1, 3, "A2", "Evening at home: come back, turn on, tidy up",
        "describe your evening with two or three actions in one sentence",
        words=[
            ("come back", "return", "qayıtmaq", "I come back home at six."),
            ("take off", "remove clothes or shoes", "çıxarmaq (paltarı)", "I take off my shoes at the door."),
            ("sit down", "take a seat", "oturmaq", "I sit down on the sofa."),
            ("turn on", "start a machine or light", "yandırmaq, açmaq", "I turn on the TV."),
            ("tidy up", "make a room clean and in order", "yığışdırmaq", "I tidy up the kitchen after dinner."),
            ("go to bed", "start sleeping for the night", "yatmağa getmək", "I go to bed at eleven."),
        ],
        phrases=[
            ("When I come back home, I take off my shoes.", "two actions with when", "Evə qayıdanda ayaqqabılarımı çıxarıram."),
            ("I sit down and relax for a while.", "resting", "Oturub bir az dincəlirəm."),
            ("I turn on some music while I cook.", "at the same time", "Yemək bişirərkən musiqi açıram."),
            ("After dinner I tidy up the kitchen.", "an order of actions", "Şam yeməyindən sonra mətbəxi yığışdırıram."),
            ("I usually go to bed around eleven.", "about a time", "Adətən təxminən on birdə yatıram."),
        ],
        grammar={
            "name": "Joining actions: and, then, after that, when",
            "rule": ("Put several actions in one sentence: 'I come back, take off my shoes and sit down.' "
                     "Use then / after that for the next step, and when + action, action: "
                     "'When I come back, I turn on the lights.'"),
            "table": ["action, action and action", "When + action 1, action 2",
                      "action 1, then action 2"],
            "examples": [("I come back, take off my shoes and sit down.", ""),
                         ("When I come back home, I turn on the lights.", ""),
                         ("I have dinner, then I tidy up the kitchen.", "")],
        },
        skills=["phrasal_verbs", "linking_words", "present_simple"],
        partner_role="flatmate",
        dialogue=[
            ("partner", "What time do you come back from work?"),
            ("learner", "I usually come back at six."),
            ("partner", "What do you do first?"),
            ("learner", "I take off my shoes, sit down and have a cup of tea."),
            ("partner", "And after dinner?"),
            ("learner", "I tidy up the kitchen, then I turn on the TV."),
        ],
        extend=[
            ("I come back.", "the short sentence"),
            ("I come back home at six.", "WHERE + WHEN"),
            ("When I come back home at six, I take off my shoes.", "WHEN + a second action"),
            ("When I come back home at six, I take off my shoes and sit down for a while.", "AND + a third action"),
        ],
        build=[
            ("Join with 'when': I come back. I turn on the lights.", "When I come back, I turn on the lights."),
            ("Put three actions in one sentence: take off my coat / sit down / turn on the TV.", "I take off my coat, sit down and turn on the TV."),
            ("Use 'then': I have dinner. I tidy up.", "I have dinner, then I tidy up."),
            ("Make it longer with WHEN: I go to bed.", "I go to bed at around eleven."),
        ],
        questions=[
            ("What do you do when you come back home?", "When I come back home, I take off my shoes and make some tea."),
            ("Who tidies up in your home?", "I tidy up the kitchen and my husband tidies up the living room."),
        ],
        speak="Tell the tutor about your evening yesterday in present simple as a routine: at least three sentences with two or three actions each.",
    ),
    _lesson(
        "en-p04", 1, 4, "A2", "Free time: hang out, eat out, stay in",
        "talk about your weekend and add WHO WITH and WHY",
        words=[
            ("hang out", "spend free time with someone", "vaxt keçirmək", "I hang out with my friends."),
            ("eat out", "eat in a restaurant", "bayırda (restoranda) yemək", "We eat out on Fridays."),
            ("stay in", "stay at home", "evdə qalmaq", "I stay in when it rains."),
            ("chill out", "relax", "dincəlmək", "I chill out on Sunday mornings."),
            ("go out", "go to a place for fun", "gəzməyə çıxmaq", "We go out on Saturday nights."),
            ("sleep in", "sleep later than usual", "gec oyanmaq, çox yatmaq", "I sleep in on Sundays."),
        ],
        phrases=[
            ("I like to hang out with my friends at the weekend.", "who with", "Həftəsonu dostlarımla vaxt keçirməyi xoşlayıram."),
            ("We sometimes eat out because we don't want to cook.", "a reason", "Bəzən bayırda yeyirik, çünki yemək bişirmək istəmirik."),
            ("If it rains, I stay in and watch films.", "a condition", "Yağış yağsa, evdə qalıb film izləyirəm."),
            ("On Sundays I sleep in and chill out.", "a lazy day", "Bazar günləri gec oyanıb dincəlirəm."),
            ("Do you want to go out tonight?", "an invitation", "Bu axşam gəzməyə çıxmaq istəyirsən?"),
        ],
        grammar={
            "name": "Phrasal verb + WHO WITH + WHY",
            "rule": ("Add who with (with my friends, with my family, on my own) and why with because: "
                     "'I stay in on Sundays because I'm tired.' The reason makes the sentence longer AND "
                     "more interesting."),
            "table": ["verb + with + who", "... because + reason", "I hang out + with my cousins + because they live nearby."],
            "examples": [("I hang out with my cousins on Saturdays.", ""),
                         ("I stay in on Sundays because I'm tired.", ""),
                         ("We eat out once a month because it's expensive.", "")],
        },
        skills=["phrasal_verbs", "linking_words", "like_ing"],
        partner_role="friend",
        dialogue=[
            ("partner", "What do you do at the weekend?"),
            ("learner", "On Saturdays I hang out with my friends."),
            ("partner", "Do you go out in the evening?"),
            ("learner", "Sometimes we eat out, but usually I stay in."),
            ("partner", "Why do you stay in?"),
            ("learner", "Because I'm tired after the week and I want to chill out."),
        ],
        extend=[
            ("I stay in.", "the short sentence"),
            ("I stay in on Sundays.", "WHEN"),
            ("I stay in on Sundays with my family.", "WHO WITH"),
            ("I stay in on Sundays with my family because we want to chill out after the week.", "WHY (because)"),
        ],
        build=[
            ("Add WHO WITH: I hang out.", "I hang out with my best friend."),
            ("Add WHY with 'because': I eat out on Fridays.", "I eat out on Fridays because I'm too tired to cook."),
            ("Use 'sleep in' and 'on Sundays'.", "I sleep in on Sundays."),
            ("Join with 'but': I go out on Saturdays. I stay in on Sundays.", "I go out on Saturdays, but I stay in on Sundays."),
        ],
        questions=[
            ("Do you prefer to go out or stay in at the weekend? Why?", "I prefer to stay in because I can chill out and sleep in."),
            ("Who do you usually hang out with?", "I usually hang out with my cousins because they live near me."),
        ],
        speak="Describe your perfect weekend. Every sentence needs a phrasal verb and WHEN, WHO WITH or WHY.",
    ),

    # ══ WEEK 2 - A2: people and plans ════════════════════════════════════════
    _lesson(
        "en-p05", 2, 1, "A2", "Phone and messages: call back, pick up, hang up",
        "handle a phone call and explain why you could not answer",
        words=[
            ("call back", "phone someone again later", "geri zəng etmək", "I'll call you back in ten minutes."),
            ("pick up", "answer the phone", "telefonu açmaq", "She didn't pick up."),
            ("hang up", "end a phone call", "dəstəyi qoymaq, zəngi bitirmək", "Don't hang up!"),
            ("get through", "manage to speak on the phone", "zəngin çatması, danışa bilmək", "I couldn't get through to the bank."),
            ("hold on", "wait a moment", "bir dəqiqə gözləmək", "Hold on, I'll check."),
            ("text back", "answer a message", "mesaja cavab yazmaq", "Text me back when you can."),
        ],
        phrases=[
            ("Sorry, I couldn't pick up because I was driving.", "a reason for a missed call", "Bağışla, maşın sürürdüm deyə telefonu aça bilmədim."),
            ("Can I call you back later?", "asking for time", "Sənə sonra geri zəng edə bilərəm?"),
            ("Hold on a second, please.", "asking to wait", "Bir saniyə gözləyin, zəhmət olmasa."),
            ("I tried to call, but I couldn't get through.", "a failed call", "Zəng etməyə çalışdım, amma çatmadı."),
            ("Text me back when you are free.", "a request", "Boş olanda mənə cavab yaz."),
        ],
        grammar={
            "name": "Past simple phrasal verbs + because / but",
            "rule": ("In the past only the verb changes: pick up → picked up, call back → called back, "
                     "hang up → hung up, get through → got through. Add because (why) or but (a problem): "
                     "'I called her, but she didn't pick up.'"),
            "table": ["verb + ed / irregular + small word", "didn't + verb + small word",
                      "I called back, but ... / because ..."],
            "examples": [("I called her, but she didn't pick up.", ""),
                         ("I couldn't get through because the line was busy.", ""),
                         ("He hung up before I could answer.", "")],
        },
        skills=["phrasal_verbs", "past_simple", "linking_words"],
        partner_role="colleague on the phone",
        dialogue=[
            ("partner", "Hi! I called you this morning."),
            ("learner", "Sorry, I couldn't pick up because I was in a meeting."),
            ("partner", "No problem. Do you have a minute now?"),
            ("learner", "Hold on a second, please. OK, I'm here."),
            ("partner", "Can we talk about the report?"),
            ("learner", "Sure, but can I call you back in ten minutes?"),
        ],
        extend=[
            ("I didn't pick up.", "the short sentence"),
            ("I didn't pick up the phone this morning.", "WHAT + WHEN"),
            ("I didn't pick up the phone this morning because I was driving.", "WHY"),
            ("I didn't pick up the phone this morning because I was driving, so I called her back later.", "SO + what you did next"),
        ],
        build=[
            ("Add WHY: I couldn't pick up.", "I couldn't pick up because I was in the shower."),
            ("Past simple with 'but': I call the bank. I don't get through.", "I called the bank, but I didn't get through."),
            ("Use 'call back' + WHEN: I'll phone you again.", "I'll call you back after lunch."),
            ("Join with 'so': She was busy. She hung up.", "She was busy, so she hung up."),
        ],
        questions=[
            ("What do you do when you can't pick up the phone?", "I text back and say I'll call back later."),
            ("Tell me about a difficult phone call.", "I called the bank three times, but I couldn't get through, so I went there."),
        ],
        speak="Role play: you missed three calls from a friend. Call them back, explain why you didn't pick up and make a plan.",
    ),
    _lesson(
        "en-p06", 2, 2, "A2", "Friends: meet up, catch up, get on with",
        "talk about a friend and what you do together",
        words=[
            ("meet up", "meet a friend by arrangement", "görüşmək (razılaşaraq)", "Let's meet up on Friday."),
            ("catch up", "talk about news after some time", "xəbərləşmək, yenilikləri danışmaq", "We had coffee and caught up."),
            ("get on with", "have a good relationship", "yola getmək", "I get on with my sister."),
            ("hang out", "spend free time together", "birlikdə vaxt keçirmək", "We hang out after work."),
            ("invite over", "ask someone to come to your home", "evə dəvət etmək", "I invited them over for dinner."),
            ("show up", "arrive, appear", "gəlib çıxmaq", "He showed up an hour late."),
        ],
        phrases=[
            ("Let's meet up this weekend.", "a suggestion", "Gəl bu həftəsonu görüşək."),
            ("It was great to catch up with you.", "after a meeting", "Səninlə xəbərləşmək çox xoş idi."),
            ("I get on really well with him.", "a good relationship", "Onunla çox yaxşı yola gedirəm."),
            ("We invited some friends over for dinner.", "hosting", "Bir neçə dostu şam yeməyinə evə dəvət etdik."),
            ("She didn't show up, so I went home.", "a problem and a result", "O gəlmədi, ona görə evə getdim."),
        ],
        grammar={
            "name": "who + extra information",
            "rule": ("Add information about a person with who: 'I have a friend who lives in Baku.' "
                     "Then the phrasal verb: 'I have a friend who I get on with really well.'"),
            "table": ["person + who + verb", "a friend + who + lives near me",
                      "... who I meet up with every week"],
            "examples": [("I have a friend who lives near me.", ""),
                         ("She's the colleague who I get on with best.", ""),
                         ("We meet up in a café that has great coffee.", "")],
        },
        skills=["phrasal_verbs", "relative_clauses", "past_simple"],
        partner_role="friend",
        dialogue=[
            ("partner", "It's so good to see you!"),
            ("learner", "Yes! It's great to catch up with you."),
            ("partner", "Do you still see Ali?"),
            ("learner", "Yes, we meet up every week. I get on really well with him."),
            ("partner", "What do you do together?"),
            ("learner", "We hang out in a café that has great coffee, or I invite him over."),
        ],
        extend=[
            ("I meet up with my friend.", "the short sentence"),
            ("I meet up with my friend every Friday.", "WHEN"),
            ("I meet up with my friend who lives near me every Friday.", "WHO (+ extra information)"),
            ("I meet up with my friend who lives near me every Friday, and we catch up over coffee.", "AND + what you do"),
        ],
        build=[
            ("Add information with 'who': I have a friend. He lives in London.", "I have a friend who lives in London."),
            ("Use 'catch up' + WHERE: We talked about our news.", "We caught up in a café."),
            ("Use 'get on with' + a reason: I like my colleague.", "I get on with my colleague because she's funny."),
            ("Past simple + 'so': He didn't show up. I called him.", "He didn't show up, so I called him."),
        ],
        questions=[
            ("Tell me about a friend who you get on with really well.", "I have a friend who lives near me. We meet up every week and catch up."),
            ("When did you last invite friends over?", "I invited some friends over last Saturday and we cooked together."),
        ],
        speak="Describe your best friend: who they are, how you met, what you do when you meet up. Use who and at least four phrasal verbs.",
    ),
    _lesson(
        "en-p07", 2, 3, "A2", "Shopping: look for, try on, pay for",
        "describe a shopping trip with a plus and a minus",
        words=[
            ("look for", "try to find", "axtarmaq", "I'm looking for a winter coat."),
            ("try on", "put on clothes to see if they fit", "geyinib yoxlamaq", "Can I try this on?"),
            ("pay for", "give money for something", "pul ödəmək", "I paid for it by card."),
            ("pick out", "choose", "seçmək", "She picked out a nice dress."),
            ("take back", "return something to a shop", "geri qaytarmaq (mağazaya)", "I took the shoes back."),
            ("sell out", "have none left", "satılıb qurtarmaq", "The small sizes sold out."),
        ],
        phrases=[
            ("I'm just looking, thanks.", "in a shop", "Sadəcə baxıram, sağ olun."),
            ("Can I try it on?", "asking to try", "Geyinib yoxlaya bilərəm?"),
            ("I liked it, but it didn't fit, so I took it back.", "plus, minus, result", "Xoşuma gəldi, amma ölçüm deyildi, ona görə qaytardım."),
            ("The blue one sold out, so I picked out the black one.", "a different choice", "Göy olan qurtarmışdı, ona görə qaranı seçdim."),
            ("Can I pay for it by card?", "paying", "Kartla ödəyə bilərəm?"),
        ],
        grammar={
            "name": "Object pronouns with phrasal verbs: try it on",
            "rule": ("With many phrasal verbs, it / them goes in the MIDDLE: try it on, take them back, "
                     "pick it out. NOT try on it. With a noun both are OK: try on the jacket / try the "
                     "jacket on. But look for and pay for never split: look for it, pay for it."),
            "table": ["try + it + on (NOT try on it)", "take + them + back",
                      "look for + it · pay for + it (no split)"],
            "examples": [("I liked the jacket, so I tried it on.", ""),
                         ("The shoes were too small, so I took them back.", ""),
                         ("I looked for it everywhere, but I didn't find it.", "")],
        },
        skills=["phrasal_verbs", "pronouns_possessives", "linking_words"],
        partner_role="shop assistant",
        dialogue=[
            ("partner", "Hello, can I help you?"),
            ("learner", "Yes, I'm looking for a winter coat."),
            ("partner", "What about this one?"),
            ("learner", "It's nice. Can I try it on?"),
            ("partner", "Of course. How is it?"),
            ("learner", "I like it, but it's a bit big. Do you have a smaller one?"),
        ],
        extend=[
            ("I tried it on.", "the short sentence"),
            ("I tried the jacket on in the shop.", "WHAT + WHERE"),
            ("I tried the jacket on in the shop, but it was too small.", "BUT + a problem"),
            ("I tried the jacket on in the shop, but it was too small, so I picked out a bigger one.", "SO + the result"),
        ],
        build=[
            ("Use 'it' in the right place: I took back the phone.", "I took it back."),
            ("Add BUT + a problem: I tried on the shoes.", "I tried on the shoes, but they were too big."),
            ("Use 'look for' + WHY: I need a present.", "I'm looking for a present because it's my mum's birthday."),
            ("Join with 'so': My size sold out. I bought it online.", "My size sold out, so I bought it online."),
        ],
        questions=[
            ("Tell me about the last thing you bought.", "I was looking for new trainers. I tried two pairs on and picked out the white ones."),
            ("Did you ever take something back to a shop? Why?", "Yes, I took a shirt back because it didn't fit."),
        ],
        speak="Tell the story of a shopping trip: what you looked for, what you tried on, what went wrong and what you paid for.",
    ),
    _lesson(
        "en-p08", 2, 4, "A2", "Plans: look forward to, put off, find out",
        "talk about plans with going to and say how you feel about them",
        words=[
            ("look forward to", "feel happy about something in the future", "səbirsizliklə gözləmək", "I'm looking forward to the holiday."),
            ("put off", "move to a later time", "təxirə salmaq", "We put off the trip until May."),
            ("find out", "learn a fact", "öyrənmək, bilmək", "I found out the price."),
            ("sign up for", "join a course or activity", "qeydiyyatdan keçmək, yazılmaq", "I signed up for a yoga class."),
            ("plan ahead", "plan early", "əvvəlcədən planlaşdırmaq", "I like to plan ahead."),
            ("call off", "cancel", "ləğv etmək", "They called off the match."),
        ],
        phrases=[
            ("I'm really looking forward to it.", "excited about the future", "Onu səbirsizliklə gözləyirəm."),
            ("We had to put it off because of the weather.", "a delay and a reason", "Hava səbəbindən təxirə salmalı olduq."),
            ("I'm going to find out more about it.", "a plan", "Bu barədə daha çox öyrənəcəyəm."),
            ("I've signed up for an English course.", "a new activity", "İngilis dili kursuna yazılmışam."),
            ("They called it off at the last minute.", "a cancellation", "Son dəqiqədə ləğv etdilər."),
        ],
        grammar={
            "name": "going to + phrasal verb + because / so that",
            "rule": ("For a plan use am / is / are going to + verb: 'I'm going to sign up for a course.' "
                     "Add why with because, or the aim with so that. Careful: look forward to + noun or "
                     "-ing: 'I'm looking forward to seeing you.'"),
            "table": ["I'm going to + phrasal verb", "... because / so that ...",
                      "look forward to + -ing / noun"],
            "examples": [("I'm going to sign up for a course because I want to speak better.", ""),
                         ("We're going to put off the party until Sunday.", ""),
                         ("I'm looking forward to meeting my new colleagues.", "")],
        },
        skills=["phrasal_verbs", "future_forms", "gerund_infinitive"],
        partner_role="friend",
        dialogue=[
            ("partner", "Any plans for the summer?"),
            ("learner", "Yes, I'm going to visit my cousins in Georgia."),
            ("partner", "Nice! Are you excited?"),
            ("learner", "Yes, I'm really looking forward to it."),
            ("partner", "Weren't you going to go in spring?"),
            ("learner", "We were, but we put it off because of my new job."),
        ],
        extend=[
            ("I'm going to sign up.", "the short sentence"),
            ("I'm going to sign up for a cooking class.", "FOR WHAT"),
            ("I'm going to sign up for a cooking class next month.", "WHEN"),
            ("I'm going to sign up for a cooking class next month because I want to eat out less.", "WHY"),
        ],
        build=[
            ("Use 'look forward to' + -ing: I'm happy I will see you.", "I'm looking forward to seeing you."),
            ("Add a reason: We put off the meeting.", "We put off the meeting because the boss was ill."),
            ("Use 'going to' + 'find out': I will learn the price.", "I'm going to find out the price."),
            ("Join with 'so': It rained. They called off the match.", "It rained, so they called off the match."),
        ],
        questions=[
            ("What are you looking forward to this month?", "I'm looking forward to my birthday because my family is going to come over."),
            ("What do you often put off? Why?", "I often put off cleaning because I'm always tired after work."),
        ],
        speak="Talk about three plans for the next months: what you are going to do, why, and how you feel about it. Use look forward to, put off and sign up for.",
    ),

    # ══ WEEK 3 - B1: longer sentences ════════════════════════════════════════
    _lesson(
        "en-p09", 3, 1, "B1", "Problems: break down, run out of, sort out",
        "tell the story of a small problem and how you solved it",
        words=[
            ("break down", "stop working (a car, a machine)", "xarab olmaq", "My car broke down on the motorway."),
            ("run out of", "have no more", "qurtarmaq, tükənmək", "We ran out of milk."),
            ("sort out", "solve, organise", "həll etmək, qaydaya salmaq", "I'll sort it out tomorrow."),
            ("fix up", "repair", "təmir etmək", "My uncle fixed it up for me."),
            ("figure out", "understand after thinking", "başa düşmək, anlamaq", "I couldn't figure out the problem."),
            ("mess up", "do something badly", "korlamaq, qarışdırmaq", "I messed up the order."),
        ],
        phrases=[
            ("My car broke down on the way to work.", "a problem on the way", "Maşınım işə gedərkən xarab oldu."),
            ("We ran out of petrol in the middle of nowhere.", "nothing left", "Heç kimsəsiz bir yerdə benzinimiz qurtardı."),
            ("Don't worry, I'll sort it out.", "offering help", "Narahat olma, mən həll edəcəyəm."),
            ("It took me an hour to figure out what was wrong.", "time + problem", "Nəyin səhv olduğunu anlamaq mənə bir saat çəkdi."),
            ("I messed up, but I learned a lot.", "admitting a mistake", "Səhv etdim, amma çox şey öyrəndim."),
        ],
        grammar={
            "name": "Past continuous for the background: was driving when ...",
            "rule": ("Tell a story with two pasts: was / were + -ing for the longer background action, "
                     "past simple for the short thing that happened: 'I was driving to work when my car "
                     "broke down.' Then say what you did: 'so I called a mechanic.'"),
            "table": ["I was + -ing ... when + past simple", "..., so I + past simple",
                      "While I was ..., ... broke down"],
            "examples": [("I was driving to work when my car broke down.", ""),
                         ("While we were cooking, we ran out of oil.", ""),
                         ("The laptop broke down, so I sorted it out with IT.", "")],
        },
        skills=["phrasal_verbs", "past_continuous", "linking_words"],
        partner_role="colleague",
        dialogue=[
            ("partner", "Why were you so late today?"),
            ("learner", "I was driving to work when my car broke down."),
            ("partner", "Oh no! What did you do?"),
            ("learner", "I couldn't figure out the problem, so I called my brother."),
            ("partner", "Did he help?"),
            ("learner", "Yes, he came quickly and sorted it out in twenty minutes."),
        ],
        extend=[
            ("My car broke down.", "the short sentence"),
            ("My car broke down on the motorway.", "WHERE"),
            ("I was driving to work when my car broke down on the motorway.", "the BACKGROUND (was + -ing ... when)"),
            ("I was driving to work when my car broke down on the motorway, so I called a mechanic who sorted it out.", "SO + the solution"),
        ],
        build=[
            ("Join with 'when': I was cooking. We ran out of salt.", "I was cooking when we ran out of salt."),
            ("Add the solution with 'so': The washing machine broke down.", "The washing machine broke down, so I called a repairman."),
            ("Use 'figure out' + 'because': I couldn't do the task.", "I couldn't figure out the task because the instructions were bad."),
            ("Use 'while': We were travelling. The car broke down.", "While we were travelling, the car broke down."),
        ],
        questions=[
            ("Tell me about a time something broke down.", "I was working on my laptop when it broke down, so I took it to a shop and they fixed it up."),
            ("What do you do when you run out of something important?", "When I run out of coffee, I borrow some from my neighbour."),
        ],
        speak="Tell a story about a problem: what you were doing, what broke down or ran out, and how you sorted it out. At least six sentences.",
    ),
    _lesson(
        "en-p10", 3, 2, "B1", "Work: take on, deal with, fill in",
        "describe your job and your responsibilities in long, clear sentences",
        words=[
            ("take on", "accept work or responsibility", "öhdəsinə götürmək", "I took on a new project."),
            ("deal with", "handle a situation or a person", "məşğul olmaq, həll etmək", "I deal with customers every day."),
            ("fill in", "write information in a form", "doldurmaq (formanı)", "Please fill in this form."),
            ("set up", "start, organise", "qurmaq, təşkil etmək", "We set up a meeting for Monday."),
            ("follow up", "check or continue later", "davamını izləmək", "I'll follow up with an email."),
            ("carry out", "do a task or a plan", "həyata keçirmək", "We carried out a survey."),
        ],
        phrases=[
            ("I deal with customers who have problems.", "a responsibility", "Problemi olan müştərilərlə məşğul oluram."),
            ("I've just taken on a new project.", "recent news", "Bu yaxınlarda yeni bir layihəni öhdəmə götürmüşəm."),
            ("Could you fill in this form, please?", "a polite request", "Bu formanı doldura bilərsiniz, zəhmət olmasa?"),
            ("Let's set up a meeting for next week.", "organising", "Gəlin gələn həftə üçün görüş təşkil edək."),
            ("I'll follow up with you on Friday.", "promising to check", "Cümə günü sizinlə əlaqə saxlayacam."),
        ],
        grammar={
            "name": "Present perfect for news: I've just taken on ...",
            "rule": ("For recent news or experience use have / has + past participle: 'I've just taken "
                     "on a project.' 'I've never dealt with such a difficult client.' Add a result with "
                     "so, or a contrast with although."),
            "table": ["I've just + participle (news)", "I've never / ever + participle (experience)",
                      "... so / although ..."],
            "examples": [("I've just taken on a new project, so I'm very busy.", ""),
                         ("I've never dealt with such an angry customer.", ""),
                         ("Although it's hard, I've set up a good team.", "")],
        },
        skills=["phrasal_verbs", "present_perfect", "linking_words"],
        partner_role="interviewer",
        dialogue=[
            ("partner", "Tell me about your job."),
            ("learner", "I work in customer service. I deal with people who have problems with their orders."),
            ("partner", "What's new at work?"),
            ("learner", "I've just taken on a new project, so I'm very busy."),
            ("partner", "What do you do in a normal day?"),
            ("learner", "I answer emails, set up meetings and follow up with clients."),
        ],
        extend=[
            ("I deal with customers.", "the short sentence"),
            ("I deal with customers every day.", "HOW OFTEN"),
            ("I deal with customers who have problems with their orders every day.", "WHO (+ which customers)"),
            ("I deal with customers who have problems with their orders every day, so I've learned to stay calm.", "SO + the result (present perfect)"),
        ],
        build=[
            ("Present perfect news with 'just': I take on a new role.", "I've just taken on a new role."),
            ("Add WHO: I deal with clients.", "I deal with clients who live abroad."),
            ("Join with 'although': The project is hard. I've taken it on.", "Although the project is hard, I've taken it on."),
            ("Use 'follow up' + WHEN + HOW: I'll check with the client.", "I'll follow up with the client tomorrow by email."),
        ],
        questions=[
            ("What do you deal with at work or school every day?", "I deal with a lot of emails, so I set up a system to sort them out."),
            ("What new thing have you taken on recently?", "I've just taken on a new course, although I'm already very busy."),
        ],
        speak="Job interview role play: describe your job or studies, your responsibilities and one thing you've taken on recently. Answer in long sentences.",
    ),
    _lesson(
        "en-p11", 3, 3, "B1", "Stories: end up, turn out, come across",
        "tell a short story with a surprise in it",
        words=[
            ("end up", "be in a place or situation in the end", "sonda ... olmaq, gəlib çıxmaq", "We ended up in a small village."),
            ("turn out", "be in the end (often a surprise)", "məlum olmaq, çıxmaq", "It turned out to be a great day."),
            ("come across", "find or meet by chance", "təsadüfən rast gəlmək", "I came across an old photo."),
            ("run into", "meet someone by chance", "təsadüfən qarşılaşmaq", "I ran into my teacher in the shop."),
            ("get lost", "not know where you are", "azmaq", "We got lost in the old town."),
            ("find out", "discover a fact", "öyrənmək, aşkar etmək", "Later I found out the truth."),
        ],
        phrases=[
            ("We got lost and ended up in a lovely café.", "a surprise ending", "Azdıq və sonda gözəl bir kafeyə gəlib çıxdıq."),
            ("It turned out that he was my neighbour.", "a surprise fact", "Məlum oldu ki, o mənim qonşum imiş."),
            ("I came across it by chance.", "finding something", "Ona təsadüfən rast gəldim."),
            ("Guess who I ran into yesterday!", "starting a story", "Təxmin et, dünən kimlə qarşılaşdım!"),
            ("In the end, it turned out fine.", "the ending", "Sonda hər şey yaxşı oldu."),
        ],
        grammar={
            "name": "Story order: first, then, suddenly, in the end",
            "rule": ("A good story has an order: At first ... Then ... Suddenly ... In the end ... "
                     "Use end up + -ing / place and turn out + that / to be for the ending: "
                     "'We ended up staying there all day.' 'It turned out to be closed.'"),
            "table": ["At first → Then → Suddenly → In the end", "end up + -ing / place",
                      "turn out + that ... / to be ..."],
            "examples": [("At first we got lost, but then we came across a lovely café.", ""),
                         ("We ended up staying there all afternoon.", ""),
                         ("In the end, it turned out to be the best day of the trip.", "")],
        },
        skills=["phrasal_verbs", "past_simple", "discourse_markers"],
        partner_role="friend",
        dialogue=[
            ("partner", "How was your trip?"),
            ("learner", "Funny! At first we got lost in the old town."),
            ("partner", "Oh no! What happened?"),
            ("learner", "Then we came across a small restaurant and went in."),
            ("partner", "Was it good?"),
            ("learner", "It turned out to be the best meal of the trip. We ended up staying for three hours."),
        ],
        extend=[
            ("I ran into a friend.", "the short sentence"),
            ("I ran into an old friend at the airport.", "WHO + WHERE"),
            ("I ran into an old friend at the airport, and it turned out that we were on the same flight.", "AND + a surprise (turned out)"),
            ("I ran into an old friend at the airport, and it turned out that we were on the same flight, so we ended up talking all the way.", "SO + the ending (ended up)"),
        ],
        build=[
            ("Use 'end up' + -ing: We didn't plan it, but we stayed all night.", "We ended up staying all night."),
            ("Use 'turn out' + that: The man was my cousin's friend.", "It turned out that the man was my cousin's friend."),
            ("Add WHERE + a surprise: I came across an old letter.", "I came across an old letter in my grandmother's house, and it turned out to be from my grandfather."),
            ("Start with 'At first' and 'but then': We got lost. We found the hotel.", "At first we got lost, but then we found the hotel."),
        ],
        questions=[
            ("Did you ever run into someone in a surprising place?", "Yes, I ran into my boss at the beach. It turned out that we were in the same hotel."),
            ("Tell me about a plan that ended up very different.", "We wanted to go to the cinema, but we ended up staying at home and cooking together."),
        ],
        speak="Tell a story with a surprise: use at first, then, suddenly, in the end, and end up, turn out, come across or run into.",
    ),
    _lesson(
        "en-p12", 3, 4, "B1", "Plans change: make it, work out, back out",
        "explain a change of plans politely, with conditions",
        words=[
            ("work out", "happen in a good way", "alınmaq, yaxşı nəticələnmək", "I hope everything works out."),
            ("back out", "decide not to do what you agreed", "sözündən dönmək, imtina etmək", "He backed out at the last minute."),
            ("fit in", "find time for", "vaxt tapmaq, sığışdırmaq", "Can you fit me in on Tuesday?"),
            ("move up / move back", "make earlier / later", "tezə / gecə keçirmək", "Can we move the meeting back to three?"),
            ("count on", "trust someone to help", "arxalanmaq, güvənmək", "You can count on me."),
            ("let down", "disappoint", "məyus etmək, ümidini qırmaq", "I don't want to let you down."),
        ],
        phrases=[
            ("I'm afraid I can't make it on Friday.", "saying no politely", "Təəssüf ki, cümə günü gələ bilməyəcəm."),
            ("If Friday doesn't work out, we can meet on Saturday.", "a condition", "Cümə alınmasa, şənbə görüşə bilərik."),
            ("Can you fit me in tomorrow morning?", "asking for time", "Sabah səhər mənə vaxt tapa bilərsiniz?"),
            ("Sorry to let you down.", "apologising", "Ümidini qırdığım üçün üzr istəyirəm."),
            ("Don't worry, you can count on me.", "a promise", "Narahat olma, mənə güvənə bilərsən."),
        ],
        grammar={
            "name": "if / unless for plans",
            "rule": ("First conditional: If + present, will + verb: 'If it doesn't work out, I'll call "
                     "you.' unless = if not: 'I'll come unless something comes up.' Never will after if."),
            "table": ["If + present, ... will + verb", "... unless + present",
                      "NOT: If it will work out ..."],
            "examples": [("If the meeting doesn't work out, we'll move it back.", ""),
                         ("I'll be there unless something comes up.", ""),
                         ("If you can't make it, I'll fit you in next week.", "")],
        },
        skills=["phrasal_verbs", "first_conditional", "modals_basic"],
        partner_role="friend who organises a dinner",
        dialogue=[
            ("partner", "So, dinner on Friday at eight?"),
            ("learner", "I'm afraid I can't make it on Friday. I have to work late."),
            ("partner", "Oh, that's a shame."),
            ("learner", "Sorry to let you down. Can we move it back to Saturday?"),
            ("partner", "Maybe. Are you sure you won't back out again?"),
            ("learner", "Don't worry, you can count on me. I'll be there unless something really serious comes up."),
        ],
        extend=[
            ("I can't make it.", "the short sentence"),
            ("I'm afraid I can't make it on Friday.", "POLITE + WHEN"),
            ("I'm afraid I can't make it on Friday because I have to work late.", "WHY"),
            ("I'm afraid I can't make it on Friday because I have to work late, but if Saturday works out, I'll definitely come.", "BUT + IF + a promise"),
        ],
        build=[
            ("Make it polite with 'I'm afraid' + WHY: I can't make it.", "I'm afraid I can't make it because my son is ill."),
            ("First conditional: it / not work out → we / try again.", "If it doesn't work out, we'll try again."),
            ("Use 'unless': I'll come. Something comes up.", "I'll come unless something comes up."),
            ("Use 'move back' + a new time: The meeting is at two. Make it later.", "Can we move the meeting back to four?"),
        ],
        questions=[
            ("What do you say when you can't make it to a meeting?", "I'm afraid I can't make it, but if you can fit me in tomorrow, I'll be there."),
            ("Who can you always count on? Why?", "I can always count on my sister because she never lets me down."),
        ],
        speak="Role play: you have to cancel a plan with a friend. Apologise, explain why, and suggest a new plan with if and unless.",
    ),

    # ══ WEEK 4 - B1: feelings, habits, advice ════════════════════════════════
    _lesson(
        "en-p13", 4, 1, "B1", "Feelings: cheer up, calm down, freak out",
        "talk about feelings and explain what makes you feel that way",
        words=[
            ("cheer up", "become happier / make someone happier", "kefini açmaq, ruhlandırmaq", "Cheer up! It's not so bad."),
            ("calm down", "become less angry or nervous", "sakitləşmək", "Calm down and tell me what happened."),
            ("freak out", "become very scared or upset", "çox qorxmaq, özündən çıxmaq", "I freaked out when I lost my passport."),
            ("stress out", "make someone feel stressed", "stresə salmaq", "Exams stress me out."),
            ("get over", "feel better after something bad", "keçirmək, özünə gəlmək", "It took me a month to get over it."),
            ("put up with", "accept something bad without complaining", "dözmək", "I can't put up with the noise."),
        ],
        phrases=[
            ("Exams really stress me out.", "a cause of stress", "İmtahanlar məni çox stresə salır."),
            ("I freaked out when I couldn't find my keys.", "a strong reaction", "Açarlarımı tapa bilməyəndə çox qorxdum."),
            ("Music always cheers me up.", "what helps", "Musiqi həmişə kefimi açır."),
            ("It took me a while to get over it.", "recovering", "Bunu keçirmək bir müddət çəkdi."),
            ("I can't put up with people who are always late.", "what you can't accept", "Həmişə gecikən insanlara dözə bilmirəm."),
        ],
        grammar={
            "name": "make + person + feel / It + verb + me + because",
            "rule": ("Say what causes a feeling: 'Traffic stresses me out.' 'Music cheers me up.' "
                     "'Rainy days make me feel sad.' Then add because or when to explain: "
                     "'I freak out when I have to speak in public.'"),
            "table": ["thing + phrasal verb + me + up/out", "thing + makes me feel + adjective",
                      "I + phrasal verb + when ..."],
            "examples": [("Long queues stress me out because I hate waiting.", ""),
                         ("Talking to my mum always cheers me up.", ""),
                         ("I freak out when I have to speak in public.", "")],
        },
        skills=["phrasal_verbs", "linking_words", "pronouns_possessives"],
        partner_role="close friend",
        dialogue=[
            ("partner", "You look tired. Is everything OK?"),
            ("learner", "Not really. Work is stressing me out at the moment."),
            ("partner", "What happened?"),
            ("learner", "I freaked out when my boss moved the deadline up."),
            ("partner", "Calm down, you'll be fine. What cheers you up?"),
            ("learner", "A walk in the park always cheers me up, so I'm going to go out after work."),
        ],
        extend=[
            ("Music cheers me up.", "the short sentence"),
            ("Music always cheers me up after a long day.", "HOW OFTEN + WHEN"),
            ("Music always cheers me up after a long day because it helps me forget about work.", "WHY"),
            ("Music always cheers me up after a long day because it helps me forget about work, but traffic stresses me out.", "BUT + a contrast"),
        ],
        build=[
            ("Say what causes it: I feel stressed. Deadlines.", "Deadlines stress me out."),
            ("Use 'freak out' + when: I lost my phone.", "I freaked out when I lost my phone."),
            ("Add WHY: I can't put up with noise.", "I can't put up with noise because I need to concentrate."),
            ("Use 'get over' + 'it took': I was ill for two weeks.", "It took me two weeks to get over the flu."),
        ],
        questions=[
            ("What stresses you out, and what cheers you up?", "Traffic stresses me out, but cooking always cheers me up because it's relaxing."),
            ("What can't you put up with?", "I can't put up with people who talk loudly on the phone on the bus."),
        ],
        speak="Talk about your feelings this week: what stressed you out, what cheered you up, and how you calmed down. Use because and when in every answer.",
    ),
    _lesson(
        "en-p14", 4, 2, "B1", "People: fall out, make up, get along",
        "describe a relationship and a disagreement you solved",
        words=[
            ("get along", "have a friendly relationship", "yola getmək, dil tapmaq", "We get along really well."),
            ("fall out", "stop being friends after an argument", "küsmək, aranın dəyməsi", "They fell out over money."),
            ("make up", "become friends again", "barışmaq", "We made up the next day."),
            ("look up to", "respect and admire", "nümunə götürmək, hörmət etmək", "I look up to my father."),
            ("take after", "look or behave like an older relative", "oxşamaq (valideynə)", "I take after my mother."),
            ("bring up", "raise a child", "böyütmək, tərbiyə etmək", "My grandparents brought me up."),
        ],
        phrases=[
            ("We fell out, but we made up after a week.", "a problem and a solution", "Aramız dəydi, amma bir həftə sonra barışdıq."),
            ("I really look up to her.", "respect", "Onu həqiqətən özümə nümunə sayıram."),
            ("Everybody says I take after my dad.", "family resemblance", "Hamı deyir ki, atama oxşayıram."),
            ("I was brought up in a small town.", "childhood", "Kiçik bir şəhərdə böyümüşəm."),
            ("We don't always get along, but we respect each other.", "an honest description", "Həmişə yola getmirik, amma bir-birimizə hörmət edirik."),
        ],
        grammar={
            "name": "Contrast: although, even though, however",
            "rule": ("Put a surprise or a contrast in one sentence with although / even though: "
                     "'Although we fell out, we made up quickly.' Or start a new sentence with However,: "
                     "'We argue a lot. However, we always make up.'"),
            "table": ["Although + clause, clause", "clause even though + clause",
                      "Sentence. However, sentence."],
            "examples": [("Although we fell out, we made up quickly.", ""),
                         ("I get along with my brother even though we are very different.", ""),
                         ("We argue a lot. However, we always make up.", "")],
        },
        skills=["phrasal_verbs", "linking_words", "past_simple"],
        partner_role="friend",
        dialogue=[
            ("partner", "Do you get along with your brother?"),
            ("learner", "Yes, although we are very different."),
            ("partner", "Do you ever fall out?"),
            ("learner", "Sometimes. Last year we fell out over a stupid thing."),
            ("partner", "And did you make up?"),
            ("learner", "Yes, we made up a week later. However, we still joke about it."),
        ],
        extend=[
            ("We fell out.", "the short sentence"),
            ("My sister and I fell out last summer.", "WHO + WHEN"),
            ("My sister and I fell out last summer because I forgot her birthday.", "WHY"),
            ("Although my sister and I fell out last summer because I forgot her birthday, we made up after a few days.", "ALTHOUGH + the ending"),
        ],
        build=[
            ("Join with 'although': We are different. We get along.", "Although we are different, we get along."),
            ("Use 'however': We argue a lot. We always make up.", "We argue a lot. However, we always make up."),
            ("Add WHO + WHY: I look up to someone.", "I look up to my grandmother because she is very brave."),
            ("Use 'take after' + 'but': I look like my dad. I behave like my mum.", "I look like my dad, but I take after my mum."),
        ],
        questions=[
            ("Who do you take after in your family?", "I take after my mum. We are both calm, although I look like my dad."),
            ("Tell me about a time you fell out with someone. Did you make up?", "I fell out with a friend over money. However, we made up a month later."),
        ],
        speak="Describe someone important in your life: how you get along, a time you fell out and made up, and why you look up to them. Use although and however.",
    ),
    _lesson(
        "en-p15", 4, 3, "B1", "Habits: give up, cut down on, take up",
        "talk about old and new habits, and how long you have had them",
        words=[
            ("give up", "stop doing something", "tərgitmək, əl çəkmək", "I gave up sugar last year."),
            ("cut down on", "do or use less", "azaltmaq", "I'm trying to cut down on coffee."),
            ("take up", "start a new hobby or activity", "(yeni hobbiyə) başlamaq", "I took up running in May."),
            ("work out", "do exercise", "idman etmək, məşq etmək", "I work out three times a week."),
            ("keep up", "continue at the same level", "davam etdirmək, saxlamaq", "It's hard to keep it up."),
            ("get into", "start to like an activity", "həvəslənmək, maraqlanmaq", "I got into yoga during the lockdown."),
        ],
        phrases=[
            ("I used to smoke, but I gave it up five years ago.", "an old habit", "Əvvəllər siqaret çəkirdim, amma beş il əvvəl tərgitdim."),
            ("I'm trying to cut down on sugar.", "a goal", "Şəkəri azaltmağa çalışıram."),
            ("I've been working out for six months.", "how long", "Altı aydır ki, idman edirəm."),
            ("I took up swimming to feel healthier.", "a new habit + purpose", "Daha sağlam hiss etmək üçün üzməyə başladım."),
            ("It's easy to start, but hard to keep it up.", "an honest opinion", "Başlamaq asandır, amma davam etdirmək çətindir."),
        ],
        grammar={
            "name": "used to / for & since",
            "rule": ("used to + verb = a past habit that stopped: 'I used to eat a lot of sweets.' "
                     "For something that started in the past and continues, use present perfect "
                     "(continuous) with for (a period) or since (a start point): 'I've been working out "
                     "for a year / since January.'"),
            "table": ["I used to + verb (not now)", "I've been + -ing + for / since",
                      "for two years · since 2024"],
            "examples": [("I used to drink five coffees a day, but I've cut down on it.", ""),
                         ("I've been working out since January.", ""),
                         ("I took up yoga two years ago, and I've kept it up.", "")],
        },
        skills=["phrasal_verbs", "used_to", "present_perfect_continuous"],
        partner_role="fitness coach",
        dialogue=[
            ("partner", "So, tell me about your habits."),
            ("learner", "I used to eat a lot of fast food, but I've cut down on it."),
            ("partner", "Great. Do you do any sport?"),
            ("learner", "Yes, I took up swimming last year, and I've kept it up."),
            ("partner", "How often do you work out?"),
            ("learner", "I've been working out three times a week since September."),
        ],
        extend=[
            ("I gave up coffee.", "the short sentence"),
            ("I gave up coffee two months ago.", "WHEN"),
            ("I used to drink four cups a day, so I gave up coffee two months ago.", "USED TO + the reason"),
            ("I used to drink four cups a day, so I gave up coffee two months ago, and I've been sleeping much better since then.", "AND + the result (for / since)"),
        ],
        build=[
            ("Use 'used to' + 'but': I ate sweets every day. Not now.", "I used to eat sweets every day, but I gave them up."),
            ("For or since: I work out. I started in March.", "I've been working out since March."),
            ("Add a purpose with 'to': I took up running.", "I took up running to feel healthier."),
            ("Use 'cut down on' + WHY: I use my phone less.", "I'm cutting down on my phone because I want to sleep better."),
        ],
        questions=[
            ("What did you use to do that you've given up?", "I used to stay up very late, but I've given it up because I work early."),
            ("What would you like to take up, and why?", "I'd like to take up tennis because I want to work out with friends."),
        ],
        speak="Talk about your habits: one you gave up, one you are cutting down on, and one you took up - with used to, for / since and why.",
    ),
    _lesson(
        "en-p16", 4, 4, "B1", "Advice: think over, go for, point out",
        "give and ask for advice in long, polite sentences",
        words=[
            ("think over", "think carefully before deciding", "ölçüb-biçmək, yaxşı düşünmək", "Think it over before you decide."),
            ("go for", "choose, try to get", "seçmək, cəhd etmək", "If you like it, go for it!"),
            ("point out", "show or mention a fact", "qeyd etmək, diqqətə çatdırmaq", "She pointed out a mistake."),
            ("talk into", "persuade someone to do something", "razı salmaq, dilə tutmaq", "He talked me into buying it."),
            ("turn down", "say no to an offer", "rədd etmək", "I turned down the job offer."),
            ("weigh up", "compare the good and bad sides", "müsbət-mənfi cəhətləri ölçmək", "Weigh up the pros and cons."),
        ],
        phrases=[
            ("If I were you, I'd think it over.", "careful advice", "Mən sənin yerində olsam, yaxşıca düşünərdim."),
            ("You should go for it!", "encouraging", "Bunu etməlisən, cəhd et!"),
            ("I'd like to point out that it's quite expensive.", "a polite warning", "Qeyd etmək istərdim ki, bu kifayət qədər bahadır."),
            ("Why don't you weigh up the pros and cons?", "a suggestion", "Niyə müsbət və mənfi cəhətləri ölçüb-biçmirsən?"),
            ("I turned it down because the salary was low.", "a decision + reason", "Maaş aşağı olduğu üçün imtina etdim."),
        ],
        grammar={
            "name": "Advice: should, If I were you, Why don't you ...?",
            "rule": ("Three ways to give advice: You should / shouldn't + verb. If I were you, I'd + verb. "
                     "Why don't you + verb? Make the advice longer with a reason: "
                     "'If I were you, I'd go for it, because it's a great chance.'"),
            "table": ["You should + verb + because ...", "If I were you, I'd + verb",
                      "Why don't you + verb?"],
            "examples": [("You should think it over because it's a big decision.", ""),
                         ("If I were you, I'd go for the job in Baku.", ""),
                         ("Why don't you talk it over with your family?", "")],
        },
        skills=["phrasal_verbs", "advice_modals", "second_conditional"],
        partner_role="friend who needs advice",
        dialogue=[
            ("partner", "I got a job offer in another city. What should I do?"),
            ("learner", "Congratulations! If I were you, I'd think it over carefully."),
            ("partner", "The salary is much better."),
            ("learner", "Then you should go for it. But I'd like to point out that the rent there is high."),
            ("partner", "Hmm. Maybe I should turn it down."),
            ("learner", "Why don't you weigh up the pros and cons before you decide?"),
        ],
        extend=[
            ("You should go for it.", "the short sentence"),
            ("You should go for the new job.", "WHAT"),
            ("You should go for the new job because the salary is much better.", "WHY"),
            ("You should go for the new job because the salary is much better, but think it over before you sign anything.", "BUT + a second piece of advice"),
        ],
        build=[
            ("Give advice with 'If I were you': turn down the offer.", "If I were you, I'd turn down the offer."),
            ("Add WHY: You should think it over.", "You should think it over because it's a big decision."),
            ("Make a suggestion with 'Why don't you': weigh up the pros and cons.", "Why don't you weigh up the pros and cons?"),
            ("Use 'talk into' in the past: My friend persuaded me to buy a car.", "My friend talked me into buying a car."),
        ],
        questions=[
            ("What's the best advice you have ever got?", "My dad told me to think things over before I decide, and he was right."),
            ("Did you ever turn down an offer? Why?", "Yes, I turned down a job because it was too far from home."),
        ],
        speak="A friend wants to move abroad. Give them advice: what they should go for, what they should think over, and one thing to point out. Use should, If I were you and Why don't you.",
    ),

    # ══ WEEK 5 - B1+: fluent daily speaking ══════════════════════════════════
    _lesson(
        "en-p17", 5, 1, "B1", "Travel: check in, get around, look around",
        "describe a trip in one long, fluent answer with extra details",
        words=[
            ("check in", "register at a hotel or airport", "qeydiyyatdan keçmək", "We checked in at the hotel at noon."),
            ("check out", "leave a hotel and pay", "oteldən çıxmaq", "We have to check out by eleven."),
            ("get around", "travel from place to place", "gəzib-dolaşmaq, hərəkət etmək", "We got around by metro."),
            ("look around", "walk and see a place", "ətrafa baxmaq, gəzmək", "We looked around the old town."),
            ("take off", "leave the ground (a plane)", "havaya qalxmaq", "The plane took off late."),
            ("stop over", "stay somewhere for a short time on a long trip", "yolüstü dayanmaq", "We stopped over in Istanbul."),
        ],
        phrases=[
            ("We checked in, left our bags and went to look around.", "the first hour", "Qeydiyyatdan keçib çantaları qoyduq və gəzməyə getdik."),
            ("The easiest way to get around is by metro.", "transport advice", "Gəzib-dolaşmağın ən asan yolu metrodur."),
            ("Our flight took off two hours late.", "a delay", "Təyyarəmiz iki saat gec havaya qalxdı."),
            ("We stopped over in Istanbul, which was great.", "an extra comment", "Yolüstü İstanbulda dayandıq, bu da əla idi."),
            ("We checked out early because we had a train to catch.", "a reason", "Qatara çatmalı olduğumuz üçün oteldən tez çıxdıq."),
        ],
        grammar={
            "name": "which / where for extra details",
            "rule": ("Add a comment or detail in the middle or end of a sentence: ', which' comments on the "
                     "whole idea ('We stopped over in Istanbul, which was great.'), 'where' adds a place "
                     "('the hotel where we stayed'). Put a comma before which when it is extra information."),
            "table": ["..., which + comment", "the place where + clause",
                      "the city, which is ..., was ..."],
            "examples": [("We got around by metro, which was fast and cheap.", ""),
                         ("The hotel where we checked in was next to the sea.", ""),
                         ("We looked around the old town, which was full of tourists.", "")],
        },
        skills=["phrasal_verbs", "non_defining_relative", "relative_clauses"],
        partner_role="friend back from a trip",
        dialogue=[
            ("partner", "How was your trip to Tbilisi?"),
            ("learner", "Amazing! The hotel where we checked in was in the old town."),
            ("partner", "How did you get around?"),
            ("learner", "We got around on foot, which was great because everything is close."),
            ("partner", "Did you have any problems?"),
            ("learner", "Only one. Our flight back took off three hours late, so we got home at night."),
        ],
        extend=[
            ("We looked around.", "the short sentence"),
            ("We looked around the old town.", "WHERE"),
            ("We looked around the old town on our first day, which was very sunny.", "WHEN + ', which' comment"),
            ("We looked around the old town on our first day, which was very sunny, and then we checked in at the hotel where my friend works.", "AND THEN + 'where' detail"),
        ],
        build=[
            ("Add a comment with ', which': We got around by bike.", "We got around by bike, which was really fun."),
            ("Use 'where': We checked in at a hotel. My cousin works there.", "We checked in at the hotel where my cousin works."),
            ("Use 'take off' + 'so': The plane was late. We missed the train.", "The plane took off late, so we missed the train."),
            ("Put three actions in one sentence: check in / leave our bags / look around.", "We checked in, left our bags and looked around the city."),
        ],
        questions=[
            ("Tell me about the best trip you've been on.", "We went to Sheki, where we looked around the palace, which was beautiful."),
            ("What's the best way to get around your city?", "The best way to get around is by metro, which is cheap, although it's crowded in the morning."),
        ],
        speak="Describe a trip from the start to the end in one long answer: check in, get around, look around, check out. Add which and where details.",
    ),
    _lesson(
        "en-p18", 5, 2, "B1", "Discussion: come up with, bring up, go along with",
        "take part in a discussion: give an idea, agree and disagree politely",
        words=[
            ("come up with", "think of an idea or plan", "(fikir) irəli sürmək, tapmaq", "She came up with a great idea."),
            ("bring up", "start talking about a subject", "(mövzunu) gündəmə gətirmək", "He brought up the problem at the meeting."),
            ("go along with", "agree with / accept", "razılaşmaq, qəbul etmək", "I'll go along with your plan."),
            ("back up", "support with facts or help", "dəstəkləmək, sübutla möhkəmləndirmək", "Can you back that up with numbers?"),
            ("talk over", "discuss", "müzakirə etmək", "Let's talk it over tomorrow."),
            ("rule out", "decide something is not possible", "istisna etmək", "We can't rule it out."),
        ],
        phrases=[
            ("I'd like to bring up one more point.", "adding a topic", "Daha bir məsələni qaldırmaq istərdim."),
            ("That's a good idea. I'll go along with it.", "agreeing", "Yaxşı fikirdir. Mən razıyam."),
            ("I see your point. However, I'm not sure it will work.", "polite disagreement", "Fikrinizi anlayıram. Lakin bunun alınacağına əmin deyiləm."),
            ("Can you back that up with an example?", "asking for support", "Bunu bir nümunə ilə əsaslandıra bilərsiniz?"),
            ("Let's not rule it out yet.", "keeping an option open", "Hələlik bunu istisna etməyək."),
        ],
        grammar={
            "name": "Opinion + reason + example",
            "rule": ("A strong B1+ answer: In my opinion / I think + idea + because + reason + for example / "
                     "for instance + example. Agree or disagree politely: 'I see your point, but ...' "
                     "'I'm not sure I agree, because ...'"),
            "table": ["In my view, ... because ...", "For example, ...",
                      "I see your point, but ... / However, ..."],
            "examples": [("In my view, we should come up with a cheaper plan because the budget is small.", ""),
                         ("For example, we could talk it over online instead of travelling.", ""),
                         ("I see your point, but I don't think we can rule it out.", "")],
        },
        skills=["phrasal_verbs", "discourse_markers", "linking_words"],
        partner_role="team leader in a meeting",
        dialogue=[
            ("partner", "We need more customers. Any ideas?"),
            ("learner", "I've come up with an idea. In my view, we should start a video channel."),
            ("partner", "Interesting. Can you back that up?"),
            ("learner", "Yes. For example, our competitor started one and doubled their sales."),
            ("partner", "But it's expensive. Maybe we should rule it out."),
            ("learner", "I see your point, but let's not rule it out yet. Can we talk it over next week?"),
        ],
        extend=[
            ("I came up with an idea.", "the short sentence"),
            ("I came up with an idea for our team trip.", "FOR WHAT"),
            ("I came up with an idea for our team trip, which is to go hiking, because it's cheap.", "', which' + WHY"),
            ("I came up with an idea for our team trip, which is to go hiking, because it's cheap and, for example, we could bring our own food.", "FOR EXAMPLE + a detail"),
        ],
        build=[
            ("Give an opinion + reason: working from home / good.", "In my view, working from home is good because we save time."),
            ("Disagree politely: 'We should cancel the project.'", "I see your point, but I don't think we should cancel it."),
            ("Use 'bring up' in the past + WHEN: He mentioned the problem.", "He brought up the problem at the end of the meeting."),
            ("Add an example: We can save money.", "We can save money. For example, we can cut down on taxis."),
        ],
        questions=[
            ("Is it better to work from home or in an office? Why?", "In my view, working from home is better because I can focus. However, I miss my colleagues."),
            ("Tell me about a good idea you came up with.", "I came up with the idea of a weekly English club at work, which everyone went along with."),
        ],
        speak="Discussion: should phones be banned at school? Give your opinion with a reason and an example, then answer the tutor's counter-arguments politely.",
    ),
    _lesson(
        "en-p19", 5, 3, "B1", "Changes and goals: move on, set up, carry on",
        "talk about a big change in your life and your goals for the future",
        words=[
            ("move on", "start something new, leave the past", "irəli getmək, keçmişi arxada qoymaq", "It was time to move on."),
            ("set up", "start a business or organisation", "qurmaq, yaratmaq", "She set up her own company."),
            ("carry on", "continue", "davam etmək", "I'll carry on learning English."),
            ("settle in", "start to feel at home in a new place", "yeni yerə uyğunlaşmaq", "It took a month to settle in."),
            ("go through", "experience something difficult", "yaşamaq, keçmək (çətinlik)", "We went through a hard time."),
            ("aim for", "try to reach a goal", "hədəfləmək", "I'm aiming for B2 next year."),
        ],
        phrases=[
            ("After five years in that job, I decided to move on.", "a change", "O işdə beş ildən sonra irəli getməyə qərar verdim."),
            ("It took me a few months to settle in.", "adapting", "Uyğunlaşmaq mənə bir neçə ay çəkdi."),
            ("We went through a difficult time, but we didn't give up.", "a hard period", "Çətin bir dövr yaşadıq, amma təslim olmadıq."),
            ("I'd love to set up my own business one day.", "a dream", "Bir gün öz biznesimi qurmaq istərdim."),
            ("I'm going to carry on so that I can reach B2.", "a goal with a purpose", "B2-yə çatmaq üçün davam edəcəyəm."),
        ],
        grammar={
            "name": "Purpose and contrast: so that, in order to, even though",
            "rule": ("Say WHY you do something with to / in order to + verb or so that + clause: "
                     "'I study every day so that I can speak at work.' Say a surprising contrast with even "
                     "though: 'Even though it was hard, I carried on.'"),
            "table": ["... to / in order to + verb", "... so that + I can / will ...",
                      "Even though + clause, clause"],
            "examples": [("I moved to Baku in order to find a better job.", ""),
                         ("I'm carrying on with English so that I can move on to B2.", ""),
                         ("Even though it was hard to settle in, I never gave up.", "")],
        },
        skills=["phrasal_verbs", "gerund_infinitive", "linking_words"],
        partner_role="interviewer for a scholarship",
        dialogue=[
            ("partner", "Tell me about a big change in your life."),
            ("learner", "Two years ago I moved to a new city in order to study."),
            ("partner", "Was it easy?"),
            ("learner", "No. Even though people were friendly, it took me months to settle in."),
            ("partner", "And what are your goals now?"),
            ("learner", "I'm going to carry on studying so that I can set up my own company one day."),
        ],
        extend=[
            ("I moved on.", "the short sentence"),
            ("I moved on to a new job last year.", "TO WHAT + WHEN"),
            ("Even though I liked my team, I moved on to a new job last year.", "EVEN THOUGH + a contrast"),
            ("Even though I liked my team, I moved on to a new job last year so that I could learn new skills, and it has turned out really well.", "SO THAT + purpose, AND + result"),
        ],
        build=[
            ("Add a purpose with 'so that': I practise every day.", "I practise every day so that I can speak more fluently."),
            ("Join with 'even though': It was hard. I carried on.", "Even though it was hard, I carried on."),
            ("Use 'in order to': I moved to the city. I wanted to study.", "I moved to the city in order to study."),
            ("Use 'aim for' + WHEN + WHY: my goal is B2.", "I'm aiming for B2 next year because I need it for work."),
        ],
        questions=[
            ("What is the biggest change you have gone through?", "I went through a big change when I moved abroad. Even though it was hard, I settled in quickly."),
            ("What are you aiming for in the next two years?", "I'm aiming for a better job, so I'm carrying on with English in order to pass an interview."),
        ],
        speak="Tell the story of a big change in your life and your goals now: what you went through, how you settled in or moved on, and what you are aiming for - with so that, in order to and even though.",
    ),
    _lesson(
        "en-p20", 5, 4, "B1", "B1+ final: one long story with phrasal verbs",
        "speak for several minutes about your life, using phrasal verbs and long sentences",
        words=[
            ("look back on", "remember the past", "geriyə baxmaq, xatırlamaq", "I look back on that year with a smile."),
            ("grow up", "become an adult", "böyümək", "I grew up in a small village."),
            ("turn into", "become something different", "çevrilmək", "The hobby turned into a job."),
            ("come true", "happen as you wished", "gerçəkləşmək", "My dream came true."),
            ("sum up", "say the main points shortly", "yekunlaşdırmaq", "To sum up, it was a great year."),
            ("keep on", "continue doing, again and again", "davam etmək, təkrar-təkrar etmək", "I kept on practising."),
        ],
        phrases=[
            ("When I look back on my childhood, I remember ...", "starting a memory", "Uşaqlığıma geri baxanda xatırlayıram ki ..."),
            ("I grew up in a town where everybody knew each other.", "background with where", "Hamının bir-birini tanıdığı bir şəhərdə böyüdüm."),
            ("What started as a hobby turned into a career.", "a change", "Hobbi kimi başlayan şey karyeraya çevrildi."),
            ("I kept on trying until my dream came true.", "never giving up", "Arzum gerçəkləşənə qədər cəhd etməyə davam etdim."),
            ("To sum up, I'm proud of how far I've come.", "ending", "Yekun olaraq, bu qədər irəlilədiyim üçün fəxr edirəm."),
        ],
        grammar={
            "name": "A fluent answer: the whole toolbox",
            "rule": ("Put everything together: background (I grew up in ... where ...), a story with time "
                     "words (at first, then, in the end), reasons and contrasts (because, although), extra "
                     "details (which, who), purpose (so that), and an ending (to sum up). Use a phrasal verb "
                     "in almost every sentence."),
            "table": ["background: where / who", "story: at first → then → in the end",
                      "why / contrast / purpose: because · although · so that", "ending: To sum up, ..."],
            "examples": [("I grew up in a small town where everybody knew each other.", ""),
                         ("Although it was hard at first, I kept on practising, and in the end my dream came true.", ""),
                         ("To sum up, when I look back on it, I'm proud of how far I've come.", "")],
        },
        skills=["phrasal_verbs", "linking_words", "discourse_markers", "relative_clauses"],
        partner_role="examiner",
        dialogue=[
            ("partner", "Tell me a little about yourself."),
            ("learner", "I grew up in a small town where everybody knew each other."),
            ("partner", "How did you start learning English?"),
            ("learner", "At first it was a hobby, but it turned into something I need for my job."),
            ("partner", "What was the hardest part?"),
            ("learner", "Phrasal verbs! Although they were hard, I kept on practising, and now I use them every day."),
        ],
        extend=[
            ("I grew up in Ganja.", "the short sentence"),
            ("I grew up in Ganja, where my grandparents had a big garden.", "', where' detail"),
            ("I grew up in Ganja, where my grandparents had a big garden, and when I look back on those years, I feel happy.", "AND WHEN + a feeling"),
            ("I grew up in Ganja, where my grandparents had a big garden, and when I look back on those years, I feel happy because we spent every summer outside.", "BECAUSE + the reason"),
        ],
        build=[
            ("One sentence with 'where': I grew up in a village. Everybody knew each other.", "I grew up in a village where everybody knew each other."),
            ("Use 'turn into' + 'although': My hobby became my job. It was not planned.", "Although I didn't plan it, my hobby turned into my job."),
            ("Use 'keep on' + 'until': I practised. My dream came true.", "I kept on practising until my dream came true."),
            ("End an answer with 'To sum up': I'm happy with my progress.", "To sum up, I'm really happy with my progress."),
        ],
        questions=[
            ("Tell me about where you grew up and how it has changed.", "I grew up in a small town, which has turned into a busy city. Although I miss the old days, I like it now."),
            ("When you look back on this course, what has changed in your English?", "When I look back on it, I can see that my sentences are much longer, because I use phrasal verbs and linking words."),
        ],
        speak=("Final B1+ test, about 5 minutes: tell the story of your life so far - where you grew up, a big "
               "change, a problem you sorted out, and your goals. Use long sentences with phrasal verbs. The "
               "tutor only asks follow-up questions, then gives feedback: two strong points and two things "
               "to practise."),
    ),
]

COURSE = {
    "id": "english_phrasal_speaking",
    "language": "english",
    "about": ("Everyday English for speaking: learn the phrasal verbs people really use every day and "
              "turn short answers into long, natural sentences - from A2 to B1+ in five weeks."),
    "learner": ("The learner already speaks basic English (A2) and wants to speak about daily life. This "
                "course teaches everyday phrasal verbs and how to build longer sentences with them: add "
                "when, where, who with, why, a contrast, a detail and a result. Always push them to make "
                "their answers longer."),
    "title": "English · A2 → B1+ · Phrasal verbs for daily speaking",
    "outcomes": [
        "Use 100+ everyday phrasal verbs about your day, people, work and feelings",
        "Turn a 3-word answer into a long, natural sentence",
        "Add when, where, who with, why, a contrast and a result to any sentence",
        "Put it, them and me in the right place: pick it up, not pick up it",
        "Tell a story with a background, a surprise and an ending",
        "Give opinions and advice, agree and disagree politely",
    ],
    "weeks": [
        {"week": 1, "title": "My day with phrasal verbs", "band": "A2"},
        {"week": 2, "title": "People, messages and plans", "band": "A2"},
        {"week": 3, "title": "Problems, work and stories", "band": "B1"},
        {"week": 4, "title": "Feelings, habits and advice", "band": "B1"},
        {"week": 5, "title": "Fluent daily speaking", "band": "B1+"},
    ],
    "lessons": LESSONS,
}
