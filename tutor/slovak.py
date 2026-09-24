"""
tutor/slovak.py - the Slovak course, A1 to B2.

The same shape as the English course in curriculum.py: every grammar skill
with its name, level and hint, the rule in one simple sentence, examples and
what the board draws; then the stages and their units. Everything the learner
reads is in simple Slovak - the learner asked for explanations in Slovak only.

Skill ids start with "sk_" so they never meet the English ones in the shared
tables (SKILL_TIPS, SKILL_BOARD, SIMPLE_RULES).
"""
from __future__ import annotations

# id -> (name, band, hint, simple rule, examples, board)
_SK: dict[str, tuple[str, str, str, str, list[str], dict]] = {
    # ── A1 ──
    "sk_byt": (
        "sloveso byť (som, si, je)", "A1", "ja som, ty si, on je, my sme, vy ste, oni sú",
        "Byť: ja som, ty si, on/ona je, my sme, vy ste, oni sú.",
        ["Som z Baku.", "Ste doma?"],
        {"formula": ["ja som · ty si · on/ona je", "my sme · vy ste · oni sú"],
         "diagram": {"kind": "split", "left": {"title": "jeden", "lines": ["ja som", "ty si", "on je"]},
                     "right": {"title": "viac", "lines": ["my sme", "vy ste", "oni sú"]}}}),
    "sk_mat": (
        "sloveso mať", "A1", "mám, máš, má, máme, máte, majú",
        "Mať: mám, máš, má, máme, máte, majú.",
        ["Mám brata.", "Máš čas?"],
        {"formula": ["ja mám · ty máš · on má", "my máme · vy máte · oni majú"],
         "diagram": {"kind": "blocks", "items": ["Ja", "mám", "sestru"]}}),
    "sk_present": (
        "prítomný čas (volám, robím, píšem)", "A1", "tri typy: volám, robím, píšem",
        "V prítomnom čase má sloveso koncovku podľa osoby: volám, robím, píšem.",
        ["Pracujem v kancelárii.", "Čo robíš večer?"],
        {"formula": ["-ám: volám, voláš, volá", "-ím / -em: robím, píšem"],
         "diagram": {"kind": "split", "left": {"title": "volať", "lines": ["volám", "voláš", "volajú"]},
                     "right": {"title": "robiť", "lines": ["robím", "robíš", "robia"]}}}),
    "sk_negation": (
        "zápor (ne-)", "A1", "nerobím, nemám, nie som",
        "Zápor: ne- píšeme spolu so slovesom: nerobím. Pri byť: nie som.",
        ["Nemám čas.", "Nie som unavený."],
        {"formula": ["ne + sloveso: nerobím, nemám", "byť: nie som, nie si, nie je"],
         "diagram": {"kind": "flow", "items": ["mám", "→", "nemám"]}}),
    "sk_questions": (
        "otázky (kde, kedy, čo)", "A1", "Kde bývaš? Máš čas?",
        "Otázku začni otázkovým slovom: Kde? Kedy? Čo? Pri otázke áno/nie ide hlas hore.",
        ["Kde pracuješ?", "Máš dnes čas?"],
        {"formula": ["otázkové slovo + sloveso: Kde bývaš?", "áno/nie: Máš čas? (hlas hore)"],
         "diagram": {"kind": "blocks", "items": ["Kde", "pracuješ", "?"]}}),
    "sk_gender": (
        "rod podstatných mien (ten, tá, to)", "A1", "ten stôl, tá kniha, to mesto",
        "Každé podstatné meno má rod: ten (stôl), tá (kniha), to (mesto).",
        ["To je môj dom.", "Tá káva je dobrá."],
        {"formula": ["ten: stôl, brat (spoluhláska)", "tá: kniha (-a) · to: mesto (-o, -e)"],
         "diagram": {"kind": "blocks", "items": ["ten stôl", "tá kniha", "to mesto"]}}),
    "sk_adj_agreement": (
        "zhoda prídavného mena (nový, nová, nové)", "A1", "nový dom, nová kniha, nové auto",
        "Prídavné meno má rovnaký rod ako podstatné meno: nový dom, nová kniha, nové auto.",
        ["Mám nový telefón.", "To je pekná izba."],
        {"formula": ["ten: -ý / -y (nový)", "tá: -á / -a (nová) · to: -é / -e (nové)"],
         "diagram": {"kind": "blocks", "items": ["nový dom", "nová kniha", "nové auto"]}}),
    "sk_accusative": (
        "4. pád (koho? čo?)", "A1", "pijem kávu, vidím ženu, mám brata",
        "Po slovesách ako mať, vidieť, chcieť je 4. pád: káva → pijem kávu.",
        ["Pijem kávu.", "Poznám tvojho brata."],
        {"formula": ["káva → kávu · žena → ženu", "brat → brata · stôl → stôl"],
         "diagram": {"kind": "split", "left": {"title": "kto? čo?", "lines": ["káva", "žena", "brat"]},
                     "right": {"title": "koho? čo?", "lines": ["pijem kávu", "vidím ženu", "mám brata"]}}}),
    "sk_plural": (
        "množné číslo", "A1", "kniha → knihy, dom → domy, mesto → mestá",
        "Množné číslo: kniha → knihy, dom → domy, mesto → mestá.",
        ["Mám dve sestry.", "Tie domy sú veľké."],
        {"formula": ["-a → -y: kniha → knihy", "dom → domy · mesto → mestá"],
         "diagram": {"kind": "split", "left": {"title": "jeden", "lines": ["kniha", "dom", "mesto"]},
                     "right": {"title": "viac", "lines": ["knihy", "domy", "mestá"]}}}),
    "sk_possessive": (
        "môj, tvoj, náš", "A1", "môj brat, moja sestra, moje auto",
        "Môj, tvoj, náš majú rod ako podstatné meno: môj brat, moja sestra, moje auto.",
        ["Moja mama je doma.", "Kde je tvoje auto?"],
        {"formula": ["môj / moja / moje", "tvoj / tvoja / tvoje · náš / naša / naše"],
         "diagram": {"kind": "blocks", "items": ["môj brat", "moja sestra", "moje auto"]}}),
    "sk_numbers": (
        "čísla a počet (1 kniha, 2 knihy, 5 kníh)", "A1", "jedna kniha, dve knihy, päť kníh",
        "Po 1 je jednotné číslo, po 2, 3, 4 množné, po 5 a viac 2. pád: päť kníh.",
        ["Mám dve deti.", "Pracujem päť dní."],
        {"formula": ["1 kniha · 2-4 knihy", "5 a viac: kníh (2. pád)"],
         "diagram": {"kind": "ladder", "items": ["1 kniha", "2 knihy", "5 kníh"]}}),
    "sk_reflexive": (
        "slovesá so sa a si", "A1", "volám sa, učím sa, sadnem si",
        "Niektoré slovesá majú sa alebo si: volám sa, učím sa, sadnem si.",
        ["Volám sa Taleh.", "Učím sa po slovensky."],
        {"formula": ["sa: volám sa, učím sa, teším sa", "si: sadnem si, kúpim si"],
         "diagram": {"kind": "blocks", "items": ["Volám", "sa", "Taleh"]}}),
    "sk_modals": (
        "chcieť, môcť, musieť + -ť", "A1", "chcem spať, môžem prísť, musím pracovať",
        "Po chcem, môžem, musím ide sloveso na -ť: chcem spať.",
        ["Chcem piť vodu.", "Musím ísť do práce."],
        {"formula": ["chcem / môžem / musím + -ť", "chcem spať · musím pracovať"],
         "diagram": {"kind": "blocks", "items": ["Musím", "pracovať", "dnes"]}}),
    "sk_word_order": (
        "poradie slov (som, sa na 2. mieste)", "A1", "Včera som bol doma. Ako sa máš?",
        "Krátke slová som, si, sa, mi stoja vo vete na druhom mieste: Včera som bol doma.",
        ["Včera som bol v práci.", "Ako sa máš?"],
        {"formula": ["1. slovo + som / sa / mi + zvyšok", "Včera som bol doma."],
         "diagram": {"kind": "blocks", "items": ["Včera", "som", "bol", "doma"]}}),

    # ── A2 ──
    "sk_past": (
        "minulý čas (robil som, robila som)", "A2", "robil som, robila si, robili sme",
        "Minulý čas: sloveso na -l, -la, -li + som / si: robil som, robila som.",
        ["Včera som pracoval doma.", "Kde si bola?"],
        {"formula": ["on robil · ona robila · oni robili", "ja: robil som · ty: robil si"],
         "diagram": {"kind": "timeline", "items": [{"type": "point", "at": -0.6, "label": "včera som robil"}]}}),
    "sk_future": (
        "budúci čas (budem + -ť)", "A2", "budem pracovať, budeš čítať",
        "Budúci čas: budem, budeš, bude + sloveso na -ť: budem pracovať.",
        ["Zajtra budem pracovať.", "Čo budeš robiť?"],
        {"formula": ["budem, budeš, bude + -ť", "budeme, budete, budú + -ť"],
         "diagram": {"kind": "timeline", "items": [{"type": "point", "at": 0.6, "label": "zajtra budem pracovať"}]}}),
    "sk_aspect": (
        "vid slovies (písať / napísať)", "A2", "píšem (proces) / napíšem (výsledok)",
        "Nedokonavé sloveso je dej, ktorý trvá: písať. Dokonavé je hotový výsledok: napísať.",
        ["Celý deň píšem list.", "Zajtra napíšem list."],
        {"formula": ["nedokonavé: písať, robiť (proces)", "dokonavé: napísať, urobiť (výsledok)"],
         "diagram": {"kind": "timeline", "items": [
             {"type": "range", "from": -0.7, "to": -0.1, "label": "písal som (proces)"},
             {"type": "point", "at": 0.5, "label": "napíšem (hotovo)"}]}}),
    "sk_locative": (
        "6. pád (v meste, na stole, o práci)", "A2", "v Bratislave, na stole, o práci",
        "Kde? O čom? v / na / o + 6. pád: v meste, na stole, o práci.",
        ["Bývam v Bratislave.", "Kniha je na stole."],
        {"formula": ["v / na / o + 6. pád", "mesto → v meste · práca → o práci"],
         "diagram": {"kind": "blocks", "items": ["Bývam", "v", "Bratislave"]}}),
    "sk_genitive": (
        "2. pád (bez, z, do, od)", "A2", "bez cukru, z Baku, do práce, veľa ľudí",
        "Po bez, z, do, od, u a po veľa je 2. pád: bez cukru, do práce.",
        ["Idem do práce.", "Som z Azerbajdžanu."],
        {"formula": ["bez / z / do / od / u + 2. pád", "práca → do práce · cukor → bez cukru"],
         "diagram": {"kind": "blocks", "items": ["Idem", "do", "práce"]}}),
    "sk_dative": (
        "3. pád (komu? čomu?)", "A2", "volám mame, píšem bratovi, idem k lekárovi",
        "Komu? 3. pád: volám mame, píšem bratovi, idem k lekárovi.",
        ["Volám mame každý deň.", "Páči sa mi to."],
        {"formula": ["mama → mame · brat → bratovi", "k / proti + 3. pád: k lekárovi"],
         "diagram": {"kind": "blocks", "items": ["Volám", "mame", "večer"]}}),
    "sk_instrumental": (
        "7. pád (s kým? čím?)", "A2", "s kamarátom, autom, pred domom",
        "S kým? Čím? s / pred / za / nad / pod + 7. pád: s kamarátom, pred domom.",
        ["Idem s kamarátom.", "Cestujem autom."],
        {"formula": ["s / pred / za + 7. pád", "kamarát → s kamarátom · auto → autom"],
         "diagram": {"kind": "blocks", "items": ["Idem", "s", "kamarátom"]}}),
    "sk_kde_kam": (
        "kde? / kam? (v škole / do školy)", "A2", "som v práci (kde) / idem do práce (kam)",
        "Kde? (miesto) v / na + 6. pád. Kam? (smer) do + 2. pád, na + 4. pád.",
        ["Som v škole.", "Idem do školy."],
        {"formula": ["kde? v škole, na pošte, doma", "kam? do školy, na poštu, domov"],
         "diagram": {"kind": "split", "left": {"title": "kde? (som)", "lines": ["v škole", "na pošte", "doma"]},
                     "right": {"title": "kam? (idem)", "lines": ["do školy", "na poštu", "domov"]}}}),
    "sk_motion": (
        "ísť / chodiť", "A2", "idem teraz / chodím často",
        "Ísť je jeden pohyb teraz: idem do práce. Chodiť je často: chodím do práce každý deň.",
        ["Teraz idem domov.", "Chodím do posilňovne."],
        {"formula": ["ísť: teraz, jedným smerom", "chodiť: často, opakovane"],
         "diagram": {"kind": "timeline", "items": [
             {"type": "repeat", "from": -0.8, "to": -0.2, "n": 5, "label": "chodím (často)"},
             {"type": "point", "at": 0, "label": "idem (teraz)"}]}}),
    "sk_comparatives": (
        "stupňovanie (lacnejší, najlacnejší)", "A2", "dobrý - lepší - najlepší",
        "Stupňovanie: -ší / -ejší a naj-: lacný, lacnejší, najlacnejší.",
        ["Toto auto je lacnejšie.", "Je to najlepšia reštaurácia."],
        {"formula": ["-ší / -ejší: lacný → lacnejší", "naj- + -ší: najlacnejší · dobrý → lepší"],
         "diagram": {"kind": "ladder", "items": ["lacný", "lacnejší", "najlacnejší"]}}),
    "sk_pronoun_cases": (
        "zámená v pádoch (ma, mi, ho, mu)", "A2", "vidíš ma? zavolám ti, poznám ho",
        "Zámená menia tvar: ja → ma, mi. Ty → ťa, ti. On → ho, mu.",
        ["Zavolám ti zajtra.", "Poznáš ho?"],
        {"formula": ["ja: ma (4.) · mi (3.) · ty: ťa · ti", "on: ho (4.) · mu (3.) · ona: ju · jej"],
         "diagram": {"kind": "blocks", "items": ["Zavolám", "ti", "zajtra"]}}),
    "sk_word_choice": (
        "výber slova", "A2", "vedieť / poznať, robiť / urobiť, mať rád",
        "Vyber slovo so správnym významom: viem (fakt, schopnosť), poznám (človeka, miesto).",
        ["Viem, kde je obchod.", "Poznám tvojho brata."],
        {"formula": ["vedieť: viem plávať, viem, kde je", "poznať: poznám Petra, poznám mesto"],
         "diagram": {"kind": "split", "left": {"title": "vedieť", "lines": ["viem plávať", "viem, kde je"]},
                     "right": {"title": "poznať", "lines": ["poznám Petra", "poznám mesto"]}}}),

    # ── B1 ──
    "sk_conditional": (
        "podmieňovací spôsob (by som)", "B1", "chcel by som, keby som mal čas",
        "Podmienka: tvar na -l + by: urobil by som. Keby som mal čas, išiel by som.",
        ["Chcel by som kávu.", "Keby som mal čas, išiel by som."],
        {"formula": ["-l + by som: chcel by som", "keby som + -l, … by som + -l"],
         "diagram": {"kind": "flow", "items": ["keby som mal čas", "→", "išiel by som"]}}),
    "sk_imperative": (
        "rozkazovací spôsob (rob! poďme!)", "B1", "píš, píšte, poďme, nerob to",
        "Rozkaz: píš! (ty), píšte! (vy), píšme! (my). Zápor: nepíš!",
        ["Poď sem!", "Nerobte si starosti."],
        {"formula": ["ty: rob · vy: robte · my: robme", "zápor: nerob, nerobte"],
         "diagram": {"kind": "blocks", "items": ["Poďme", "do", "kina"]}}),
    "sk_relative": (
        "vzťažné vety (ktorý, ktorá, ktoré)", "B1", "muž, ktorý tu býva; kniha, ktorú čítam",
        "Ktorý má rod a pád podľa vety: muž, ktorý tu býva; kniha, ktorú čítam.",
        ["To je muž, ktorý tu pracuje.", "Kniha, ktorú čítam, je dobrá."],
        {"formula": ["ten → ktorý · tá → ktorá · to → ktoré", "kniha, ktorú čítam (4. pád)"],
         "diagram": {"kind": "flow", "items": ["kniha", "→", "ktorú", "→", "čítam"]}}),
    "sk_ze_aby": (
        "že, aby, keď, pretože", "B1", "viem, že…; chcem, aby…; pretože…",
        "Že je fakt, aby je želanie alebo cieľ (aby + tvar na -l), pretože je dôvod.",
        ["Myslím, že má pravdu.", "Chcem, aby si prišiel."],
        {"formula": ["že: Viem, že prší.", "aby + -l: Chcem, aby si prišiel."],
         "diagram": {"kind": "split", "left": {"title": "že (fakt)", "lines": ["viem, že prší"]},
                     "right": {"title": "aby (cieľ)", "lines": ["chcem, aby si prišiel"]}}}),
    "sk_prefixes": (
        "predpony slovies (pri-, od-, vy-, pre-)", "B1", "prísť, odísť, vyjsť, prejsť",
        "Predpona mení význam slovesa: ísť → prísť (sem), odísť (preč), vyjsť (von).",
        ["Prišiel som neskoro.", "Odišla o piatej."],
        {"formula": ["pri- sem · od- preč · vy- von", "pre- cez · za- dnu, za"],
         "diagram": {"kind": "blocks", "items": ["prísť", "odísť", "vyjsť", "prejsť"]}}),
    "sk_verb_cases": (
        "slovesá s pádom (čakať na, báť sa)", "B1", "čakám na autobus, bojím sa psa, pomáham mame",
        "Niektoré slovesá majú stálu predložku a pád: čakať na + 4. pád, báť sa + 2. pád.",
        ["Čakám na autobus.", "Bojím sa psov."],
        {"formula": ["čakať na / myslieť na + 4. pád", "báť sa + 2. pád · pomáhať + 3. pád"],
         "diagram": {"kind": "split", "left": {"title": "sloveso", "lines": ["čakať na", "báť sa", "pomáhať"]},
                     "right": {"title": "príklad", "lines": ["čakám na teba", "bojím sa tmy", "pomáham mame"]}}}),
    "sk_plural_cases": (
        "množné číslo v pádoch", "B1", "s kamarátmi, v mestách, do obchodov",
        "Aj v množnom čísle sa menia koncovky: s kamarátmi, v mestách, do obchodov.",
        ["Idem s kamarátmi.", "Bol som v mnohých mestách."],
        {"formula": ["7. pád: s kamarátmi · so ženami", "6. pád: v mestách · o ľuďoch"],
         "diagram": {"kind": "blocks", "items": ["Idem", "s", "kamarátmi"]}}),
    "sk_se_passive": (
        "sa namiesto osoby (predáva sa)", "B1", "tu sa hovorí po slovensky; dom sa predáva",
        "Keď nie je dôležité, kto to robí: sa + sloveso: Dom sa predáva.",
        ["Tu sa hovorí po slovensky.", "Ako sa to píše?"],
        {"formula": ["sa + 3. osoba: predáva sa", "Ako sa to povie po slovensky?"],
         "diagram": {"kind": "blocks", "items": ["Tu", "sa", "hovorí", "po slovensky"]}}),

    # ── B2 ──
    "sk_passive": (
        "trpný rod (je postavený)", "B2", "Most bol postavený v roku 1990.",
        "Trpný rod: byť + tvar na -ný / -tý: Most bol postavený v roku 1990.",
        ["Most bol postavený v roku 1990.", "Obchod je zatvorený."],
        {"formula": ["byť + -ný / -tý", "postaviť → postavený · zavrieť → zatvorený"],
         "diagram": {"kind": "shift", "items": [["Postavili most.", "Most bol postavený."]]}}),
    "sk_past_conditional": (
        "minulá podmienka (bol by som prišiel)", "B2", "keby som bol vedel, bol by som prišiel",
        "Pre minulosť, ktorá sa nestala: keby som bol vedel, bol by som prišiel.",
        ["Keby som bol vedel, bol by som prišiel.", "Bola by som ti zavolala."],
        {"formula": ["keby som bol + -l", "bol by som + -l"],
         "diagram": {"kind": "timeline", "items": [{"type": "cross", "at": -0.5, "label": "bol by som prišiel"}]}}),
    "sk_reported": (
        "nepriama reč (povedal, že…)", "B2", "Povedal, že je unavený.",
        "Nepriama reč: že + čas ostáva ako v pôvodnej vete: Som unavený. → Povedal, že je unavený.",
        ["Povedala, že príde.", "Spýtal sa, či mám čas."],
        {"formula": ["Som unavený. → povedal, že je unavený", "otázka áno/nie → či: spýtal sa, či…"],
         "diagram": {"kind": "shift", "items": [["Som unavený.", "povedal, že je unavený"],
                                                 ["Máš čas?", "spýtal sa, či mám čas"]]}}),
    "sk_verbal_nouns": (
        "podstatné mená zo slovies (čítanie)", "B2", "čítať → čítanie, učiť → učenie",
        "Zo slovesa urobíš podstatné meno pomocou -nie / -tie: čítať → čítanie.",
        ["Čítanie ma baví.", "Plávanie je zdravé."],
        {"formula": ["-ať → -anie: čítať → čítanie", "-iť → -enie: učiť → učenie"],
         "diagram": {"kind": "flow", "items": ["čítať", "→", "čítanie"]}}),
    "sk_participles": (
        "príčastia (pracujúci, napísaný)", "B2", "pracujúci ľudia, napísaný list",
        "Príčastie je sloveso ako prídavné meno: pracujúci človek (ktorý pracuje), napísaný list.",
        ["Hovoriaci muž je môj učiteľ.", "List je už napísaný."],
        {"formula": ["-úci / -iaci = ktorý robí: pracujúci", "-ný / -tý = ktorý je urobený: napísaný"],
         "diagram": {"kind": "split", "left": {"title": "robí (-úci)", "lines": ["pracujúci človek", "hovoriaci muž"]},
                     "right": {"title": "je urobený (-ný)", "lines": ["napísaný list", "zatvorené okno"]}}}),
    "sk_discourse": (
        "spájacie výrazy (však, navyše, preto)", "B2", "však, navyše, preto, na druhej strane",
        "Tieto slová spájajú myšlienky: však (ale), navyše (a ešte), preto (výsledok).",
        ["Je to drahé, navyše je to ďaleko.", "Pršalo, preto sme ostali doma."],
        {"formula": ["však = ale · navyše = a ešte", "preto = výsledok · na druhej strane = kontrast"],
         "diagram": {"kind": "flow", "items": ["pršalo", "→", "preto", "→", "ostali sme doma"]}}),
    "sk_collocations": (
        "ustálené spojenia", "B2", "mať pravdu, dať pozor, robiť si starosti",
        "Niektoré slová idú vždy spolu: mať pravdu, dať pozor, robiť si starosti.",
        ["Máš pravdu.", "Daj si pozor."],
        {"formula": ["mať pravdu · dať pozor", "robiť si starosti · urobiť rozhodnutie"],
         "diagram": {"kind": "blocks", "items": ["mať pravdu", "dať pozor"]}}),
}

