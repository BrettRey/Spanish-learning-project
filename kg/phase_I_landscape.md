# Phase I – B1 Spanish Landscape

## 1. Scope & Intended Outcomes
- **Goal:** establish the B1 (Threshold) layer of the knowledge graph so agents can plan lessons, generate prompts, and assess work against CEFR-aligned targets.
- **Coverage:** spoken interaction & production, written interaction & production, mediation, and supporting linguistic resources at B1.
- **Deliverable types:** `CanDo`, `Function`, `Construction`, `Lexeme`, `Topic`, `DiscourseMove`, `PragmaticCue`, `AssessmentCriterion`.

## 2. Reference Can-Do Inventory (CEFR Companion Volume)
| Domain | Descriptor families to encode as `CanDo` nodes | Example task archetypes |
| --- | --- | --- |
| **Overall Spoken Interaction** | Maintain straightforward exchanges; handle travel, work, study situations; cope with misunderstandings. | Resolve a booking issue, ask clarification in a meeting. |
| **Spoken Production** | Give straightforward descriptions; narrate experiences, dreams, hopes; briefly give reasons and explanations. | 2–3 minute presentation, story retell. |
| **Spoken Interaction – Sustained Monologue** | Describe events and reactions; relate plot of a film/book; improvise on familiar topics. | Book/film review, weekend recap. |
| **Written Production** | Write connected texts on familiar topics; simple reports; narratives with sequencing markers. | 180-word email, opinion paragraph. |
| **Written Interaction** | Exchange information, routine correspondence, requests for information/clarification. | Complaint letter, community forum response. |
| **Mediation** | Relay main points of clear texts; summarize argument; explain instructions. | Take notes for a colleague, interpret event details. |

## 3. Functional Domains & Priority Nodes
- **Social exchange & courtesy:** apologies, invitations, refusals, thanks, advice (politeness strategies, mitigation—`PragmaticCue` nodes).
- **Transactional tasks:** travel arrangements, housing, healthcare, education, workplace routines (`Function` + `Topic`).
- **Narration & description:** sequencing, aspect, descriptive adjectives, comparisons (`Construction`: pretérito imperfecto/perfecto contrast, connectors).
- **Expressing opinions & attitudes:** agreement/disagreement, speculation, probability (`Construction`: subjunctive in nominal clauses, periphrases).
- **Problem-solving interaction:** clarifying misunderstandings, negotiating solutions (`DiscourseMove`: confirm, reformulate, hedge).

## 4. Grammar Backbone
Create `Construction`/`Morph` nodes for:
1. **Mood & modality:** present subjunctive triggers (volition, emotion, doubt), `ojalá`, impersonal expressions.
2. **Temporal-aspectual control:** preterite vs imperfect narration, recent past (`acabar de`), near future (`ir a + inf.`).
3. **Complex sentences:** relative clauses with indicative/subjunctive, conditional period (real/unreal), reported speech in present/preterite sequence.
4. **Discourse connectors:** causal (`puesto que`), adversative (`sin embargo`), concessive (`aunque`), sequential (`luego`, `además`).
5. **Morphology:** object pronoun stacking, se impersonal/passive, reflexive verbs, periphrastic comparatives.

## 5. Lexical Fields & Concepts
- **Primary selection driver:** word-family frequency. Rank and select lemmas using corpus metrics (e.g., Zipf scores from Corpus del Español, CREA, or SUBTLEX-ESP). Store the family frequency band, exact metric, and source corpus in each `Lexeme` node (`frequency` and `frequency_source` fields).
- **Pedagogical exceptions:** when a lower-frequency item is required for cultural literacy or target descriptors, flag it with `low_frequency_exception: true` and justify in `notes`.

High-priority semantic clusters (ordered by frequency within each set):
- **Life domains:** work/studies, leisure, travel, health & wellness, urban living.
- **Opinion & evaluation:** adjectives (`apasionante`, `aburrido`), hedges (`quizás`, `tal vez`), boosters (`sin duda`).
- **Narrative verbs:** reporting speech (`contó`, `añadió`), emotion verbs (`emocionarse`, `preocuparse`).
- **Collocations & chunks:** `tener ganas de`, `me parece que`, `a pesar de`, `por lo visto`, `no solo... sino también`.

