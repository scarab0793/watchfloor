import json,re,sys
cats_en=["Red Sea","Naval","Research","Submarines","Munitions","Land","Hypersonics","Security","Strikes","Politics","Exports","Operations","Diplomacy","Drones","Counter-drone","Naval drones","Anti-submarine","Air defence","Directed energy","Maritime","Missiles","Strategy","Exercise","Air","Industry","Cyber and infrastructure","Strategic forces","Aviation accident","Escalation","Drones and missiles","Maritime security","Exercises","Space","History","Black Sea","Communications","Ceasefire","Energy","Electronic warfare","Robotics","South China Sea","Manpower","Artillery","Logistics","Naval air","Helicopters","Marines","Balloons","Underwater","Shipbuilding","Lasers","Small arms","Medical","Missile defence","Military AI","Training","Policy"]
CAT={
"de":["Rotes Meer","Marine","Forschung","U-Boote","Munition","Landstreitkräfte","Hyperschall","Sicherheit","Angriffe","Politik","Exporte","Operationen","Diplomatie","Drohnen","Drohnenabwehr","Seedrohnen","U-Boot-Abwehr","Luftverteidigung","Gerichtete Energie","Seewesen","Raketen","Strategie","Übung","Luftwaffe","Industrie","Cyber und Infrastruktur","Strategische Kräfte","Flugunfall","Eskalation","Drohnen und Raketen","Maritime Sicherheit","Übungen","Weltraum","Geschichte","Schwarzes Meer","Kommunikation","Waffenruhe","Energie","Elektronische Kampfführung","Robotik","Südchinesisches Meer","Personal","Artillerie","Logistik","Marineflieger","Hubschrauber","Marineinfanterie","Ballons","Unterwasser","Schiffbau","Laser","Handfeuerwaffen","Medizin","Raketenabwehr","Militärische KI","Ausbildung","Politik"],
"fr":["Mer Rouge","Marine","Recherche","Sous-marins","Munitions","Terre","Hypersonique","Sécurité","Frappes","Politique","Exportations","Opérations","Diplomatie","Drones","Lutte anti-drones","Drones navals","Lutte anti-sous-marine","Défense aérienne","Énergie dirigée","Maritime","Missiles","Stratégie","Exercice","Air","Industrie","Cyber et infrastructures","Forces stratégiques","Accident aérien","Escalade","Drones et missiles","Sécurité maritime","Exercices","Espace","Histoire","Mer Noire","Communications","Cessez-le-feu","Énergie","Guerre électronique","Robotique","Mer de Chine méridionale","Effectifs","Artillerie","Logistique","Aéronavale","Hélicoptères","Infanterie de marine","Ballons","Sous-marin","Construction navale","Lasers","Armes légères","Médical","Défense antimissile","IA militaire","Entraînement","Politique"],
"es":["Mar Rojo","Armada","Investigación","Submarinos","Munición","Tierra","Hipersónicos","Seguridad","Ataques","Política","Exportaciones","Operaciones","Diplomacia","Drones","Antidrones","Drones navales","Guerra antisubmarina","Defensa aérea","Energía dirigida","Marítimo","Misiles","Estrategia","Ejercicio","Aire","Industria","Ciberseguridad e infraestructuras","Fuerzas estratégicas","Accidente aéreo","Escalada","Drones y misiles","Seguridad marítima","Ejercicios","Espacio","Historia","Mar Negro","Comunicaciones","Alto el fuego","Energía","Guerra electrónica","Robótica","Mar de la China Meridional","Personal","Artillería","Logística","Aviación naval","Helicópteros","Infantería de marina","Globos","Submarino","Construcción naval","Láseres","Armas ligeras","Sanidad","Defensa antimisiles","IA militar","Adiestramiento","Política"],
"pl":["Morze Czerwone","Marynarka wojenna","Badania","Okręty podwodne","Amunicja","Wojska lądowe","Broń hipersoniczna","Bezpieczeństwo","Uderzenia","Polityka","Eksport","Operacje","Dyplomacja","Drony","Walka z dronami","Drony morskie","Zwalczanie okrętów podwodnych","Obrona powietrzna","Broń kierowanej energii","Morskie","Rakiety","Strategia","Ćwiczenie","Lotnictwo","Przemysł","Cyberbezpieczeństwo i infrastruktura","Siły strategiczne","Wypadek lotniczy","Eskalacja","Drony i rakiety","Bezpieczeństwo morskie","Ćwiczenia","Kosmos","Historia","Morze Czarne","Łączność","Zawieszenie broni","Energetyka","Walka elektroniczna","Robotyka","Morze Południowochińskie","Kadry","Artyleria","Logistyka","Lotnictwo morskie","Śmigłowce","Piechota morska","Balony","Podwodne","Budowa okrętów","Lasery","Broń strzelecka","Medycyna","Obrona przeciwrakietowa","Wojskowa AI","Szkolenie","Polityka"]}
for k,v in CAT.items(): assert len(v)==len(cats_en),(k,len(v))
hu_t=open(sys.argv[1],encoding='utf8').read()
m=re.search(r'const HCAT=(\{.*?\});\n',hu_t); HCATHU=json.loads(m.group(1))
CAT["hu"]=[HCATHU.get(c,c) for c in cats_en]
CAT["en"]=cats_en
def L(code,**kw): return kw
ui={}
ui["en"]=dict(name="English",title="Watchfloor – defence and military news",titleHome="Watchfloor – defence industry and military news",
 reg={"All":"All","Wars":"Wars","USA":"USA","Europe":"Europe","Far East":"Far East","Middle East":"Middle East","Oceania":"Oceania","Russia":"Russia"},
 war={"All wars":"All wars","Ukraine":"Ukraine","Iran and Gulf":"Iran and Gulf","Gaza":"Gaza"},
 st={"Analysis":"Analysis","Reported":"Reported","Official claim":"Official claim","Company claim":"Company claim","Unverified":"Unverified","Confirmed":"Confirmed"},
 mon=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],dayfirst=True,
 s=dict(band=["F-22 Raptor","K2 Black Panther","HMAS Hobart (D39)"],bandcap="Illustration photos:",bandcap2="Wikimedia Commons (free licence, authors on the file pages).",
 filterRegion="Filter by region",search="Search stories",filterWars="Filter wars",feedTitle="War feed",feedSub="Latest from Ukraine, Iran and Gaza",feedAria="War news feed",
 more="Read the full article",none="No stories match. Clear the search or pick another region.",back="← All stories",src="Sources",photoAlt="Photo for:",logoAlt="Company logo",
 logoCap="Company logo:",logoCap2="Wikimedia Commons. The logo is a trademark of its owner and is shown only to identify the company.",photoCap="Illustration photo (file image, not from the reported event):",
 lic="Wikimedia Commons (free licence, author on the file page)",langAria="Language",artAria="Generic illustration"))
