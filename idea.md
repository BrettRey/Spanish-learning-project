<html contenteditable=""><head>
<meta http-equiv="content-type" content="text/html; charset=windows-1252"></head><body><p>Short
 version: make Codex the “coach” front-end, and let a few small, local 
tools (KG + SRS + ASR) do the real tracking. Use the Agents SDK to 
coordinate them and MCP to expose your tools. Here’s a concrete way to 
wire it up.</p>
<h1>1) What runs where</h1>
<ul><li>
<p><strong>Codex CLI</strong> for the live lesson/conversation (terminal or IDE), guided by an <code>AGENTS.md</code> in your repo. Codex keeps state across turns and can run local commands/tests. (<a href="https://openai.com/codex/?utm_source=chatgpt.com" title="Codex">openai.com</a>)</p>
</li><li>
<p><strong>Agents SDK</strong> as the lightweight orchestrator that can 
call multiple tools/agents and keep the “lesson &#8594; assess &#8594; schedule &#8594; 
next lesson” loop coherent. (<a href="https://platform.openai.com/docs/guides/agents-sdk?utm_source=chatgpt.com" title="Agents SDK - OpenAI API">platform.openai.com</a>)</p>
</li><li>
<p><strong>MCP (Model Context Protocol)</strong> to expose your local 
tools—knowledge-graph queries, SRS scheduling, ASR/Whisper—to 
Codex/agents. OpenAI shows how to turn Codex into or call it from an MCP
 server; do the same for your tools. (<a href="https://developers.openai.com/codex/?utm_source=chatgpt.com" title="Codex">developers.openai.com</a>)</p>
</li></ul>
<h1>2) Minimal repo layout</h1>
<pre><code>language-coach/
&#9500;&#9472; AGENTS.md
&#9500;&#9472; state/                      # per-learner state
&#9474;  &#9500;&#9472; learner.yaml             # CEFR goals, correction style, L1, etc.
&#9474;  &#9492;&#9472; mastery.sqlite           # item mastery history, FSRS params
&#9500;&#9472; kg/                         # knowledge graph
&#9474;  &#9500;&#9472; seed/                    # YAML/JSON nodes &amp; edges
&#9474;  &#9492;&#9472; kg.sqlite                # compiled graph (SQLite)
&#9500;&#9472; mcp_servers/
&#9474;  &#9500;&#9472; kg_server.py             # exposes kg.query(), kg.next(), kg.add_evidence()
&#9474;  &#9500;&#9472; srs_server.py            # exposes srs.due(), srs.update()
&#9474;  &#9492;&#9472; speech_server.py         # exposes asr.transcribe(), tts.speak()
&#9500;&#9472; lesson_templates/           # prompt &amp; exercise templates (YAML/MD)
&#9500;&#9472; evaluation/                 # rubrics; IRT/heuristics; CEFR can-do mapping
&#9492;&#9472; ui/                         # optional web shell for audio; terminal works too
</code></pre>
<p>All three servers are tiny local scripts that speak MCP—so Codex (or your Agents runner) can call them as tools.</p>
<h1>3) Data model (lean but expressive)</h1>
<p><strong>KG nodes</strong> (examples): <code>Lexeme</code>, <code>Construction</code>, <code>Morph</code>, <code>Function</code>, <code>CanDo</code>, <code>Topic</code>, <code>Script</code>, <code>PhonologyItem</code>.<br>
<strong>Edges</strong> (typed): <code>prerequisite_of</code>, <code>realizes</code>, <code>contrasts_with</code>, <code>depends_on</code>, <code>practice_with</code>, <code>addresses_error</code>.</p>
<p>Example node (YAML):</p>
<pre><code class="language-yaml">id: constr.zh.ba3
type: Construction
label: &#25226;-b&#462; disposal construction
prerequisites: [constr.zh.svo_basic, morph.zh.ba3_particle]
can_do: [cando.zh.describe_object_relocation_A2]
diagnostics:
  - form: "S &#25226; O V (C)"
  - function: "foregrounds object; implies affectedness"
