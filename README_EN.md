# Content Review Copilot
## AI-assisted review, rule checks, and traceable rewriting for branded content

[简体中文](README.md) · English

Content Review Copilot is a portfolio prototype for reviewing branded social content. It turns “read a draft, flag issues, revise it, and check it again” into an actionable workflow: define the review basis, inspect the draft section by section, let an editor decide on each suggestion, generate an optimized draft, run a second review, and prepare an exportable final version with its review history.

The problem it explores is concrete: brand reviews often depend on a brief, brand guidelines, product knowledge, platform rules, and editorial judgment at the same time. When those sources live in separate documents or workflows, it is difficult to trace why a change was requested or to verify that earlier issues were resolved after rewriting. This prototype connects rule sources, issue evidence, human decisions, revision, and re-review in one session.

> **Project status and demo boundaries**
>
> This is a locally runnable portfolio prototype with synthetic data. The default `MockLLMProvider` needs no API key; the brand, product, draft, and image cues in the demo below are fictional. This is not a production service connected to real enterprise data, and no real-world accuracy result is claimed.
>
> The repository contains two interfaces: a five-step editorial workflow built with React + FastAPI, and a Streamlit workbench for developers. The default model is mock. A real provider can call an OpenAI-compatible text endpoint, but its vision method is currently unimplemented. Image cues in the demo are passed as text to the mock provider and do not demonstrate actual image recognition.

## A concrete review walkthrough

The example below uses a fictional daily product post to show the path from review brief to final copy. The product, rules, and text are synthetic and are not real brand guidance or legal advice.

### 1. Create the review task

| Setting | Example |
| --- | --- |
| Content type | Product experience / Daily sharing |
| Content goal | Brand awareness |
| Writing style | Natural and authentic |
| Required keyword | `轻盈奶粉` |
| Target persona | New mother: sincere, restrained, specific |
| Image cues | `Breakfast kitchen`, `package text` (text labels understood by the mock, not visual recognition) |
| Review basis | Task requirements, demo brand rules, demo product knowledge, demo platform rules, and a content quality rubric |
| Rewrite intensity | Standard |

Editors can paste copy or upload TXT, Markdown, DOCX, or PDF. The task view summarizes the review focus and the sources and versions used. Task, brand, product, platform, quality, and custom rules are captured in a review-policy snapshot for the session.

### 2. Source draft

```text
#日常
根治问题，产品体验很好。
推荐轻盈奶粉。
```

The sample deliberately includes observable issues: the demo prohibited term “根治”; an opening with no specific scene; a core section with only a vague positive statement; a direct recommendation as the ending; and a required keyword that appears in the ending but not the core section.

### 3. Example issue cards

| Issue card | Source evidence | Severity | Suggested action |
| --- | --- | --- | --- |
| Medical efficacy claim | “根治问题” | Mandatory / high | Remove or replace “根治” under the configured rule, then scan the revision again |
| Opening lacks a scene | The copy moves from “#日常” directly to a conclusion | Suggested improvement | Add a person, time, or usage context; do not invent an experience that was not provided |
| Core lacks specific support | “产品体验很好” | Suggested improvement | Use supplied product facts or experience details; do not make up product benefits when evidence is missing |
| Keyword coverage is incomplete | “轻盈奶粉” does not appear in the core section | Suggested improvement | Include the keyword naturally in the core content |
| Ending is too direct | “推荐轻盈奶粉” | Suggested improvement | End with a measured, needs-based statement |

Issue cards show source evidence, issue type, rule source/reference, severity, and suggested text. Hard issues are marked mandatory; the editor can accept, ignore, or regenerate softer writing suggestions. The API workflow also includes a claim guard for newly introduced high-risk numbers or statements: when a generated draft adds unsupported patterns, such as statistics or guarantees, the workflow stops and asks for evidence or revision.

> Demo note: the precise issue list depends on the current parser, synthetic rule files, and how the draft is segmented. The table is an explanatory case based on repository code and synthetic rules; it is not a screenshot or a measured response from a live LLM.

### 4. Editorial decisions and rewrite plan

An editor might:

- Accept “remove or revise the medical efficacy wording”.
- Accept “add a concrete everyday scene to the opening”.
- Accept “include the keyword in the core and use supported facts”.
- Accept “make the ending more restrained”.
- Ignore or request regeneration for another suggestion.

The system then builds a rewrite task from those decisions instead of treating revision as an opaque one-click operation. The product UI shows which review sources apply. The API checks that mandatory issues have been addressed before continuing to the next step.

### 5. Example optimized copy

The following is a **human-written target example** to illustrate the intended shape of a revision. It is **not output observed from the repository's mock provider**. The default mock generation may return the source or a fixed fallback for repeatability. With a live compatible model, wording depends on the model, input, and configuration.

```text
最近准备早餐时，我顺手记录了这次轻盈奶粉的体验。

关于产品本身，我会先看配方和包装上标注的信息，再结合自己的日常需求判断是否适合。仅凭“体验很好”这样的概括，还不足以说明具体感受；如果有真实使用细节，可以补充在这里。

如果你也在了解轻盈奶粉，建议先核对产品标签和自己的需求，再做选择。
```