ui["hu"]=dict(name="Magyar",title="Watchfloor – védelmi és katonai hírek",titleHome="Watchfloor – védelmi és katonai hírek",
 reg={"All":"Mind","Wars":"Háborúk","USA":"USA","Europe":"Európa","Far East":"Távol-Kelet","Middle East":"Közel-Kelet","Oceania":"Óceánia","Russia":"Oroszország"},
 war={"All wars":"Összes háború","Ukraine":"Ukrajna","Iran and Gulf":"Irán és az Öböl","Gaza":"Gáza"},
 st={"Analysis":"Elemzés","Reported":"Jelentett","Official claim":"Hivatalos állítás","Company claim":"Céges állítás","Unverified":"Nem megerősített","Confirmed":"Megerősített"},
 mon=["jan.","febr.","márc.","ápr.","máj.","jún.","júl.","aug.","szept.","okt.","nov.","dec."],fmt="M D.",
 s=dict(band=["F-22 Raptor vadászgép","K2 Black Panther harckocsi","HMAS Hobart romboló"],bandcap="Illusztrációs fotók:",bandcap2="Wikimedia Commons (szabad licenc, a szerzők a fájloldalakon szerepelnek).",
 filterRegion="Szűrés régió szerint",search="Keresés a hírek között",filterWars="Háborúk szűrése",feedTitle="Háborús hírfolyam",feedSub="A legfrissebb hírek Ukrajnából, Iránból és Gázából",feedAria="Háborús hírfolyam",
 more="Teljes cikk elolvasása",none="Nincs találat. Töröld a keresést, vagy válassz másik régiót.",back="← Összes hír",src="Források",photoAlt="Fotó:",logoAlt="Cégembléma",
 logoCap="Cégembléma:",logoCap2="Wikimedia Commons. Az embléma tulajdonosának védjegye, kizárólag a cég azonosítására szolgál.",photoCap="Illusztrációs fotó (archív kép, nem a jelentett eseményről):",
 lic="Wikimedia Commons (szabad licenc, a szerző a fájl oldalán szerepel)",langAria="Nyelv",artAria="Általános illusztráció"))