prompts:
  - "Move X from Y to Z using &#25226;"
</code></pre>
<p><strong>SRS item</strong> links to KG:</p>
<pre><code class="language-json">{
  "item_id": "card.zh.ba3.prompt.001",
  "node_id": "constr.zh.ba3",
  "type": "production",
  "last_review": "2025-11-03T17:00Z",
  "stability": 2.4,
  "difficulty": 4.8,
  "reps": 3
}
</code></pre>
<p>Use FSRS (or SM-2 if you want trivial) with per-item difficulty + global learner params.</p>
<h1>4) The agents (clear division of labour)</h1>
<ul><li>
<p><strong>Curriculum Planner</strong>: queries the KG for the <em>frontier</em> (prereqs satisfied, not mastered) and writes a tiny plan for the session.</p>
</li><li>
<p><strong>Coach (Codex)</strong>: runs the live lesson, uses your 
templates to generate tasks, adapts in real time, and calls tools for 
“what next?”. (Codex is good at navigating your repo, honoring <code>AGENTS.md</code>, and running local commands.) (<a href="https://github.com/openai/codex?utm_source=chatgpt.com" title="openai/codex: Lightweight coding agent that runs in your ...">GitHub</a>)</p>
</li><li>
<p><strong>Assessor</strong>: scores responses (text or ASR transcript) against a rubric; emits <code>grade, rationale, evidence_nodes</code>.</p>
</li><li>
<p><strong>Scheduler</strong>: updates FSRS parameters and returns the next due items.</p>
</li><li>
<p><strong>KG Maintainer</strong>: increments evidence counts, writes misconceptions (edges like <code>addresses_error</code>) when a pattern of errors appears.</p>
</li></ul>
<p>Wire these with the Agents SDK runner so a single <code>/next</code> step does: planner &#8594; coach &#8594; assessor &#8594; scheduler &#8594; coach. (<a href="https://platform.openai.com/docs/guides/agents-sdk?utm_source=chatgpt.com" title="Agents SDK - OpenAI API">platform.openai.com</a>)</p>
<h1>5) Expose your tools via MCP (sketch)</h1>
<p>Each tool is a tiny Python MCP server:</p>
<pre><code class="language-python"># mcp_servers/kg_server.py
from agents.mcp import MCPTool
import sqlite3, json

@MCPTool("kg.next", desc="Return next learnable nodes for learner")
def kg_next(learner_id: str, k: int = 5) -&gt; str:
    # query kg.sqlite + state/mastery.sqlite; return JSON list of node_ids
    ...

@MCPTool("kg.prompt", desc="Emit task seed for a node")
def kg_prompt(node_id: str, kind: str = "production") -&gt; str:
    # read lesson_templates/ and node metadata; return a prompt scaffold
    ...
</code></pre>
<p>Do the same for <code>srs.due</code>, <code>srs.update(q, response, quality)</code>, and <code>asr.transcribe(audio_bytes)</code>.</p>
<p>OpenAI’s guide shows the pattern for wiring Codex/Agents with MCP; mirror that for your servers. (<a href="https://developers.openai.com/codex/guides/agents-sdk/?utm_source=chatgpt.com" title="Use Codex with the Agents SDK">developers.openai.com</a>)</p>
<h1>6) <code>AGENTS.md</code> (what Codex needs to be a good Coach)</h1>
<p>Keep this at repo root so Codex reads it by default:</p>
<pre><code class="language-markdown"># AGENTS.md

## Roles
- You are the **Coach** for L2 learners. Use tools:
  - `kg.next` to pick what to teach next (never guess).
  - `kg.prompt` to fetch exercise scaffolds.
  - `srs.due` to interleave reviews (spaced repetition).
  - `srs.update` after each turn with quality 0–5.
  - `asr.transcribe` for speech; correct selectively by rule:
    - meaning before form; only 1–2 targeted corrections per utterance.

