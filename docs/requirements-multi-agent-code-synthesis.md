# Requirements Engineering
## Multi-Agent Code-Synthese mit strukturgesteuertem Feedback-Loop

**Arbeitstitel:** StructCoder (Platzhalter)
**Autor:** Steve Leonel Yomi Mbiakop
**Version:** 1.0
**Datum:** August 2026

---

## Inhaltsverzeichnis

1. [Projektübersicht](#1-projektübersicht)
2. [Zielsetzung und Abgrenzung](#2-zielsetzung-und-abgrenzung)
3. [Stakeholder und Nutzungskontext](#3-stakeholder-und-nutzungskontext)
4. [Glossar](#4-glossar)
5. [Systemarchitektur](#5-systemarchitektur)
6. [Funktionale Anforderungen](#6-funktionale-anforderungen)
7. [Nicht-funktionale Anforderungen](#7-nicht-funktionale-anforderungen)
8. [Datenmodell](#8-datenmodell)
9. [Schnittstellenspezifikation](#9-schnittstellenspezifikation)
10. [Evaluationsdesign](#10-evaluationsdesign)
11. [Technologie-Stack](#11-technologie-stack)
12. [Projektstruktur](#12-projektstruktur)
13. [Konfiguration](#13-konfiguration)
14. [Teststrategie](#14-teststrategie)
15. [Sicherheitsanforderungen](#15-sicherheitsanforderungen)
16. [Risiken und Gegenmaßnahmen](#16-risiken-und-gegenmaßnahmen)
17. [Arbeitspakete und Meilensteine](#17-arbeitspakete-und-meilensteine)
18. [Definition of Done](#18-definition-of-done)
19. [Erweiterungsoptionen](#19-erweiterungsoptionen)

---

## 1. Projektübersicht

### 1.1 Kurzbeschreibung

Das System löst Programmieraufgaben, die durch eine natürlichsprachliche Beschreibung und Testfälle spezifiziert sind, mittels mehrerer kooperierender LLM-Agenten. Der zentrale Unterschied zu bestehenden Multi-Agent-Code-Generatoren: Der Feedback-Loop wird nicht nur durch ein binäres Erfolgssignal (Tests bestanden / nicht bestanden) gesteuert, sondern zusätzlich durch **strukturelle Metriken**, die den generierten Code mit einer Referenzlösung vergleichen.

Diese Metriken (POS, PPS, PSS, PES) stammen aus der Bachelorarbeit *„Beyond Accuracy: Measuring Intelligence in Programming by Example"* (TU Clausthal, 2026) und werden hier von einer DSL-Repräsentation auf Python-AST übertragen.

### 1.2 Motivation

Ein binäres Erfolgssignal (BSS) sagt einem Coder-Agenten lediglich, *dass* seine Lösung falsch ist - nicht *warum*. Die strukturellen Metriken erlauben eine differenzierte Diagnose:

- **Hoher POS, niedriger PPS** → richtige Operationen, falsche Anordnung
- **Niedriger POS** → grundsätzlich falscher Lösungsansatz
- **BSS = 1, alle Metriken niedrig** → Verdacht auf Zufallstreffer / triviale Lösung

Diese Diagnose wird in gezieltes Feedback übersetzt, das der Coder-Agent im nächsten Iterationsschritt erhält.

### 1.3 Forschungsfrage des Projekts

> Führt strukturgesteuertes Feedback in einem Multi-Agent-Code-Synthese-System zu einer höheren Lösungsrate und/oder zu weniger benötigten Iterationen als rein binäres Pass/Fail-Feedback?

---

## 2. Zielsetzung und Abgrenzung

### 2.1 Projektziele (Muss)

| ID | Ziel |
|---|---|
| Z1 | Lauffähiges Multi-Agent-System, das HumanEval-Aufgaben löst |
| Z2 | Portierung der vier Thesis-Metriken von DSL-Tokens auf Python-AST |
| Z3 | Feedback-Loop, dessen Feedback-Text aus dem Metrik-Muster abgeleitet wird |
| Z4 | Sichere Sandbox-Ausführung von LLM-generiertem Code |
| Z5 | Reproduzierbare Evaluation: Baseline (BSS-only) vs. strukturgesteuert |
| Z6 | Dokumentiertes, öffentliches GitHub-Repository mit README und Ergebnissen |

### 2.2 Projektziele (Kann)

| ID | Ziel |
|---|---|
| Z7 | Streamlit-Dashboard zur Visualisierung der Metriken pro Aufgabe |
| Z8 | Zweiter Benchmark (MBPP) zur Prüfung der Generalisierbarkeit |
| Z9 | Veröffentlichung des Metrik-Moduls als eigenständiges PyPI-Paket |

### 2.3 Explizite Nicht-Ziele

- **Kein** produktives SaaS-Produkt mit Nutzerverwaltung
- **Kein** Web-Frontend (über ein optionales Read-only-Dashboard hinaus)
- **Kein** eigenes Training oder Fine-Tuning eines Modells
- **Kein** Anspruch auf semantische Äquivalenzprüfung (siehe Limitation L1)
- **Keine** Unterstützung anderer Zielsprachen als Python in Version 1.0

### 2.4 Bekannte Limitationen (bewusst akzeptiert)

| ID | Limitation | Konsequenz |
|---|---|---|
| L1 | Strukturelle Nähe ≠ semantische Äquivalenz | Muss im README explizit benannt werden |
| L2 | Metriken benötigen eine Referenzlösung | Nur auf Benchmarks mit kanonischer Lösung anwendbar |
| L3 | Eine kanonische Referenz ist nur *eine* von vielen validen Lösungen | Niedrige Metrikwerte sind nicht automatisch „schlechter Code" |
| L4 | Evaluation auf einer Domäne (Python-Funktionen, HumanEval) | Generalisierbarkeit ungeprüft |

---

## 3. Stakeholder und Nutzungskontext

| Stakeholder | Interesse | Anforderung daraus |
|---|---|---|
| Entwickler (du) | Portfolio-Wert, Lerneffekt | Sauberer Code, aussagekräftige Ergebnisse |
| Recruiter / Tech Lead | Schnelle Erfassbarkeit der Leistung | README mit Ergebnis-Zahlen in den ersten 30 Sekunden lesbar |
| Fachlicher Prüfer | Wissenschaftliche Nachvollziehbarkeit | Reproduzierbarkeit, benannte Limitationen |
| Open-Source-Nutzer (optional) | Wiederverwendbarkeit des Metrik-Moduls | Klare API, Lizenz, Beispiele |

**Primärer Nutzungskontext:** Kommandozeilen-Ausführung eines Evaluationslaufs über ein Benchmark-Subset, lokal auf einem Entwicklerrechner mit Docker.

---

## 4. Glossar

| Begriff | Bedeutung |
|---|---|
| **BSS** | Binary Success Signal - 1 wenn alle Testfälle bestanden, sonst 0 |
| **POS** | Program Operation Score - Multiset-Überlappung der Tokens (Präsenz) |
| **PPS** | Program Position Score - positionsweise Übereinstimmung |
| **PSS** | Program Sequence Score - längster gemeinsamer zusammenhängender Block |
| **PES** | Program Edit Score - 1 − (normalisierte Levenshtein-Distanz) |
| **Kandidat** | Vom Coder-Agent generierter Code für eine Aufgabe |
| **Referenz** | Kanonische Musterlösung des Benchmarks |
| **Iteration** | Ein Durchlauf Coder → Tester → Critic → Feedback |
| **Run** | Kompletter Evaluationslauf über ein Aufgaben-Subset |
| **Trivial Solution** | Lösung mit BSS = 1, die den Input ignoriert oder konstant antwortet |

---

## 5. Systemarchitektur

### 5.1 Komponentenübersicht

```
┌─────────────────────────────────────────────────────────┐
│                      Orchestrator                        │
│  (steuert Iterationen, Abbruchbedingungen, Logging)      │
└───────┬──────────┬───────────┬────────────┬─────────────┘
        │          │           │            │
        ▼          ▼           ▼            ▼
   ┌─────────┐ ┌────────┐ ┌─────────┐ ┌──────────┐
   │ Planner │ │ Coder  │ │ Tester  │ │  Critic  │
   │  Agent  │ │ Agent  │ │  Agent  │ │  Agent   │
   └─────────┘ └────────┘ └────┬────┘ └────┬─────┘
                                │           │
                                ▼           ▼
                          ┌──────────┐ ┌──────────┐
                          │  Docker  │ │  Metrik- │
                          │ Sandbox  │ │  Modul   │
                          └──────────┘ └──────────┘
                                             │
                                             ▼
                                       ┌──────────┐
                                       │   AST-   │
                                       │Tokenizer │
                                       └──────────┘
```

### 5.2 Ablaufdiagramm (eine Aufgabe)

```
START
  │
  ▼
[Aufgabe laden: Prompt + Tests + Referenzlösung]
  │
  ▼
[Planner-Agent] ──► Lösungsplan (Text, kein Code)
  │
  ▼
┌─► [Coder-Agent] ──► Kandidat-Code
│     │
│     ▼
│   [Tester-Agent] ──► Docker-Sandbox ──► BSS + Fehlermeldungen
│     │
│     ▼
│   [Critic-Agent] ──► AST-Tokenisierung ──► POS/PPS/PSS/PES
│     │
│     ▼
│   [Feedback-Strategie]
│     │
│     ├─ BSS = 1 ─────────────────────────► ERFOLG (Trivial-Check) ──► ENDE
│     │
│     ├─ max_iterations erreicht ─────────► FEHLSCHLAG ──────────────► ENDE
│     │
└─────┴─ sonst: Feedback-Text generieren ──► zurück zum Coder-Agent
```

### 5.3 Komponentenverantwortlichkeiten

| Komponente | Verantwortung | Kennt Referenzlösung? |
|---|---|---|
| Orchestrator | Iterationssteuerung, Logging, Abbruch | Nein (reicht nur durch) |
| Planner-Agent | Aufgabenzerlegung in Teilschritte | **Nein** |
| Coder-Agent | Code-Generierung, Feedback-Verarbeitung | **Nein** |
| Tester-Agent | Testausführung in Sandbox, BSS-Ermittlung | Nein |
| Critic-Agent | Metrikberechnung, Diagnose-Ableitung | **Ja** |
| Metrik-Modul | POS/PPS/PSS/PES-Berechnung | Ja (als Parameter) |
| AST-Tokenizer | Python-Code → Token-Sequenz | Nein (arbeitet auf einzelnem Code) |

> **Kritische Invariante (INV-1):** Planner- und Coder-Agent dürfen die Referenzlösung **niemals** im Prompt sehen. Andernfalls ist die gesamte Evaluation wertlos. Diese Invariante wird durch einen automatisierten Test abgesichert (siehe T-4).

---

## 6. Funktionale Anforderungen

Priorisierung nach MoSCoW: **M** = Must, **S** = Should, **C** = Could.

### 6.1 Benchmark-Anbindung (FR-100)

| ID | Prio | Anforderung |
|---|---|---|
| FR-101 | M | Das System lädt HumanEval über die `datasets`-Bibliothek. |
| FR-102 | M | Pro Aufgabe werden Prompt, Testfälle, kanonische Lösung und Task-ID extrahiert. |
| FR-103 | M | Ein Subset (Anzahl oder explizite ID-Liste) ist per Konfiguration wählbar. |
| FR-104 | S | Der geladene Datensatz wird lokal gecacht, um wiederholte Downloads zu vermeiden. |
| FR-105 | C | MBPP wird über dieselbe Schnittstelle unterstützt (Adapter-Muster). |

### 6.2 Planner-Agent (FR-200)

| ID | Prio | Anforderung |
|---|---|---|
| FR-201 | M | Der Planner erhält ausschließlich den Aufgaben-Prompt (ohne Referenzlösung). |
| FR-202 | M | Er gibt eine nummerierte Liste von Lösungsschritten in natürlicher Sprache zurück. |
| FR-203 | M | Er generiert **keinen** Code (per Prompt-Instruktion und Nachverarbeitungs-Check). |
| FR-204 | S | Der Planner wird nur in Iteration 1 aufgerufen; in Folgeiterationen wird sein Plan wiederverwendet. |
| FR-205 | C | Bei niedrigem POS in Iteration ≥ 2 wird der Planner erneut aufgerufen (Neuplanung). |

### 6.3 Coder-Agent (FR-300)

| ID | Prio | Anforderung |
|---|---|---|
| FR-301 | M | Der Coder erhält: Aufgaben-Prompt, Lösungsplan und (ab Iteration 2) den Feedback-Text. |
| FR-302 | M | Er erhält die vollständige Historie seiner bisherigen Versuche dieser Aufgabe. |
| FR-303 | M | Die Ausgabe wird zu reinem Python-Code extrahiert (Markdown-Fences entfernt). |
| FR-304 | M | Nicht-parsbarer Code (SyntaxError) wird als Iterationsfehlschlag mit eigenem Feedback behandelt. |
| FR-305 | M | Der Coder sieht **niemals** die Referenzlösung (INV-1). |
| FR-306 | S | Die Funktionssignatur aus dem Prompt wird beibehalten (Prüfung per AST). |

### 6.4 Tester-Agent (FR-400)

| ID | Prio | Anforderung |
|---|---|---|
| FR-401 | M | Kandidat-Code + Testfälle werden in einem isolierten Docker-Container ausgeführt. |
| FR-402 | M | BSS = 1 genau dann, wenn **alle** Testfälle bestehen; sonst BSS = 0. |
| FR-403 | M | Ein Timeout (Default 10 s) beendet Endlosschleifen. |
| FR-404 | M | Fehlermeldung und Traceback werden erfasst und für das Feedback aufbereitet. |
| FR-405 | M | Der Container hat **keinen** Netzwerkzugang. |
| FR-406 | S | Anzahl bestandener Einzeltests wird protokolliert (partielle Korrektheit, analog APPS). |
| FR-407 | S | Ressourcenlimits (Memory, CPU) werden gesetzt. |

### 6.5 AST-Tokenizer (FR-500)

| ID | Prio | Anforderung |
|---|---|---|
| FR-501 | M | Python-Quellcode wird per `ast`-Modul in eine flache Token-Sequenz überführt. |
| FR-502 | M | Die Tokenisierung ist deterministisch: gleicher Input → gleiche Sequenz. |
| FR-503 | M | Variablennamen werden normalisiert (α-Äquivalenz), damit reine Umbenennung die Metriken nicht beeinflusst. |
| FR-504 | M | Literale werden auf Typ-Ebene abstrahiert, außer bei kleinen Ganzzahlen (semantisch relevant, z. B. `* 2`). |
| FR-505 | M | Nicht-parsbarer Code liefert eine leere Token-Sequenz (Metriken = 0). |
| FR-506 | S | Die Traversierungsreihenfolge ist dokumentiert (Pre-Order DFS über den AST). |
| FR-507 | S | Docstrings und Kommentare werden ignoriert. |

**Beispiel-Tokenisierung:**

```python
def solve(lst):
    return sorted([x * 2 for x in lst])
```
→ `[FunctionDef, arg, Return, Call:sorted, ListComp, BinOp:Mult, Name, Constant:2, comprehension, Name]`

### 6.6 Metrik-Modul (FR-600)

| ID | Prio | Anforderung |
|---|---|---|
| FR-601 | M | POS: Multiset-Schnitt geteilt durch `max(\|p\|, \|p̂\|)`. |
| FR-602 | M | PPS: positionsweise Übereinstimmungen geteilt durch `max(\|p\|, \|p̂\|)`. |
| FR-603 | M | PSS: längster gemeinsamer **zusammenhängender** Block geteilt durch `max(\|p\|, \|p̂\|)`. |
| FR-604 | M | PES: `1 − Levenshtein(p, p̂) / max(\|p\|, \|p̂\|)`. |
| FR-605 | M | Sind beide Sequenzen leer, ergeben alle Metriken 0 (Konvention der Thesis). |
| FR-606 | M | Alle Metriken liegen im Intervall [0, 1]. |
| FR-607 | M | Die Invariante `POS ≥ max(PPS, PSS, PES)` gilt für jedes Paar und wird getestet. |
| FR-608 | S | Das Modul ist ohne Abhängigkeit zum Agenten-Code importierbar (eigenständiges Package). |

### 6.7 Critic-Agent und Diagnose (FR-700)

| ID | Prio | Anforderung |
|---|---|---|
| FR-701 | M | Der Critic berechnet alle vier Metriken für Kandidat gegen Referenz. |
| FR-702 | M | Aus dem Metrik-Muster wird genau eine Diagnose-Kategorie abgeleitet (siehe Tabelle unten). |
| FR-703 | M | Zu jeder Kategorie gehört ein vordefinierter, parametrisierter Feedback-Text. |
| FR-704 | M | Der Feedback-Text enthält **keine** Tokens, Struktur oder Inhalte der Referenzlösung. |
| FR-705 | M | Der Feedback-Text enthält die Testfehlermeldung aus FR-404. |
| FR-706 | S | Die Schwellenwerte der Kategorien sind konfigurierbar, nicht hartkodiert. |

**Diagnose-Matrix (Default-Schwellenwerte):**

| Kategorie | Bedingung | Feedback-Kern |
|---|---|---|
| `SUCCESS` | BSS = 1 | - (Abbruch) |
| `SYNTAX_ERROR` | Code nicht parsbar | „Der Code ist syntaktisch ungültig: {error}" |
| `WRONG_APPROACH` | BSS = 0 **und** POS < 0.4 | „Der grundlegende Lösungsansatz scheint nicht zu passen. Überdenke die Strategie neu, statt Details zu korrigieren." |
| `WRONG_ORDER` | BSS = 0 **und** POS ≥ 0.6 **und** PPS < 0.4 | „Die verwendeten Operationen wirken passend, aber ihre Reihenfolge bzw. Verschachtelung stimmt nicht. Prüfe die Abfolge der Schritte." |
| `FRAGMENTED` | BSS = 0 **und** POS ≥ 0.6 **und** PSS < 0.4 **und** PPS ≥ 0.4 | „Zusammengehörige Teilschritte sind auseinandergerissen. Prüfe, ob Operationen zusammengehören, die du getrennt hast." |
| `NEAR_MISS` | BSS = 0 **und** PES ≥ 0.7 | „Die Lösung ist strukturell fast korrekt - es fehlt vermutlich ein kleines Detail. Prüfe Randfälle und einzelne Operatoren." |
| `GENERIC_FAIL` | BSS = 0, keine andere Kategorie greift | „Die Tests schlagen fehl: {error}" |
| `SUSPICIOUS_PASS` | BSS = 1 **und** POS < 0.3 | - (kein Feedback, nur Logging-Flag) |

> **Hinweis zur Reihenfolge:** Die Kategorien werden in der Reihenfolge `SYNTAX_ERROR → WRONG_APPROACH → WRONG_ORDER → FRAGMENTED → NEAR_MISS → GENERIC_FAIL` geprüft; die erste zutreffende gewinnt.

### 6.8 Trivial-Solution-Erkennung (FR-800)

Adressiert den in der Thesis (Kap. 6.3.5) dokumentierten Fall, dass ein Programm die Beispiele erfüllt, ohne die intendierte Regel umzusetzen.

| ID | Prio | Anforderung |
|---|---|---|
| FR-801 | M | Bei BSS = 1 wird geprüft, ob der Kandidat mindestens ein Funktionsargument im AST verwendet. |
| FR-802 | M | Lösungen ohne Argumentnutzung werden als `TRIVIAL` geflaggt. |
| FR-803 | S | Lösungen mit BSS = 1 und POS < 0.3 werden als `SUSPICIOUS` geflaggt. |
| FR-804 | S | Geflaggte Lösungen werden in der Auswertung separat ausgewiesen, nicht stillschweigend mitgezählt. |

### 6.9 Orchestrator und Feedback-Loop (FR-900)

| ID | Prio | Anforderung |
|---|---|---|
| FR-901 | M | Der Loop bricht ab bei BSS = 1 **oder** Erreichen von `max_iterations` (Default 5). |
| FR-902 | M | Jede Iteration wird vollständig protokolliert (siehe Datenmodell). |
| FR-903 | M | Ein Betriebsmodus `baseline` liefert nur generisches Pass/Fail-Feedback (Kontrollgruppe). |
| FR-904 | M | Ein Betriebsmodus `structural` liefert das Diagnose-basierte Feedback. |
| FR-905 | M | Beide Modi sind ansonsten identisch (gleiches Modell, gleiche Temperatur, gleiches Subset, gleicher Seed). |
| FR-906 | M | Ein unterbrochener Lauf kann fortgesetzt werden (bereits verarbeitete Task-IDs werden übersprungen). |
| FR-907 | S | API-Fehler werden mit exponentiellem Backoff bis zu 3× wiederholt. |
| FR-908 | S | Aufgaben werden parallel verarbeitet (konfigurierbare Worker-Anzahl, Default 1). |

### 6.10 Ergebnisauswertung (FR-1000)

| ID | Prio | Anforderung |
|---|---|---|
| FR-1001 | M | Pro Run wird eine JSONL-Datei mit einem Eintrag je Iteration geschrieben. |
| FR-1002 | M | Ein Auswertungsskript erzeugt eine Zusammenfassung: Lösungsrate, Ø-Iterationen, Metrik-Mittelwerte. |
| FR-1003 | M | Metriken werden getrennt über **alle** Aufgaben und über **nur gelöste** Aufgaben gemittelt (Konvention der Thesis). |
| FR-1004 | M | Baseline- und Structural-Modus werden in einer Vergleichstabelle gegenübergestellt. |
| FR-1005 | S | Ein Balkendiagramm analog Abb. 6.1/6.2 der Thesis wird generiert (matplotlib). |
| FR-1006 | S | Mehrere Seeds werden als Mittelwert ± Standardabweichung ausgewiesen. |
| FR-1007 | C | Streamlit-Dashboard zur interaktiven Exploration der Ergebnisse. |

---

## 7. Nicht-funktionale Anforderungen

| ID | Kategorie | Anforderung |
|---|---|---|
| NFR-01 | Reproduzierbarkeit | Ein Lauf ist bei gleichem Seed, Modell und Subset reproduzierbar; `temperature` ist konfigurierbar und wird im Run-Log festgehalten. |
| NFR-02 | Reproduzierbarkeit | Jeder Run speichert seine vollständige Konfiguration (inkl. Modellname und Datum) in der Ergebnisdatei. |
| NFR-03 | Sicherheit | Generierter Code wird **ausschließlich** in einer Sandbox ausgeführt (siehe Kapitel 15). |
| NFR-04 | Kostenkontrolle | Ein Kosten-Zähler protokolliert Tokenverbrauch pro Run; ein konfigurierbares Budget-Limit bricht den Lauf ab. |
| NFR-05 | Performance | Eine Aufgabe mit 5 Iterationen läuft in unter 3 Minuten (bei kleinem Modell). |
| NFR-06 | Wartbarkeit | Metrik-Modul, Tokenizer und Agenten sind getrennte, unabhängig testbare Module. |
| NFR-07 | Wartbarkeit | Keine hartkodierten Prompts im Ablaufcode; Prompts liegen in separaten Template-Dateien. |
| NFR-08 | Portabilität | Lauffähig unter Linux, macOS und Windows (WSL2) mit Python 3.10+ und Docker. |
| NFR-09 | Beobachtbarkeit | Strukturiertes Logging mit Log-Level; jede Iteration ist im Nachhinein rekonstruierbar. |
| NFR-10 | Dokumentation | README enthält Motivation, Architektur, Setup, Ergebnisse und Limitationen. |
| NFR-11 | Lizenz | MIT-Lizenz; Benchmark-Lizenzen werden im README genannt. |
| NFR-12 | Code-Qualität | Typannotationen, `ruff`-konform, Docstrings für alle öffentlichen Funktionen. |

---

## 8. Datenmodell

### 8.1 `Task`

| Feld | Typ | Beschreibung |
|---|---|---|
| `task_id` | str | Eindeutige Benchmark-ID (z. B. `HumanEval/0`) |
| `prompt` | str | Funktionssignatur + Docstring |
| `test_code` | str | Testfälle als ausführbarer Python-Code |
| `reference_solution` | str | Kanonische Lösung (nur für Critic) |
| `entry_point` | str | Name der zu implementierenden Funktion |

### 8.2 `IterationResult`

| Feld | Typ | Beschreibung |
|---|---|---|
| `task_id` | str | Referenz auf Task |
| `iteration` | int | Iterationsnummer (1-basiert) |
| `mode` | str | `baseline` oder `structural` |
| `plan` | str \| null | Planner-Ausgabe (nur Iteration 1) |
| `candidate_code` | str | Generierter Code |
| `bss` | int | 0 oder 1 |
| `tests_passed` | int | Anzahl bestandener Einzeltests |
| `tests_total` | int | Gesamtzahl Testfälle |
| `error_message` | str \| null | Fehlermeldung/Traceback |
| `pos`, `pps`, `pss`, `pes` | float | Die vier Metriken |
| `diagnosis` | str | Diagnose-Kategorie (siehe FR-702) |
| `feedback_text` | str \| null | An Coder übergebenes Feedback |
| `flags` | list[str] | z. B. `["TRIVIAL"]`, `["SUSPICIOUS"]` |
| `tokens_in`, `tokens_out` | int | Tokenverbrauch dieser Iteration |
| `duration_s` | float | Dauer der Iteration |

### 8.3 `RunSummary`

| Feld | Typ | Beschreibung |
|---|---|---|
| `run_id` | str | UUID oder Zeitstempel |
| `config` | object | Vollständige Konfiguration |
| `solve_rate` | float | Anteil gelöster Aufgaben |
| `avg_iterations_to_solve` | float | Ø-Iterationen bis Erfolg (nur gelöste) |
| `metrics_all` | object | POS/PPS/PSS/PES über alle Aufgaben |
| `metrics_solved` | object | POS/PPS/PSS/PES nur über gelöste Aufgaben |
| `exact_match_rate` | float | Anteil mit PES = 1.0 |
| `trivial_count` | int | Anzahl `TRIVIAL`-Flags |
| `suspicious_count` | int | Anzahl `SUSPICIOUS`-Flags |
| `total_cost_usd` | float | Geschätzte API-Kosten |

---

## 9. Schnittstellenspezifikation

### 9.1 Metrik-Modul (öffentliche API)

```python
def tokenize(source: str) -> list[str]:
    """Wandelt Python-Quellcode in eine normalisierte Token-Sequenz um.
    Gibt bei SyntaxError eine leere Liste zurück."""

def program_operation_score(ref: list[str], cand: list[str]) -> float: ...
def program_position_score(ref: list[str], cand: list[str]) -> float: ...
def program_sequence_score(ref: list[str], cand: list[str]) -> float: ...
def program_edit_score(ref: list[str], cand: list[str]) -> float: ...

def all_metrics(ref_source: str, cand_source: str) -> MetricResult:
    """Bequemlichkeitsfunktion: tokenisiert beide Quellen und
    berechnet alle vier Metriken."""
```

### 9.2 Sandbox

```python
def run_in_sandbox(
    candidate_code: str,
    test_code: str,
    timeout_s: int = 10,
    memory_mb: int = 512,
) -> SandboxResult:
    """Führt Kandidat + Tests isoliert aus.
    Wirft niemals - Fehler landen in SandboxResult.error."""
```

### 9.3 CLI

```bash
# Einzelner Lauf
python -m structcoder run \
    --mode structural \
    --benchmark humaneval \
    --limit 50 \
    --model claude-haiku-4-5 \
    --max-iterations 5 \
    --seed 0 \
    --out results/run_structural_seed0.jsonl

# Baseline zum Vergleich
python -m structcoder run --mode baseline --limit 50 --seed 0 \
    --out results/run_baseline_seed0.jsonl

# Auswertung
python -m structcoder report \
    --runs results/*.jsonl \
    --out results/summary.md
```

---

## 10. Evaluationsdesign

### 10.1 Versuchsaufbau

| Parameter | Wert |
|---|---|
| Benchmark | HumanEval (164 Aufgaben; Subset ≥ 50 für erste Läufe) |
| Bedingungen | `baseline` (BSS-only) vs. `structural` (Diagnose-Feedback) |
| Max. Iterationen | 5 |
| Seeds | mindestens 3 (0, 1, 2) |
| Modell | identisch in beiden Bedingungen |
| Temperatur | identisch, > 0 (sonst sind Wiederholungen sinnlos) |

> **Wichtig:** Beide Bedingungen müssen dasselbe Aufgaben-Subset, Modell und Iterationsbudget verwenden. Sonst ist die Differenz nicht dem Feedback zuzuschreiben - dieselbe Compute-Matching-Kritik, die in der Thesis (Sesterhenn et al.) zitiert wird.

### 10.2 Primäre Metriken

| Metrik | Definition |
|---|---|
| **Solve Rate** | Anteil Aufgaben mit BSS = 1 innerhalb des Iterationsbudgets |
| **Ø Iterationen bis Lösung** | Mittelwert über gelöste Aufgaben |
| **Iteration-1-Solve-Rate** | Anteil, der ohne jedes Feedback gelöst wird (Basisniveau) |

### 10.3 Sekundäre Metriken

- POS/PPS/PSS/PES, gemittelt über alle bzw. nur gelöste Aufgaben
- Exact-Match-Rate (PES = 1.0)
- Anzahl `TRIVIAL`- und `SUSPICIOUS`-Flags
- Verteilung der Diagnose-Kategorien über alle Iterationen

### 10.4 Erwartete Ergebnistabelle

| Bedingung | Solve Rate | Ø Iter. | POS (gelöst) | PPS (gelöst) | PSS (gelöst) | PES (gelöst) |
|---|---|---|---|---|---|---|
| Baseline, Seed 0-2 | - | - | - | - | - | - |
| Structural, Seed 0-2 | - | - | - | - | - | - |

### 10.5 Ehrliche Ergebnisinterpretation

Das Projekt ist **auch dann erfolgreich**, wenn strukturgesteuertes Feedback keinen Vorteil bringt. Ein sauber gemessenes Negativergebnis mit benannten Gründen ist wissenschaftlich wertvoller als ein geschöntes Positivergebnis - und im Vorstellungsgespräch überzeugender. Erwartungsgemäß zu diskutierende Punkte:

- Moderne LLMs korrigieren sich bereits gut mit reinem Fehlermeldungs-Feedback
- Die kanonische Referenz ist nur eine von vielen validen Lösungen (L3)
- HumanEval-Aufgaben sind kurz; strukturelles Feedback könnte erst bei längeren Programmen greifen

---

## 11. Technologie-Stack

| Bereich | Technologie | Begründung |
|---|---|---|
| Sprache | Python 3.10+ | `ast` nativ, Thesis-Code wiederverwendbar, Benchmarks sind Python |
| LLM-Zugriff | `anthropic` oder `openai` SDK | Function Calling, gute Python-Unterstützung |
| Benchmark | `datasets` (Hugging Face) | HumanEval/MBPP direkt ladbar |
| Code-Analyse | `ast` (Standard Library) | Keine externe Abhängigkeit nötig |
| Sandbox | `docker` (Python SDK) | Prozess- und Netzwerkisolation |
| Testausführung | `pytest` (im Container) | Standard, gute Fehlermeldungen |
| Logging | `structlog` oder `logging` | Strukturierte JSONL-Logs |
| Auswertung | `pandas` + `matplotlib` | Tabellen und Diagramme analog Thesis |
| Konfiguration | `pydantic-settings` + YAML | Validierte, typisierte Konfiguration |
| Code-Qualität | `ruff`, `mypy` | Linting und Typprüfung |
| Tests | `pytest` | Unit- und Integrationstests |
| Optional Dashboard | `streamlit` | Schnelle Visualisierung ohne Frontend-Aufwand |

**Bewusst nicht verwendet:** LangChain/LangGraph/CrewAI. Bei vier klar definierten Agentenrollen überwiegt der Framework-Overhead den Nutzen; direkte SDK-Aufrufe sind besser nachvollziehbar und im Repository leichter zu lesen.

---

## 12. Projektstruktur

```
structcoder/
├── README.md
├── LICENSE
├── pyproject.toml
├── config/
│   ├── default.yaml
│   └── prompts/
│       ├── planner.txt
│       ├── coder_initial.txt
│       └── coder_retry.txt
├── src/structcoder/
│   ├── __init__.py
│   ├── __main__.py            # CLI-Einstiegspunkt
│   ├── config.py              # Pydantic-Settings
│   ├── benchmarks/
│   │   ├── base.py            # Task-Protokoll
│   │   ├── humaneval.py
│   │   └── mbpp.py            # optional
│   ├── metrics/
│   │   ├── tokenizer.py       # AST → Token-Sequenz
│   │   └── scores.py          # POS/PPS/PSS/PES
│   ├── agents/
│   │   ├── llm_client.py      # API-Wrapper, Retry, Kostenzählung
│   │   ├── planner.py
│   │   ├── coder.py
│   │   ├── tester.py
│   │   └── critic.py
│   ├── sandbox/
│   │   ├── docker_runner.py
│   │   └── Dockerfile
│   ├── feedback/
│   │   ├── diagnosis.py       # Metrik-Muster → Kategorie
│   │   └── templates.py       # Kategorie → Feedback-Text
│   ├── orchestrator.py        # Iterationsschleife
│   └── reporting/
│       ├── aggregate.py
│       └── plots.py
├── tests/
│   ├── test_tokenizer.py
│   ├── test_scores.py
│   ├── test_diagnosis.py
│   ├── test_sandbox.py
│   └── test_no_reference_leak.py
├── results/                   # JSONL-Läufe (gitignored außer finalen)
└── docs/
    └── thesis_link.md         # Bezug zur Bachelorarbeit
```

---

## 13. Konfiguration

```yaml
# config/default.yaml
run:
  mode: structural          # baseline | structural
  seed: 0
  max_iterations: 5
  parallel_workers: 1

benchmark:
  name: humaneval
  limit: 50
  task_ids: null            # oder explizite Liste

llm:
  provider: anthropic
  model: claude-haiku-4-5
  temperature: 0.7
  max_tokens: 2000
  max_retries: 3

sandbox:
  timeout_s: 10
  memory_mb: 512
  network: false

diagnosis:
  pos_low: 0.4
  pos_high: 0.6
  pps_low: 0.4
  pss_low: 0.4
  pes_near_miss: 0.7
  suspicious_pos: 0.3

budget:
  max_usd: 10.0

output:
  results_dir: results/
  log_level: INFO
```

---

## 14. Teststrategie

| ID | Testart | Gegenstand | Akzeptanzkriterium |
|---|---|---|---|
| T-1 | Unit | Tokenizer | Determinismus; α-Äquivalenz (Umbenennung ändert Sequenz nicht); leere Liste bei SyntaxError |
| T-2 | Unit | Metriken | Identische Programme → alle Metriken = 1.0; disjunkte Programme → alle = 0.0; beide leer → 0.0 |
| T-3 | Property | Metrik-Invariante | Für zufällige Token-Paare gilt `POS ≥ max(PPS, PSS, PES)` |
| T-4 | Unit | Referenz-Leak (INV-1) | Planner- und Coder-Prompts enthalten die Referenzlösung nicht - als String-Assertion über den finalen Prompt |
| T-5 | Unit | Diagnose | Jede Kategorie wird durch mindestens einen konstruierten Metrik-Vektor ausgelöst; Reihenfolgeprüfung deterministisch |
| T-6 | Integration | Sandbox | Endlosschleife wird durch Timeout beendet; Netzwerkzugriff schlägt fehl; Exception im Kandidatencode crasht den Host-Prozess nicht |
| T-7 | Integration | Orchestrator | Ein Mini-Lauf über 2 Aufgaben mit gemocktem LLM läuft vollständig durch und schreibt gültige JSONL |
| T-8 | Regression | Thesis-Konsistenz | Die Metriken reproduzieren die Beispielwerte aus Kap. 4.2 der Thesis (POS 0.75, PPS/PSS/PES je 0.25) auf dem dortigen Beispiel |
| T-9 | Manuell | Reporting | Zusammenfassung und Diagramme werden aus vorhandenen JSONL fehlerfrei erzeugt |

> **T-8 ist der wichtigste Test:** Er belegt, dass die portierte Implementierung dieselbe Semantik hat wie die der Bachelorarbeit.

---

## 15. Sicherheitsanforderungen

| ID | Anforderung |
|---|---|
| SEC-1 | LLM-generierter Code wird **niemals** im Host-Prozess ausgeführt (kein `exec`, kein `eval`). |
| SEC-2 | Ausführung erfolgt in einem Docker-Container mit `--network none`. |
| SEC-3 | Der Container läuft als nicht-privilegierter Nutzer, nicht als root. |
| SEC-4 | Ressourcenlimits: Memory (Default 512 MB), CPU-Anteil, Prozessanzahl (`--pids-limit`). |
| SEC-5 | Der Container hat kein Volume-Mount auf Host-Verzeichnisse außerhalb eines temporären Arbeitsordners. |
| SEC-6 | Container werden nach jeder Ausführung entfernt (`--rm`), kein Zustand zwischen Aufgaben. |
| SEC-7 | API-Keys werden ausschließlich über Umgebungsvariablen geladen, niemals committet; `.env` ist in `.gitignore`. |
| SEC-8 | Das Budget-Limit (NFR-04) verhindert unbeabsichtigt hohe API-Kosten bei Endlosläufen. |

---

## 16. Risiken und Gegenmaßnahmen

| ID | Risiko | Wahrsch. | Auswirkung | Gegenmaßnahme |
|---|---|---|---|---|
| R-1 | Strukturelles Feedback zeigt keinen messbaren Vorteil | Mittel | Mittel | Als ehrliches Ergebnis dokumentieren (10.5); Projektwert liegt in Methodik und Messung |
| R-2 | Kanonische Referenz ist nur eine von vielen validen Lösungen → Metriken bestrafen guten Code | Hoch | Mittel | Als Limitation L3 benennen; zusätzlich Iterationsanzahl als Erfolgsmaß nutzen |
| R-3 | AST-Tokenisierung zu grob oder zu fein → Metriken wenig aussagekräftig | Mittel | Hoch | Frühzeitig T-8 gegen Thesis-Beispiele; Granularität dokumentiert und konfigurierbar |
| R-4 | API-Kosten laufen aus dem Ruder | Niedrig | Mittel | Budget-Limit (NFR-04), kleines Modell, kleines Subset in der Entwicklung |
| R-5 | Docker-Setup verzögert den Start | Mittel | Niedrig | Sandbox als erstes Arbeitspaket; Fallback `subprocess` + Timeout nur lokal in der Entwicklung |
| R-6 | Referenzlösung leakt versehentlich in Coder-Prompt | Niedrig | Sehr hoch | Automatisierter Test T-4; Trennung im Datenmodell |
| R-7 | Zeitbudget neben Studium/Werkstudentenjob reicht nicht | Mittel | Mittel | Strikte MoSCoW-Priorisierung; Kann-Ziele (Z7-Z9) sind streichbar |
| R-8 | Modell-Nichtdeterminismus macht Vergleich verrauscht | Hoch | Mittel | Mehrere Seeds (mind. 3), Mittelwert ± Standardabweichung |

---

## 17. Arbeitspakete und Meilensteine

### AP 1 - Fundament (Woche 1)

- [ ] Repository, `pyproject.toml`, Linting, CI-Grundgerüst
- [ ] Konfigurationsmodul (Pydantic + YAML)
- [ ] HumanEval-Loader mit Task-Datenmodell (FR-101 bis FR-104)
- [ ] Docker-Sandbox mit Timeout und Ressourcenlimits (FR-401 bis FR-407, SEC-1 bis SEC-6)
- [ ] Tests T-6

**Meilenstein M1:** Eine hartkodierte korrekte Lösung wird geladen, in der Sandbox getestet und liefert BSS = 1.

### AP 2 - Metriken (Woche 2)

- [ ] AST-Tokenizer mit Normalisierung (FR-501 bis FR-507)
- [ ] Portierung POS/PPS/PSS/PES aus der Thesis (FR-601 bis FR-608)
- [ ] Tests T-1, T-2, T-3, T-8

**Meilenstein M2:** Die Thesis-Beispielwerte (POS 0.75, übrige 0.25) werden exakt reproduziert.

### AP 3 - Agenten und Loop (Woche 3)

- [ ] LLM-Client mit Retry und Kostenzählung
- [ ] Planner-, Coder-, Tester-, Critic-Agent (FR-201 ff., FR-301 ff., FR-701 ff.)
- [ ] Diagnose-Modul und Feedback-Templates (FR-702 bis FR-706)
- [ ] Trivial-Erkennung (FR-801 bis FR-804)
- [ ] Orchestrator mit beiden Modi (FR-901 bis FR-908)
- [ ] Tests T-4, T-5, T-7

**Meilenstein M3:** Ein Lauf über 5 Aufgaben in beiden Modi läuft durch und schreibt vollständige JSONL.

### AP 4 - Evaluation und Veröffentlichung (Woche 4)

- [ ] Auswertungsskript und Diagramme (FR-1001 bis FR-1006)
- [ ] Vollständige Läufe: 2 Modi × 3 Seeds über ≥ 50 Aufgaben
- [ ] README mit Motivation, Architektur, Ergebnissen, Limitationen (NFR-10)
- [ ] Verlinkung zur Bachelorarbeit und zu den Thesis-Repositories
- [ ] Optional: Streamlit-Dashboard (Z7)

**Meilenstein M4:** Öffentliches Repository mit belastbaren Ergebniszahlen im README.

---

## 18. Definition of Done

Das Projekt gilt als abgeschlossen, wenn:

1. Alle Muss-Anforderungen (M) implementiert und durch Tests abgedeckt sind
2. T-8 (Thesis-Konsistenz) grün ist - die Metrik-Semantik ist nachweislich identisch
3. T-4 (kein Referenz-Leak) grün ist
4. Mindestens 50 HumanEval-Aufgaben in beiden Modi über 3 Seeds evaluiert sind
5. Die Ergebnistabelle aus 10.4 mit echten Zahlen gefüllt ist
6. Das README einem fachfremden Leser in unter 2 Minuten vermittelt, was das Projekt tut und was dabei herauskam
7. Alle Limitationen (L1-L4) im README offen benannt sind
8. Das Repository ohne Zusatzwissen per `README`-Anleitung reproduzierbar aufsetzbar ist

---

## 19. Erweiterungsoptionen

Sinnvolle Anschlusspunkte nach Version 1.0 - bewusst außerhalb des Kern-Scopes gehalten:

| Option | Beschreibung | Aufwand |
|---|---|---|
| Semantische Prüfung | Zusätzliche zurückgehaltene Testfälle zur Prüfung echter Generalisierung (direkter Future-Work-Punkt der Thesis) | Mittel |
| Referenzfreier Modus | Mehrere Kandidaten generieren; strukturelle Divergenz untereinander als Unsicherheitssignal statt Referenzvergleich | Hoch |
| MBPP als zweiter Benchmark | Generalisierbarkeit über HumanEval hinaus prüfen | Niedrig |
| Längere Programme | Aufgaben mit mehr als einer Funktion - dort greift strukturelles Feedback vermutlich stärker | Mittel |
| Metrik-Paket auf PyPI | Metrik-Modul eigenständig veröffentlichen (Z9) | Niedrig |
| GitHub Action | Metriken als PR-Kommentar auf echten Repositories | Mittel |

---

## Anhang A - Bezug zur Bachelorarbeit

| Thesis-Element | Verwendung im Projekt |
|---|---|
| POS/PPS/PSS/PES (Kap. 4.2) | Kern des Critic-Agenten, portiert auf Python-AST |
| Konvention „leere Sequenzen → 0" (Kap. 4.2) | FR-605 |
| Metrik-Invariante POS ≥ übrige (Kap. 6.3.1) | FR-607, Test T-3 |
| Trennung „alle Aufgaben" / „nur gelöste" (Kap. 5.4) | FR-1003 |
| Trivial-Solution-Fall (Kap. 6.3.5) | FR-800 komplett |
| Best-Effort-Kandidaten (Kap. 6.3.3) | Konzeptueller Vorläufer des Feedback-Loops |
| Compute-Matching-Kritik (Kap. 2.2) | FR-905, Abschnitt 10.1 |
| Future Work: struktur + funktional kombinieren (Kap. 7.1) | Gesamtmotivation des Projekts |

---

## Anhang B - Beispiel-Prompts (Ausgangspunkt)

**Planner:**
> Du erhältst eine Programmieraufgabe. Zerlege sie in nummerierte Lösungsschritte in natürlicher Sprache. Schreibe **keinen** Code. Maximal 5 Schritte.

**Coder (Iteration 1):**
> Implementiere die folgende Funktion in Python. Halte dich an die vorgegebene Signatur. Gib ausschließlich Code zurück, ohne Erklärung.
> Aufgabe: {prompt}
> Lösungsplan: {plan}

**Coder (Folgeiterationen):**
> Dein vorheriger Lösungsversuch war nicht korrekt.
> Aufgabe: {prompt}
> Dein bisheriger Code: {previous_code}
> Rückmeldung: {feedback_text}
> Korrigiere den Code. Gib ausschließlich Code zurück, ohne Erklärung.