ui["de"]=dict(name="Deutsch",title="Watchfloor – Verteidigungs- und Militärnachrichten",titleHome="Watchfloor – Verteidigungs- und Militärnachrichten",
 reg={"All":"Alle","Wars":"Kriege","USA":"USA","Europe":"Europa","Far East":"Ferner Osten","Middle East":"Naher Osten","Oceania":"Ozeanien","Russia":"Russland"},
 war={"All wars":"Alle Kriege","Ukraine":"Ukraine","Iran and Gulf":"Iran und Golf","Gaza":"Gaza"},
 st={"Analysis":"Analyse","Reported":"Berichtet","Official claim":"Offizielle Angabe","Company claim":"Unternehmensangabe","Unverified":"Unbestätigt","Confirmed":"Bestätigt"},
 mon=["Jan.","Feb.","März","Apr.","Mai","Juni","Juli","Aug.","Sept.","Okt.","Nov.","Dez."],fmt="D. M",
 s=dict(band=["F-22 Raptor","K2 Black Panther","HMAS Hobart (D39)"],bandcap="Illustrationsfotos:",bandcap2="Wikimedia Commons (freie Lizenz, Urheber auf den Dateiseiten).",
 filterRegion="Nach Region filtern",search="Meldungen durchsuchen",filterWars="Kriege filtern",feedTitle="Kriegsticker",feedSub="Das Neueste aus der Ukraine, dem Iran und Gaza",feedAria="Kriegsnachrichten",
 more="Ganzen Artikel lesen",none="Keine Treffer. Suche löschen oder eine andere Region wählen.",back="← Alle Meldungen",src="Quellen",photoAlt="Foto zu:",logoAlt="Firmenlogo",
 logoCap="Firmenlogo:",logoCap2="Wikimedia Commons. Das Logo ist eine Marke seines Inhabers und dient nur der Kennzeichnung des Unternehmens.",photoCap="Illustrationsfoto (Archivbild, nicht vom berichteten Ereignis):",
 lic="Wikimedia Commons (freie Lizenz, Urheber auf der Dateiseite)",langAria="Sprache",artAria="Allgemeine Illustration"))
ui["fr"]=dict(name="Français",title="Watchfloor – actualité de la défense et des armées",titleHome="Watchfloor – actualité de la défense et des armées",
 reg={"All":"Tout","Wars":"Guerres","USA":"États-Unis","Europe":"Europe","Far East":"Extrême-Orient","Middle East":"Moyen-Orient","Oceania":"Océanie","Russia":"Russie"},
 war={"All wars":"Toutes les guerres","Ukraine":"Ukraine","Iran and Gulf":"Iran et Golfe","Gaza":"Gaza"},
 st={"Analysis":"Analyse","Reported":"Rapporté","Official claim":"Déclaration officielle","Company claim":"Déclaration de l’entreprise","Unverified":"Non vérifié","Confirmed":"Confirmé"},
 mon=["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."],fmt="D M",
 s=dict(band=["F-22 Raptor","K2 Black Panther","HMAS Hobart (D39)"],bandcap="Photos d’illustration :",bandcap2="Wikimedia Commons (licence libre, auteurs sur les pages des fichiers).",
 filterRegion="Filtrer par région",search="Rechercher des articles",filterWars="Filtrer les guerres",feedTitle="Fil des guerres",feedSub="Les dernières nouvelles d’Ukraine, d’Iran et de Gaza",feedAria="Fil d’actualité des guerres",
 more="Lire l’article complet",none="Aucun résultat. Effacez la recherche ou choisissez une autre région.",back="← Tous les articles",src="Sources",photoAlt="Photo pour :",logoAlt="Logo de l’entreprise",
 logoCap="Logo de l’entreprise :",logoCap2="Wikimedia Commons. Le logo est une marque de son propriétaire et n’est affiché que pour identifier l’entreprise.",photoCap="Photo d’illustration (image d’archive, sans rapport avec l’événement rapporté) :",
 lic="Wikimedia Commons (licence libre, auteur sur la page du fichier)",langAria="Langue",artAria="Illustration générique"))