## Preferences
- Correction style: implicit recasts by default; explicit only on repeated error.
- Register and topics from `state/learner.yaml`.
- Log every exercise result to `state/mastery.sqlite` via `srs.update`.

## Commands
- Run tests: `pytest`
- Start local MCP servers: `uv run mcp_servers/*.py` (or `python -m ...`)
- Data refresh: `python kg/build.py seed/ kg.sqlite`

## Conventions
- Exercises tagged by node_id; one objective each.
- Always call `kg.next` at session start; never freewheel curriculum.
</code></pre>
<p>AGENTS.md is first-class in Codex; it’s exactly where this belongs. (<a href="https://agents.md/?utm_source=chatgpt.com" title="AGENTS.md">agents.md</a>)</p>
<h1>7) Session loop (what actually happens)</h1>
<ol><li>
<p><strong>Open Codex</strong> in the repo; it reads <code>AGENTS.md</code>. Ask Codex: “Start a 20-min session for Brett.”</p>
</li><li>
<p>Codex calls <code>kg.next(learner='brett', k=3)</code> &#8594; picks 1 new node + 2 reviews (<code>srs.due</code>).</p>
</li><li>
<p>For each item, Codex calls <code>kg.prompt(node, kind)</code> to get a task scaffold, runs the conversation, and—if audio—sends the recording to <code>asr.transcribe</code>.</p>
</li><li>
<p>The <strong>Assessor</strong> (an Agent) scores the turn and <em>immediately</em> calls <code>srs.update(...)</code>.</p>
</li><li>
<p>After ~20 minutes, the <strong>Planner</strong> emits a short summary + next-time plan and updates <code>state/learner.yaml</code>.</p>
</li></ol>
<h1>8) Speech</h1>
<p>Use Whisper (local) or Realtime API (streaming) depending on 
constraints. The Agents SDK + Codex supports Realtime/tooling; MCP keeps
 the boundary clean (Codex asks a tool to transcribe/play). (<a href="https://developers.openai.com/tracks/building-agents/?utm_source=chatgpt.com" title="Building agents">developers.openai.com</a>)</p>
<h1>9) Why this matches Greer’s desiderata</h1>
<ul><li>
<p><strong>Memory/progression</strong>: lives in <code>state/</code> (mastery DB + learner prefs).</p>
</li><li>
<p><strong>Knowledge graph</strong>: explicit KG driving selection and feedback, not ad-hoc RAG.</p>
</li><li>
<p><strong>SRS</strong>: due-items interleaved with the frontier; Scheduler owns the timing.</p>
</li><li>
<p><strong>LLM for active use</strong>: Codex delivers production tasks + live correction; Duo’s passivity critique doesn’t apply.</p>
</li></ul>
<h1>10) Getting from zero to a POC (in ~1 afternoon)</h1>
<ul><li>
<p>Seed 30–50 nodes (one language) + edges + 100 cards.</p>
</li><li>
<p>Implement <code>srs.due/update</code> with FSRS defaults.</p>
</li><li>
<p>Implement <code>kg.next/prompt</code> and one rubric.</p>
</li><li>
<p>Write the <code>AGENTS.md</code> above and point Codex at the repo.</p>
</li><li>
<p>Drive the loop manually first (single agent); then add the Assessor and Scheduler as standalone Agents.</p>
</li></ul>
<p>If you want, I can tailor the seed KG to your EAP B1 speaking-fluency
 course (topics, functions, and constructions), and drop in the 
selective-correction policy you like. For the plumbing bits I referenced
 above, the official docs/tutorials are here: Codex CLI &amp; product 
pages, Agents guides/SDK, and Codex&#8596;Agents via MCP. (<a href="https://developers.openai.com/codex/cli/?utm_source=chatgpt.com" title="Codex CLI">developers.openai.com</a>)</p></body></html>