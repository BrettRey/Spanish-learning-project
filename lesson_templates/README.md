# Lesson Templates

This directory contains pedagogically-sound lesson templates for Spanish language instruction, aligned with CEFR levels A2-B1 and based on Second Language Acquisition (SLA) research and best practices.

## Overview

These templates serve as structured scaffolds for generating dynamic, learner-appropriate lessons. Each template specifies:

- **CEFR Level**: Target proficiency level(s)
- **Skill Focus**: Primary and secondary skills addressed
- **Required Nodes**: Prerequisites from the knowledge graph (grammar, vocabulary, functions)
- **Interaction Type**: How students engage with content
- **Prompt Scaffolds**: Structured prompts for AI-generated lesson content
- **Assessment Criteria**: Level-appropriate evaluation standards
- **Adaptive Parameters**: How to adjust difficulty based on learner performance

## Templates

### 1. conversation-a2.yaml
**Purpose**: Interactive conversational practice for A2 learners
**Duration**: 10-15 minutes
**Key Features**:
- Synchronous dialogue simulation
- Role-based scenarios (friend, shopkeeper, coworker, neighbor)
- Context-specific vocabulary and structures
- Implicit feedback through recasts
- Adaptive difficulty based on student performance

**Use Cases**:
- Planning meals together
- Shopping for clothing
- Discussing weekend activities
- Describing family and daily routines

**Pedagogical Foundation**:
- Interaction Hypothesis (Long, 1996): Negotiation of meaning through conversation
- Noticing Hypothesis (Schmidt, 1990): Drawing attention to forms through reformulation
- Communicative Language Teaching: Focus on meaningful interaction

---

### 2. grammar-drill-b1.yaml
**Purpose**: Structured grammar practice for B1 learners
**Duration**: 40-45 minutes
**Key Features**:
- Three-phase approach: Presentation → Practice → Production (PPP)
- Recognition → Controlled Practice → Guided Production → Free Production
- Contextualized exercises maintaining meaning-focus
- Immediate corrective feedback with explanations
- Communicative task as culmination

**Target Structures**:
- Present subjunctive (common uses)
- Preterite vs. imperfect contrast
- Simple conditional
- Perfect tenses
- Por vs. para distinction

**Pedagogical Foundation**:
- Focus on Form (Long, 1991): Attention to linguistic features within meaningful contexts
- Skill Acquisition Theory (DeKeyser, 1998): Declarative to procedural knowledge through practice
- Task-Based Language Teaching: Grammar emerges from communicative need

---

### 3. vocabulary-production-a2.yaml
**Purpose**: Active vocabulary acquisition for A2 learners
**Duration**: 30-35 minutes
**Key Features**:
- Multi-modal presentation (visual, auditory, kinesthetic)
- Depth-of-processing approach with elaboration
- Semantic field organization (8-12 words/phrases)
- Multiple exposures in varied contexts (minimum 7)
- Productive use from early stages
- Personalization for better retention

**Semantic Fields**:
- La casa y los muebles (house and furniture)
- De compras: ropa (shopping: clothing)
- Actividades de tiempo libre (leisure activities)
- Comida y bebida (food and drink)

**Pedagogical Foundation**:
- Depth of Processing (Craik & Lockhart, 1972): Elaborative encoding enhances retention
- Dual Coding Theory (Paivio, 1986): Visual and verbal encoding
- Retrieval Practice: Testing effect for long-term retention
- Personalization: Connection to learner's life improves memory

---

### 4. listening-comprehension-a2.yaml
**Purpose**: Scaffolded listening comprehension for A2 learners
**Duration**: 25-30 minutes
**Key Features**:
- Three-phase structure: Pre-listening → While-listening → Post-listening
- Multiple listening passes with different purposes (gist → specific → verification)
- Explicit strategy instruction
- Gradual reduction of support over time
- Integration with other skills (speaking, writing)

**Audio Characteristics**:
- Length: 90-150 seconds
- Speech rate: 120-140 words per minute
- Clear standard Spanish
- Minimal background noise

**Listening Strategies Taught**:
- Listen for cognates
- Use context to guess meanings
- Focus on keywords, not every word
- Use visual cues
- Don't panic at unknown words

**Pedagogical Foundation**:
- Bottom-up and Top-down Processing: Both phonemic and schematic knowledge
- Strategy Instruction: Explicit teaching of metacognitive strategies
- Scaffolding (Vygotsky, 1978): Gradual release of support
- Schema Activation: Prior knowledge facilitates comprehension

---

### 5. integrated-skills-b1.yaml
**Purpose**: Integrated skills lesson combining all four skills
**Duration**: 50-60 minutes
**Key Features**:
- Thematic coherence across all activities
- Receptive skills (reading, listening) provide input for productive skills (speaking, writing)
- Cognitive progression: Understand → Analyze → Evaluate → Create
- Language recycling across phases
- Authentic or semi-authentic materials

