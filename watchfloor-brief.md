# Watchfloor – projekt-brief (átvitelhez)

## Mi ez
**Cél: az Euronews-hoz hasonlóan többnyelvű oldal** – egyetlen Watchfloor, fejlécben nyelvválasztó (EN, FR, DE, ES, HU, PL, CS, SK, PT), a választott nyelv megjegyzése, nyelvenként saját URL (pl. `/fr/`, `/de/`) vagy `?lang=`; a tartalom mindig ugyanaz a hírlista, csak a megjelenített szöveg és a felületi címkék (régió, státusz, téma, dátum, kereső, gombok) váltanak.

A Watchfloor egy többnyelvű védelmi/katonai híroldal. Célnyelvek (9): **angol (EN, forrásnyelv), francia (FR), német (DE), spanyol (ES), magyar (HU), lengyel (PL), cseh (CS), szlovák (SK), portugál (PT)**. Jelenleg csak az EN és a HU él; a többi nyelv még nincs megépítve. Az oldal egyetlen önálló HTML-fájl (CSS + JS beágyazva), a tartalom egy JS `items` tömbben van; a nézet hash-routinggal (`#/`, `#/a/<id>`) működik. Szűrők: régió (USA, Europe, Far East, Middle East, Oceania, Russia), háborúk (Ukraine, Iran and Gulf, Gaza), kereső, oldalsáv-feed.

## Hol él
- **Angol oldal**: privát Claude artifact – https://claude.ai/artifact/8XQjjXKdvnoH2uoG7jV9wG
- **Magyar oldal**: privát Claude artifact – https://claude.ai/artifact/69GNUzUfzizZGji1dSEkSS
- **GitHub repó**: `scarab0793/watchfloor` (main ágra push)
  - `index.html` = angol, `hu.html` = magyar
  - Publikus: https://scarab0793.github.io/watchfloor/ és https://scarab0793.github.io/watchfloor/hu.html (a repóban CNAME is van)
- Tervezett fájlok a többi nyelvhez: `fr.html`, `de.html`, `es.html`, `pl.html`, `cs.html`, `sk.html`, `pt.html` (+ külön privát artifact mindegyikhez, mint a HU-nál); nyelvváltó az oldalak fejlécében.
- Állapot (2026-10-28): ~369 egyedi hír; a legutóbbi szinkron 15 hírt fordított le.

## Adatmodell
Egy hír (`items` elem): `{id, r | w, c, st, time, t, s, p[], cav, src}`
- `id` egyedi azonosító (kebab-case), `r` régió **vagy** `w` háború (alcsoport), `c` téma (pl. Naval, Land, Air defence, Drones, Red Sea, Diplomacy), `st` státusz (Reported, Official claim, Company claim, Analysis), `time` pl. „27 Oct”
- `t` cím, `s` egysoros összefoglaló, `p[]` bekezdések (jellemzően 3), `cav` fenntartás/óvatossági megjegyzés, `src` források `[[név, url], …]`
- Forrás-konstansok: `AR` (Army Recognition), `DP` (The Defense Post), `DIE` (Defence Industry Europe)
- Képek: `LOGO` és `IMG` map (id → Wikimedia Commons fájlnév); a fejléc három illusztrációs fotót mutat.
- Ismert hiba: az angol tömbben az `f22-tsuiki-keen-sword` id kétszer szerepel (eltérő bekezdésszámmal) – érdemes egyesíteni.

## Nyelvi kiadások működése (a HU a minta, a többi nyelv ugyanígy épül)
- Minden nyelvi oldal `items` tömbje szó szerint az angol; az elemek angolok maradnak (a szűrők és a dátum szerinti rendezés miatt).
- A tömb után nyelvenként egy fordítás-objektum (HU-nál `const HU={id:{t,s,p}}`; más nyelvnél pl. `FR`, `DE`, …) felülírja a megjelenített szöveget, majd címke-térképek (HU-nál): `HR`, `HW`, `HC`, `HS`, `HST`, `HCAT`, `hutime`, végül `items.forEach(...)` alkalmazza a HU-t.
- Új `c` témaérték esetén minden nyelv saját `HCAT`-jába címke kell.
- Fordítási szabályok (minden nyelvre): természetes, pontos nyelvhasználat; nevek, számok, mértékegységek, dátumok pontosak; nyelvspecifikus idézőjel (HU „ ”, DE „ “, FR « », PL „ ”, CS/SK „ “, ES/PT « » vagy “ ”); a bekezdésszám egyezzen az angollal; MI-re nem utalunk.

