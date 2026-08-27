# Bezug zur Bachelorarbeit

Dieses Projekt ist eine direkte Fortsetzung der Bachelorarbeit
*"Beyond Accuracy: Measuring Intelligence in Programming by Example"*
(Steve Leonel Yomi Mbiakop, TU Clausthal, 2026).

- Volltext: [Thesis.pdf](Thesis.pdf)
- Requirements-Dokument dieses Projekts: [requirements-multi-agent-code-synthesis.md](requirements-multi-agent-code-synthesis.md)

## Woher die vier Metriken stammen

POS, PPS, PSS und PES (Kap. 4.2 der Thesis) wurden dort fuer eine
DSL-Token-Repraesentation entwickelt (DeepCoder) und auf DreamCoders
typisierten Lambda-Kalkuel uebertragen. Dieses Projekt portiert dieselbe
Metrik-Semantik ein weiteres Mal, diesmal auf Python-AST (`src/beyondpass/metrics/`).
Die Kernaussage der Thesis, die auch die Motivation dieses Projekts ist:
ein binaeres Erfolgssignal allein sagt nichts darueber aus, *wie nah* eine
falsche Loesung war oder *welche Art* von Fehler vorliegt.

## Code-Basis der Thesis

- [DeepCoder-Fork mit Thesis-Erweiterungen](https://github.com/YOMILEONEL/deepcoder)
- [DreamCoder-Fork mit Thesis-Erweiterungen](https://github.com/YOMILEONEL/ec)

Siehe auch den Abschnitt "Relation to the Thesis" im [README](../README.md)
fuer die vollstaendige Zuordnung Thesis-Element -> Verwendung in diesem
Projekt.