**Task Sequence**:
1. **Reading** (300-400 words): Informational text on theme
2. **Listening** (2-3 minutes): Related audio adding new perspective
3. **Speaking** (12-15 minutes): Discussion integrating input
4. **Writing** (150-200 words): Essay/article synthesizing information

**Sample Themes**:
- Work-life balance
- Sustainable living
- Technology in daily life
- Travel and culture
- Healthy lifestyle habits

**Pedagogical Foundation**:
- Task-Based Language Teaching (TBLT): Real-world tasks drive learning
- Content and Language Integrated Learning (CLIL): Language learned through content
- Skills Integration: Mirrors real-world language use
- Scaffolding: Skills build on each other sequentially

---

### 6. narrate-past-events-b1.yaml
**Purpose**: Guide B1 learners through planning and delivering coherent spoken narratives about meaningful experiences.
**Duration**: 35-40 minutes
**Key Features**:
- Authentic PRESEEA model for noticing tense contrasts and discourse moves
- Planning canvas with sequencing/evaluative language bank
- Peer rehearsal loop with targeted checklist before final performance
- Performance task tied to speaking rubric plus optional writing follow-up

**Alignment**:
- `cando.es.narrate_past_events_B1`
- `construction.es.preterite_imperfect_contrast_B1`
- `discourse_move.es.sequencing_markers_B1`
- `lexeme.es.contar`, `lexeme.es.a_pesar_de`

**Pedagogical Foundation**:
- Task-Based Language Teaching: Storytelling task integrates form and meaning
- Output Hypothesis (Swain, 1985): Rehearsal and performance promote accuracy
- Focus on Form (Long, 1991): Tense contrast addressed within communicative need
- Retrieval Practice: Oral retelling plus optional written consolidation

---

## Template Structure

All templates follow a consistent YAML structure:

```yaml
template_id: unique-identifier
template_name: "Human-Readable Name"
cefr_level: A2 | B1
skill_focus:
  primary: speaking | listening | reading | writing | grammar | vocabulary
  secondary: [additional skills]

description: >
  Detailed description of template purpose and approach

required_nodes:
  grammar: [list of prerequisite grammar points]
  vocabulary: [list of semantic fields or topics]
  functions: [list of communicative functions]

interaction_type: synchronous_dialogue | structured_practice | guided_production | receptive_with_tasks | task_based_sequence

prompt_scaffold:
  # Detailed scaffolding for AI generation
  # Context, examples, guidelines, techniques

expected_output:
  duration_minutes: X-Y
  # Other quantitative measures

assessment_criteria:
  # Level-appropriate evaluation standards

adaptive_parameters:
  increase_difficulty_if: [conditions]
  decrease_difficulty_if: [conditions]
  difficulty_adjustments: [specific modifications]

follow_up_activities:
  # Suggested extensions and practice

metadata:
  created: YYYY-MM-DD
  version: X.Y
  author: Spanish Learning System
  tags: [relevant tags]
```

## Usage Guidelines

### For Lesson Planning

1. **Select appropriate template** based on:
   - Learner's CEFR level
   - Skill development goals
   - Time available
   - Learning context (individual vs. group)

2. **Check required nodes** in knowledge graph:
   - Ensure prerequisites are met
   - Plan remediation if needed
   - Consider vertical and horizontal sequencing

3. **Customize parameters**:
   - Adjust difficulty based on learner profile
   - Select topic/theme relevant to learner interests
   - Modify duration as needed

4. **Generate lesson content**:
   - Use prompt scaffolds to generate specific materials
   - Adapt language to learner level
   - Include cultural elements where appropriate

### For AI Generation

Templates provide structured prompts for AI systems to generate:
- Dialogues and role-play scenarios
- Grammar exercises at appropriate difficulty
- Vocabulary presentations with examples
- Listening scripts and comprehension questions
- Reading texts and tasks
- Assessment items

The **prompt_scaffold** sections contain detailed instructions for maintaining:
- Linguistic appropriateness (level-appropriate language)
- Pedagogical soundness (effective teaching sequences)
- Engagement (interesting, relevant content)
- Cultural authenticity (appropriate cultural contexts)

### For Assessment

Each template includes:
- **Expected output**: Quantitative benchmarks
- **Assessment criteria**: Qualitative standards aligned with CEFR
- **Adaptive parameters**: Guidance for adjusting difficulty

Use these to:
- Evaluate student performance
- Determine placement and progress
- Identify areas for remediation
- Plan next learning steps

## Adaptive Learning

Templates include sophisticated adaptive parameters:

### Difficulty Increase Indicators
- High accuracy (>85%)
- Consistent use of advanced structures
- Exceeding length/complexity targets
- Student requests for challenge