Each lexical family becomes one `Lexeme` node with synonyms, collocation metadata, and frequency bands (B1 band via Cervantes PCIC), ensuring intra-family ordering respects frequency data.

## 6. Discourse & Pragmatics
- **Turn management:** `¿Qué te parece si...?`, `¿Te importa que...?`, softening requests.
- **Register control:** `usted` vs `tú`, email openings/closings, hedging in meetings.
- **Cohesion devices:** referencing (`este`, `esa situación`), ellipsis, discourse markers (`entonces`, `total que`).
- **Intercultural cues:** punctuality, small talk norms, indirect disagreement – align with PCIC sociocultural objectives.

Model as `PragmaticCue` or `DiscourseMove` nodes linked to target `CanDo` descriptors.

## 7. Task & Genre Templates
Map exemplar tasks to `LessonTemplate` metadata:
1. **Oral presentation:** 2-minute talk describing past trip (B1 spoken production).
2. **Role-play:** resolve a service complaint with negotiation steps.
3. **Opinion essay:** 180-word text defending a viewpoint with connectors.
4. **Note-taking mediation:** summarize a radio segment for a colleague.
5. **Interactive planning:** agree on weekend plans with constraints.

Each template references the `CanDo`, required constructions, and evaluation rubric items (DELE B1 rubrics: coherence, range, accuracy, fluency).

## 8. Evaluation Rubrics & Criteria
- Source rubrics from **DELE B1** and **SIELE** guidelines: accuracy vs complexity, coherence, fluency, pronunciation.
- Create `AssessmentCriterion` nodes: `lexical_range_B1`, `grammatical_control_B1`, `coherence_cohesion_B1`, `phonological_control_B1`.
- Align rating scales (0–3 or 0–5) with CEFR descriptors; include sample evidence statements.

## 9. Error Anticipation
Leverage learner corpora (CEDEL2, ICLE Spanish subset) to define `CommonError` relationships:
- Overuse of indicative after volition verbs.
- Pretérito vs imperfect confusion.
- Misplaced object pronouns (`leísmo`, `loísmo`).
- Gender/number agreement in new lexical fields.
- Literal translations of idioms (false friends).

Use `addresses_error` edges from targeted lessons or drills back to these nodes.

## 10. Resource Bibliography (for node metadata)
- **CEFR Companion Volume** (Council of Europe, 2020) – authoritative descriptors.
- **Plan Curricular del Instituto Cervantes (PCIC)** – lexical/grammar inventory by level.
- **DELE B1 exam guides** – task formats, rubrics.
- **Aula Internacional 3 / Prisma Fusión B1** – syllabus benchmarks, lexical sets.
- **Corpus del Español, CREA** – frequency and example sourcing.
- **Routledge Spanish Grammar in Context**, **Gramática de uso del español B1–B2** – reference examples.
- **Pragmatics references:** *Developing Interactional Competence in a Second Language* (Kasper), *La cortesía en el español peninsular* (Briz).
- **Learner corpora:** CEDEL2 (UNED), SPLLOC – error patterns.

Document resource citations in node metadata (`source` field) to maintain traceability.

## 11. Immediate Next Steps
1. Catalog ~50 B1 `CanDo` nodes using Companion Volume + PCIC crosswalk.
2. For each `CanDo`, list required functions, grammar, lexicon, and discourse moves; create edges (`prerequisite_of`, `supports`, `addresses_error`).
3. Populate initial `Lexeme`, `Construction`, and `PragmaticCue` YAML entries referencing this landscape.
4. Draft evaluation rubrics in `evaluation/` connected to `AssessmentCriterion` nodes.
5. Validate coverage against DELE B1 sample tasks to ensure no major descriptor gaps.