ui["es"]=dict(name="Español",title="Watchfloor – noticias de defensa y militares",titleHome="Watchfloor – noticias de defensa y militares",
 reg={"All":"Todo","Wars":"Guerras","USA":"EE. UU.","Europe":"Europa","Far East":"Extremo Oriente","Middle East":"Oriente Medio","Oceania":"Oceanía","Russia":"Rusia"},
 war={"All wars":"Todas las guerras","Ukraine":"Ucrania","Iran and Gulf":"Irán y el Golfo","Gaza":"Gaza"},
 st={"Analysis":"Análisis","Reported":"Informado","Official claim":"Declaración oficial","Company claim":"Declaración de la empresa","Unverified":"Sin verificar","Confirmed":"Confirmado"},
 mon=["ene.","feb.","mar.","abr.","may.","jun.","jul.","ago.","sept.","oct.","nov.","dic."],fmt="D M",
 s=dict(band=["F-22 Raptor","K2 Black Panther","HMAS Hobart (D39)"],bandcap="Fotos de ilustración:",bandcap2="Wikimedia Commons (licencia libre, autores en las páginas de los archivos).",
 filterRegion="Filtrar por región",search="Buscar noticias",filterWars="Filtrar guerras",feedTitle="Frente de guerra",feedSub="Lo último de Ucrania, Irán y Gaza",feedAria="Noticias de guerra",
 more="Leer el artículo completo",none="Sin resultados. Borra la búsqueda o elige otra región.",back="← Todas las noticias",src="Fuentes",photoAlt="Foto de:",logoAlt="Logotipo de la empresa",
 logoCap="Logotipo de la empresa:",logoCap2="Wikimedia Commons. El logotipo es una marca de su propietario y se muestra solo para identificar a la empresa.",photoCap="Foto de ilustración (imagen de archivo, no del suceso informado):",
 lic="Wikimedia Commons (licencia libre, autor en la página del archivo)",langAria="Idioma",artAria="Ilustración genérica"))
ui["pl"]=dict(name="Polski",title="Watchfloor – wiadomości o obronności i wojsku",titleHome="Watchfloor – wiadomości o obronności i wojsku",
 reg={"All":"Wszystko","Wars":"Wojny","USA":"USA","Europe":"Europa","Far East":"Daleki Wschód","Middle East":"Bliski Wschód","Oceania":"Oceania","Russia":"Rosja"},
 war={"All wars":"Wszystkie wojny","Ukraine":"Ukraina","Iran and Gulf":"Iran i Zatoka","Gaza":"Gaza"},
 st={"Analysis":"Analiza","Reported":"Doniesienia","Official claim":"Oficjalne twierdzenie","Company claim":"Twierdzenie firmy","Unverified":"Niepotwierdzone","Confirmed":"Potwierdzone"},
 mon=["sty","lut","mar","kwi","maj","cze","lip","sie","wrz","paź","lis","gru"],fmt="D M",
 s=dict(band=["F-22 Raptor","K2 Black Panther","HMAS Hobart (D39)"],bandcap="Zdjęcia ilustracyjne:",bandcap2="Wikimedia Commons (wolna licencja, autorzy na stronach plików).",
 filterRegion="Filtruj według regionu",search="Szukaj wiadomości",filterWars="Filtruj wojny",feedTitle="Serwis wojenny",feedSub="Najnowsze wiadomości z Ukrainy, Iranu i Gazy",feedAria="Wiadomości wojenne",
 more="Czytaj cały artykuł",none="Brak wyników. Wyczyść wyszukiwanie lub wybierz inny region.",back="← Wszystkie wiadomości",src="Źródła",photoAlt="Zdjęcie do:",logoAlt="Logo firmy",
 logoCap="Logo firmy:",logoCap2="Wikimedia Commons. Logo jest znakiem towarowym właściciela i służy wyłącznie do identyfikacji firmy.",photoCap="Zdjęcie ilustracyjne (obraz archiwalny, nie z opisywanego zdarzenia):",
 lic="Wikimedia Commons (wolna licencja, autor na stronie pliku)",langAria="Język",artAria="Ilustracja poglądowa"))
ui["en"]["fmt"]="D M"
for k in ui: ui[k]["cat"]=dict(zip(cats_en,CAT[k]))
json.dump(ui,open('ui.json','w',encoding='utf8'),ensure_ascii=False,indent=0)
print({k:len(json.dumps(v)) for k,v in ui.items()})