### Difficulty Decrease Indicators
- Low accuracy (<60-70%)
- Frequent requests for repetition
- Frustration or confusion signals
- Errors impeding comprehension

### Adjustment Strategies

**To Make Easier**:
- Slow speech rate
- Simplify vocabulary
- Increase scaffolding
- Provide more examples
- Reduce output requirements
- Add visual support

**To Make Harder**:
- Increase speech rate
- Introduce less common vocabulary
- Reduce scaffolding
- Add time pressure
- Increase output requirements
- Require more complex structures

## Best Practices

### Skill Integration
While templates focus on specific skills, effective lessons integrate multiple skills naturally. Consider:
- Listening provides input for speaking
- Reading provides models for writing
- Vocabulary supports all skills
- Grammar enables precise expression

### Personalization
Adapt content to learner:
- Interests and hobbies
- Professional context
- Age and life experience
- Learning style preferences
- Cultural background

### Spaced Repetition
Language items should appear:
- Multiple times within a lesson (minimum 7 exposures for vocabulary)
- Across multiple lessons (spaced intervals)
- In varied contexts (transfer and generalization)
- With increasing depth (from recognition to production)

### Error Correction
Balance accuracy and fluency:
- **A2**: Focus on communication; correct only when meaning is unclear
- **B1**: Higher accuracy expectations; explicit correction appropriate
- **Production tasks**: Delayed correction to maintain flow
- **Practice tasks**: Immediate correction with explanation

### Cultural Integration
Include authentic cultural content:
- Everyday situations in Spanish-speaking contexts
- Cultural products, practices, and perspectives
- Appropriate registers and social conventions
- Regional variations when relevant

## Research Foundation

These templates are grounded in current SLA research:

### Key Theories

**Input Hypothesis** (Krashen, 1982)
Learners acquire language through comprehensible input slightly above current level (i+1)

**Output Hypothesis** (Swain, 1985)
Production pushes learners to process language more deeply and notice gaps

**Interaction Hypothesis** (Long, 1996)
Negotiation of meaning through interaction facilitates acquisition

**Noticing Hypothesis** (Schmidt, 1990)
Conscious attention to form is necessary for acquisition

**Task-Based Language Teaching** (Ellis, 2003)
Meaningful tasks drive language development better than isolated forms

**Focus on Form** (Long, 1991)
Attention to linguistic features within meaningful communication

### Evidence-Based Practices

- **Comprehensible input** at appropriate level
- **Meaningful output** in authentic contexts
- **Negotiation of meaning** through interaction
- **Form-focused instruction** within communication
- **Explicit strategy instruction** for skill development
- **Spaced repetition** for retention
- **Retrieval practice** over mere review
- **Scaffolding** with gradual release
- **Personalization** for motivation and memory
- **Multi-modal presentation** for diverse learners

## Alignment with CEFR

Templates align with CEFR:

### A2 (Waystage)
- Handle routine tasks requiring simple information exchange
- Describe aspects of background and immediate environment
- Express immediate needs in simple terms
- Use basic grammatical structures with reasonable accuracy
- Maintain short social exchanges

### B1 (Threshold)
- Deal with most situations while traveling
- Produce simple connected text on familiar topics
- Describe experiences, events, dreams, hopes, and ambitions
- Give reasons and explanations for opinions and plans
- Understand main points of clear standard input

See `../evaluation/cefr-can-do-mapping.yaml` for detailed descriptors.

## Version History

- **v1.0** (2025-11-04): Initial release with 5 core templates
  - Conversation practice (A2)
  - Grammar drills (B1)
  - Vocabulary production (A2)
  - Listening comprehension (A2)
  - Integrated skills (B1)

## Future Enhancements

Planned additions:
- A1 beginner templates
- B2 upper-intermediate templates
- Reading comprehension templates
- Writing process templates
- Pronunciation practice templates
- Cultural competence templates
- Assessment/testing templates
- Specialized ESP templates (business, academic, etc.)

## Contributing

When creating new templates:
1. Follow the established YAML structure
2. Base content on CEFR descriptors
3. Ground approach in SLA research
4. Provide concrete examples
5. Include adaptive parameters
6. Test with real learners
7. Document pedagogical rationale

## References

- Council of Europe (2001, 2018). *Common European Framework of Reference for Languages*
- Ellis, R. (2003). *Task-based Language Learning and Teaching*
- Krashen, S. D. (1982). *Principles and Practice in Second Language Acquisition*
- Long, M. (1996). The role of the linguistic environment in second language acquisition
- Nation, I. S. P. (2001). *Learning Vocabulary in Another Language*
- Schmidt, R. (1990). The role of consciousness in second language learning
- Swain, M. (1985). Communicative competence: Some roles of comprehensible input and comprehensible output in its development
- VanPatten, B. & Williams, J. (2015). *Theories in Second Language Acquisition*

---

For assessment rubrics and CEFR can-do statements, see `../evaluation/`