## Szinkron-folyamat (jelenleg HU-ra fut ütemezetten; a többi nyelvre ugyanígy kell, nyelvenként külön feladat vagy egy közös, 8 nyelvet végigvivő feladat)
1. Mindkét artifact beolvasása (Artifact `read`), mentés fájlba, a `<!DOCTYPE html>`…`</html>` rész használata.
2. Hiányzó HU-bejegyzések keresése (angol id-k, amiknek nincs HU-ja); ha nincs eltérés, nincs teendő.
3. Magyar oldal frissítése: angol `items` átmásolása szó szerint + új fordítások a HU-ba; mást nem módosítunk.
4. Ellenőrzés node-dal (parse, minden id-hez van HU, bekezdésszám egyezik, nincs duplikált id), opcionálisan Playwright (JS-hiba nélkül).
5. Újrapublikálás ugyanarra az artifact URL-re; ütközésnél újraolvasás és merge.
6. `hu.html` másolása a klónba, commit „Update Watchfloor HU <dátum>”, `git pull --rebase origin main`, `git push origin HEAD:main`; hiba esetén értesítés.

## Az angol oldal frissítése
Az angol tartalmat (új hírek az `items` tömb elejére, forrásokkal és `cav` megjegyzéssel, státusszal) egy külön ütemezett feladat/munkamenet tölti fel; a HU-szinkron ennek a kimenetére épül. Az angol szerkesztési szabályok (hangnem: óvatos, forrás-hű, „claim” vs. megerősített megkülönböztetése, `cav` kötelező) a meglévő tételekből olvashatók ki – a projektbe érdemes bemásolni 3–4 példaelemet stílusmintának.

## Amit át kell vinni a projektbe
- Ez a brief mint projekt-utasítás (Project instructions).
- Fájlok a projekt tudásbázisába: `index.html`, `hu.html` (vagy a repó csatlakoztatása).
- Mindkét artifact URL és a repó neve (fent).
- Ütemezett feladatok: a HU-szinkron (és az új nyelvek szinkronja) (és az angol frissítő) promptja – ezeket az ütemezett feladatok listájában kell megnézni/átállítani az új projektre.
- Elérések: GitHub-konnektor (`scarab0793/watchfloor`), Artifact-eszköz (a két artifact tulajdonosa ugyanaz a fiók kell legyen, különben a publikálás elutasításra kerül).

## Nyitott pontok
- A 7 hiányzó nyelv (FR, DE, ES, PL, CS, SK, PT) megépítése: első körben a teljes archívum lefordítása (~370 hír × 7 nyelv – nagy munka, érdemes nyelvenként külön munkamenetben/szakaszokban), utána a napi szinkron.
- Eldöntött irány: egyetlen oldal nyelvválasztóval és nyelvenkénti fordítás-adatokkal (a külön-külön oldalas HU-modell helyett), hogy ne kelljen 9 teljes példányt karbantartani. Ehhez a HU-oldal címke-térképeit (`HR`, `HW`, `HC`, `HS`, `HST`, `HCAT`, `hutime`) nyelvi szótárrá kell általánosítani.
- Duplikált `f22-tsuiki-keen-sword` id javítása.
- Az artifactok külső képeket töltenek (Wikimedia) – az artifact CSP blokkolja őket, a publikus GitHub Pages változatban működnek; ha fontos, data URI-ra cserélendő.
- Az angol frissítő feladat pontos promptját nem ebből a munkamenetből ismerem – azt az ütemezett feladatok közül kell kimásolni.