The example intentionally avoids unsupported benefits such as “improves sleep” or “boosts immunity”, as well as invented usage periods, review counts, or effect percentages. If the project knowledge base contains verified facts such as a product specification, those facts can be added to the copy with their source.

### 6. Second review, final version, and history

After generation, the editor can modify the draft and start a second review. The pipeline checks the new copy again for mandatory issues and missing keywords. If issues remain, the editor handles them before finalization. The UI supports:

- Applying accepted second-review suggestions to generate a final version.
- Marking the current draft as final when the editor is satisfied.
- Copying final text or exporting Word.
- Reopening a saved review session and inspecting its state and versions.

API workflow states include `NEW_REVIEW`, `WAITING_FOR_FIRST_DECISIONS`, `OPTIMIZED_DRAFT_READY`, `WAITING_FOR_SECOND_DECISIONS`, and `READY_TO_DELIVER`. Session content and decisions are stored in local SQLite. The Streamlit workbench also supports version saving, version comparison, and Markdown/Word export.

## Product workflow

| Stage | Input / action | System output | Editor control |
| --- | --- | --- | --- |
| Task setup | Draft, content type, goal, style, keyword, persona, image cues | Review task and policy snapshot | Adjust brand/quality rules and add custom rules |
| First review | Parse copy and check rules and keyword placement | Section diagnoses, evidence, severity, suggestions | Accept, ignore, or regenerate each suggestion |
| Rewrite | Use accepted suggestions, product knowledge, and review policy | Optimized draft, title options, tags, rewrite validation | Edit the draft and decide whether to begin the second review |
| Second review | Run the review pipeline on the optimized draft | Remaining issues and review results | Handle new or unresolved issues |
| Finalization | Apply second-review changes or keep the current draft | Final copy, tags, exportable file | Copy content, export Word, and inspect history |

## How review policy is organized

A review session can combine the following sources and record their source, version, and rule count:

1. **Task requirements:** Required keywords, content goal, and writing style from the current brief.
2. **Brand rules:** For example, consistent brand naming and restrictions on unsupported benefit claims.
3. **Product knowledge:** Structured product facts, such as specifications or official descriptions.
4. **Platform rules:** The sample rule file is explicitly marked synthetic and is not an official platform policy.
5. **Content quality rubric:** Structure, naturalness, persona alignment, CTA naturalness, and image-text consistency.
6. **Custom rules:** Rules with a selected type, scope, and severity.

Pydantic models represent policies and rules, including source, version, priority, scope, required terms, and prohibited terms. The policy builder checks conflicts between required and prohibited terms and generates a policy ID from the rule content. Rules and product knowledge are read through local JSON repositories. These files demonstrate the data contract, not a real enterprise knowledge base.

## How the system works

### Layered architecture

- **React frontend:** Create review tasks, configure rules, present workflow steps, collect editorial decisions, edit drafts, view history, and export.
- **FastAPI service:** Expose endpoints for creating reviews, first review, decisions, rewriting, second review, finalization, history, and DOCX export.
- **Review workflow service:** Maintain session state and decisions; prevent mandatory issues from advancing without action.
- **Python pipeline:** Coordinate input parsing, policy creation, context resolution, image-cue handling, rule checks, section diagnoses, rewrite planning, generation, validation, and result assembly.
- **Local data layer:** JSON stores rules, knowledge, personas, directions, and reference articles; SQLite stores review sessions.
- **Streamlit developer workbench:** Offers a second local entry point to inspect diagnoses, evaluation, policy, provider state, and execution traces.

### Pipeline data flow

```text
Draft + brief + image cues
        ↓
Pydantic input validation / policy snapshot / context resolution
        ↓
Rule and knowledge retrieval ── image cues converted into structured descriptions
        ↓
Hard-rule cleanup / parsing / opening, core, ending, and persona diagnosis
        ↓
Issue aggregation / rewrite plan / full or staged generation
        ↓
Post-rewrite validation / one feedback retry when validation fails
        ↓
Final evaluation / report / workflow state / execution trace
```

Key modules:

| Module | Responsibility |
| --- | --- |
| `InputParser` / Pydantic models | Validate drafts, rules, decisions, and output contracts |
| `ReviewPolicyBuilder` | Combine task, brand, product, platform, quality, and custom rules |
| `RuleRetriever` / `KnowledgeRetriever` | Read constraints and writing context from JSON repositories |
| `DeterministicRuleEngine` | Apply explicit prohibited-term cleanup and record replacements |
| `ContentParser` | Split copy into title, opening, core, ending, and tags |
| Section evaluators | Check structure, keyword placement, facts/image cues, and persona |
| `RewritePlanner` / `GenerationRouter` | Turn accepted issues into a plan and choose full or staged generation |
| Rewrite generators | Generate a full draft or pass context in opening → core → ending order |
| `RewriteQualityValidator` | Check target issues, required keyword, hard rules, fact preservation, meaningful change, and new issues |
| `TraceRecorder` / ResultAssembler | Record stage status, summaries, latency, and errors; assemble the report |