SLOVAK_SKILLS: dict[str, tuple[str, str, str]] = {sid: (v[0], v[1], v[2]) for sid, v in _SK.items()}
SLOVAK_TIPS: dict[str, tuple[str, list[str]]] = {sid: (v[3], v[4]) for sid, v in _SK.items()}
SLOVAK_BOARD: dict[str, dict] = {sid: v[5] for sid, v in _SK.items()}
SLOVAK_RULES: dict[str, str] = {sid: v[3] for sid, v in _SK.items()}


def _unit(uid: str, title: str, skills: list[str], can_do: str, examples: list[str]) -> dict:
    return {"id": uid, "title": title, "skills": skills, "can_do": can_do, "examples": examples}


SLOVAK_STAGES: list[dict] = [
    {"id": "A1.1", "band": "A1", "title": "Prvé vety", "exit_score": 10, "units": [
        _unit("sk-01", "Byť, mať a otázky", ["sk_byt", "sk_mat", "sk_questions"],
              "povedať, kto som a čo mám, a opýtať sa",
              ["Som Taleh. Som z Baku.", "Mám brata a sestru.", "Kde bývaš?"]),
        _unit("sk-02", "Prítomný čas a zápor", ["sk_present", "sk_negation"],
              "povedať, čo robím každý deň",
              ["Pracujem v kancelárii.", "Ráno pijem kávu.", "Nemám dnes čas."]),
        _unit("sk-03", "Rod, prídavné mená, môj", ["sk_gender", "sk_adj_agreement", "sk_possessive"],
              "opísať veci a ľudí okolo seba",
              ["Mám nový telefón.", "Moja izba je malá.", "To je pekné mesto."]),
    ]},
    {"id": "A1.2", "band": "A1", "title": "Veci a ľudia okolo mňa", "exit_score": 19, "units": [
        _unit("sk-04", "4. pád a množné číslo", ["sk_accusative", "sk_plural"],
              "povedať, čo mám, chcem a vidím",
              ["Pijem kávu bez cukru.", "Mám dve sestry.", "Vidím tvojho brata."]),
        _unit("sk-05", "Chcem, môžem, musím; sa a si", ["sk_modals", "sk_reflexive"],
              "hovoriť o plánoch a povinnostiach",
              ["Chcem sa učiť po slovensky.", "Musím ísť do práce.", "Volám sa Taleh."]),
        _unit("sk-06", "Čísla a poradie slov", ["sk_numbers", "sk_word_order"],
              "počítať veci a stavať krátke vety",
              ["Pracujem päť dní v týždni.", "Mám dve deti.", "Ako sa máš?"]),
    ]},
    {"id": "A2.1", "band": "A2", "title": "Minulosť a budúcnosť", "exit_score": 28, "units": [
        _unit("sk-07", "Minulý čas", ["sk_past"],
              "rozprávať, čo som robil včera",
              ["Včera som pracoval doma.", "Kde si bola cez víkend?", "Nevidel som ho."]),
        _unit("sk-08", "Budúci čas a vid", ["sk_future", "sk_aspect"],
              "hovoriť o pláne a o hotovej veci",
              ["Zajtra budem pracovať.", "Večer napíšem list.", "Budeme čakať."]),
        _unit("sk-09", "Kde, kam a pohyb", ["sk_locative", "sk_kde_kam", "sk_motion"],
              "povedať, kde som a kam idem",
              ["Som v práci.", "Idem do obchodu.", "Každý deň chodím pešo."]),
    ]},
    {"id": "A2.2", "band": "A2", "title": "Pády v živote", "exit_score": 37, "units": [
        _unit("sk-10", "2. a 3. pád", ["sk_genitive", "sk_dative"],
              "povedať odkiaľ, bez čoho a komu",
              ["Som z Azerbajdžanu.", "Volám mame každý deň.", "Idem k lekárovi."]),
        _unit("sk-11", "7. pád a zámená", ["sk_instrumental", "sk_pronoun_cases"],
              "povedať s kým a čím",
              ["Idem s kamarátom.", "Cestujem vlakom.", "Zavolám ti zajtra."]),
        _unit("sk-12", "Porovnávanie a správne slovo", ["sk_comparatives", "sk_word_choice"],
              "porovnať veci a vybrať presné slovo",
              ["Bratislava je menšia ako Baku.", "Viem, kde to je.", "Poznám ho dobre."]),
    ]},
    {"id": "B1.1", "band": "B1", "title": "Želania a dôvody", "exit_score": 46, "units": [
        _unit("sk-13", "Podmienka a rozkaz", ["sk_conditional", "sk_imperative"],
              "povedať, čo by som chcel, a poradiť",
              ["Chcel by som pracovať na Slovensku.", "Keby som mal čas, cestoval by som.", "Poď so mnou!"]),
        _unit("sk-14", "Dlhšie vety", ["sk_ze_aby", "sk_relative"],
              "spájať vety a vysvetliť dôvod",
              ["Myslím, že je to dobrý nápad.", "Chcem, aby si prišiel.", "To je kniha, ktorú čítam."]),
    ]},
    {"id": "B1.2", "band": "B1", "title": "Presnejšie", "exit_score": 55, "units": [
        _unit("sk-15", "Predpony a slovesá s pádom", ["sk_prefixes", "sk_verb_cases"],
              "presne povedať, čo sa stalo",
              ["Prišiel som neskoro.", "Čakám na autobus.", "Bojím sa výšok."]),
        _unit("sk-16", "Množné číslo v pádoch a sa", ["sk_plural_cases", "sk_se_passive"],
              "hovoriť o skupinách a o tom, čo sa robí",
              ["Idem s kamarátmi do kina.", "Tu sa hovorí po slovensky.", "Ako sa to píše?"]),
    ]},
    {"id": "B2.1", "band": "B2", "title": "Ako rodený hovoriaci", "exit_score": 64, "units": [
        _unit("sk-17", "Trpný rod a príčastia", ["sk_passive", "sk_participles", "sk_verbal_nouns"],
              "opisovať procesy a výsledky",
              ["Most bol postavený v roku 1990.", "Čítanie ma baví.", "List je už napísaný."]),
        _unit("sk-18", "Minulá podmienka a nepriama reč", ["sk_past_conditional", "sk_reported"],
              "hovoriť o tom, čo sa mohlo stať, a čo kto povedal",
              ["Keby som bol vedel, bol by som prišiel.", "Povedal, že je unavený.", "Spýtala sa, či mám čas."]),
        _unit("sk-19", "Plynulá reč", ["sk_discourse", "sk_collocations"],
              "argumentovať a hovoriť prirodzene",
              ["Je to drahé, navyše je to ďaleko.", "Máš pravdu.", "Nerob si starosti."]),
    ]},
]

# What the tutor says aloud around the board, in Slovak ("ty" - a friendly tutor).
SLOVAK_PHRASES = {
    "did_you_mean": "Správne je:",
    "say_it": "Povedz to.",
    "now_say_it": "Teraz to povedz:",
    "now_you_say_it": "Teraz to povedz ty.",
    "good": "Dobre.",
    "better": "Lepšie:",
    "again": "Ešte raz:",
    "look": "Pozri sa na tabuľu.",
    "form": "Tvar:",
    "so_not": "Takže nie „{wrong}“, ale „{right}“.",
    "for_example": "Napríklad:",
    "practise": "Poďme to precvičiť.",
    "in_lang": "Po slovensky:",
    "timeline": "Na časovej osi:",
    "then": ", potom ",
    "left": "Vľavo",
    "right": "Vpravo",
    "leads_to": " vedie k ",
    "becomes": "sa zmení na",
    "fix_picture": "Vo vete je zlý blok „{bad}“ - správne je „{good}“.",
}