### Explicit rules vs semantic evaluation

The system uses deterministic checks for mechanical conditions such as prohibited terms, required keywords, and explicit length limits. More contextual judgments, such as naturalness, persona, and coherence, sit at the semantic evaluation boundary. The policy distinguishes hard and soft rules: hard rules are intended to block noncompliant content from finalization, while soft rules become suggestions for editorial review.

After rewriting, `RewriteQualityValidator` checks whether target issues were resolved, required terms are present, brand/product names found in the source are preserved, hard-rule fixes remain, the text changed sufficiently, and new issues were introduced. If validation fails, the pipeline retries once with feedback and validates again. This is a post-generation gate, independent of the generator's self-reported result.

## Data and evaluation

- `data/` contains synthetic JSON examples for brand rules, platform rules, product knowledge, quality rubrics, content directions, personas, and references.
- `benchmark/dataset.jsonl` contains **30 synthetic cases** covering compliance, keywords, structure, product facts, persona, image cues, and edge inputs.
- `python -m benchmark.runner` computes issue precision, recall, F1, compliance pass rate, average latency, and estimated cost.
- No model accuracy or performance number is preclaimed here. A run only describes the current code, data, and provider configuration; it is not evidence of real brand-review accuracy.
- The developer workbench records per-stage latency and traces. Estimated cost is produced by the current token-estimation logic and should be calibrated against actual provider billing.

## Technology

| Layer | Technology |
| --- | --- |
| Editorial UI | React, TypeScript, Vite, Tailwind CSS |
| API | Python, FastAPI, Pydantic |
| Review and generation | Modular Python pipeline, provider abstraction, deterministic rule engine |
| Local storage | JSON rules/knowledge, SQLite review history |
| Developer UI | Streamlit |
| Document/data handling | python-docx, pypdf, pandas, openpyxl |

## Run locally

Python 3.11+ and Node.js/npm are required.

### Start the API

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn api.main:app --reload
```

The API defaults to `http://127.0.0.1:8000`. Visit `/api/health` for a health check.

### Start the React editorial interface

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite defaults to `http://localhost:5173` and is configured to proxy the local API.

### Start the Streamlit developer workbench

From the repository root:

```bash
streamlit run app.py
```

The workbench has a bilingual interface and Product/Developer modes for workflow and technical details.

### Run the offline benchmark

```bash
python -m benchmark.runner
```

This command processes 30 synthetic cases. Its scores should not be interpreted as an online quality guarantee.

### Optional: configure a live text model

Create a `.env` file in the repository root with settings for an OpenAI-compatible Chat Completions service:

```dotenv
LLM_PROVIDER=openai
LLM_MODEL=your-model-name
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
```

The current `RealLLMProvider` implements text generation and text-based structured output. Its vision method is not implemented. Do not commit `.env` files or API keys. A live model connection still requires separate validation of model behavior, rule performance, cost, and latency.

## Repository map

```text
app.py                     Bilingual Streamlit developer workbench
api/
  main.py                  FastAPI routes and app entry point
  service.py               Five-stage review workflow, claim guard, export
  store.py                 SQLite session storage
backend/
  pipeline.py              Review pipeline and traces
  policy.py                Policy assembly and hard/soft rule evaluation
  providers.py             Mock / OpenAI-compatible providers
  services.py              Parsing, section diagnosis, context, and routing
  generators.py             Full and staged generators
  validation.py             Post-generation rewrite validation
  repositories.py           JSON rule/knowledge retrieval
frontend/
  src/App.tsx               React editorial workflow
  src/api.ts                Frontend API client
data/                       Synthetic rules, product knowledge, persona, rubric
benchmark/                  30 synthetic cases and metric implementation
docs/                       Workflow analysis and architecture mapping
tests/                      Python tests
```

## Design choices and limits

- **Traceable review basis:** Issue cards include evidence and rule sources; a session stores a policy snapshot.
- **Editorial control:** Suggestions can be accepted, ignored, or regenerated; the system keeps editorial decisions explicit.
- **Hard rules and style guidance are distinct:** Required/prohibited terms and high-risk issues can block progression; writing-quality suggestions remain reviewable.
- **Revisions are checked:** The pipeline reviews the draft again and can retry once with validation feedback.
- **Claims need support:** Input and product knowledge are the basis for product statements; guards check for unsupported new number/guarantee patterns.
- **Synthetic demos are not operational findings:** The sample platform rules are explicitly synthetic, not official policy; the mock benchmark does not show real-world accuracy.
- **Visual limits are explicit:** The mock accepts text cues; the real provider's vision implementation is currently empty.

## Project docs

- [Original workflow analysis](docs/original_workflow_analysis.md)
- [New architecture](docs/new_architecture.md)

## License

The repository does not currently declare an open-source license. Confirm licensing before reuse or distribution.

