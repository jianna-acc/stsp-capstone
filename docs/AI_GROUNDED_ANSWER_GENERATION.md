<!-- File: /docs/AI_GROUNDED_ANSWER_GENERATION.md -->

# AI Grounded Answer Generation

## Purpose

Phase 5D generates student-friendly answers using only the study-material chunks retrieved by the Phase 5C retrieval pipeline.

The completed workflow is:

```text
Student question
→ Gemini retrieval-query embedding
→ Supabase vector retrieval
→ bounded study-context prompt
→ Gemini answer generation
→ validated answer with source references

Main Components
Grounded-answer contracts

File:

backend/app/ai/grounded_answer_contracts.py

This file defines:

GroundedAnswerRequest
GroundedSourceReference
GroundedAnswerResult
GroundedAnswerOutcome
Stable Phase 5D failure codes
Normal no-context behavior
Source-order and source-identity validation
Provider and model metadata validation

A request contains the student question and the retrieved RetrievedStudyChunk objects.

The supported successful outcomes are:

Outcome	Meaning
answered	Study context was available and a grounded answer was produced.
no_context	No relevant study context was available, so Gemini was not called.

The approved no-context answer is returned without making an external generation request.

Controlled Prompt Builder

File:

backend/app/ai/grounded_prompt.py

The GroundedPromptBuilder converts retrieved chunks into a bounded and structured prompt.

The builder:

Accepts only a validated GroundedAnswerRequest.
Preserves retrieval similarity order.
Limits the number of included chunks.
Limits the total source-content character count.
Normalizes control characters and newlines.
Assigns deterministic [Source N] markers.
Excludes internal UUIDs and embedding vectors from the prompt.
Treats uploaded document text as untrusted reference data.
Returns an effective request containing only the chunks sent to Gemini.

The default limits are:

Maximum context chunks: 8
Maximum context characters: 24,000
Maximum question characters: 4,000
Prompt-Injection Boundary

Uploaded study materials may contain text that resembles instructions.

The grounded system instruction tells Gemini to treat all study-source text as untrusted data rather than executable instructions.

The model is instructed not to:

Change system rules based on document content
Reveal credentials
Execute code
Access external systems
Use outside knowledge to fill missing information
Invent source numbers

This is a prompt-level safety boundary and does not replace backend validation.

Grounded-Answer Generation Service

File:

backend/app/services/grounded_answer_generation.py

The GroundedAnswerGenerationService:

Validates the grounded-answer request.
Returns the approved no-context result when no chunks exist.
Builds a bounded prompt.
Calls the configured GenerationProvider.
Validates the provider result.
Validates citation markers.
Preserves source metadata for the chunks actually sent to Gemini.
Returns a GroundedAnswerResult.
Closes provider resources through aclose().

The result does not expose:

Raw embedding vectors
Supabase service credentials
Gemini credentials
Unused retrieved chunks
Citation Handling

Generated citations use the exact format:

[Source 1]
[Source 2]

The service validates that:

At least one supplied source is referenced
Citation markers use the approved format
Citation numbers refer only to sources supplied to Gemini
Malformed or out-of-range citations are rejected

When Gemini omits citations, the service performs one citation-correction retry using the exact allowed markers.

When the second response is otherwise valid but still contains no citation marker, the service appends a deterministic source-reference footer:

Sources consulted: [Source 1]

The footer contains only sources actually supplied to Gemini.

The fallback does not repair malformed citations or permit nonexistent source numbers.

Provider Failures

Stable Phase 5D failure codes include:

Failure code	Meaning
GROUNDED_ANSWER_VALIDATION_FAILED	The question, context, prompt limits, or generation settings are invalid.
GROUNDED_ANSWER_GENERATION_FAILED	The configured AI provider could not generate an answer.
GROUNDED_ANSWER_RESPONSE_FAILED	The provider result, citations, source references, or final result are inconsistent.

Provider exceptions are converted into controlled Phase 5D errors.

FastAPI Dependency

File:

backend/app/api/grounded_answer_generation_dependency.py

The dependency:

Reads backend settings.
Constructs GeminiProvider.
Constructs GroundedAnswerGenerationService.
Yields the configured service.
Closes provider resources after use.

Gemini credentials remain backend-only.

No public grounded-answer route is added during Phase 5D.

Service Export

File:

backend/app/services/__init__.py

Phase 5D publicly exports:

GroundedAnswerGenerationService

This allows later backend routes and orchestration layers to import the service consistently.

Guarded Live Smoke Test

Script:

backend/scripts/smoke_live_grounded_answer_generation.py

Run it from the backend directory as a module:

python -m scripts.smoke_live_grounded_answer_generation

The live workflow performs:

Gemini query embedding
→ Supabase retrieval
→ grounded prompt construction
→ Gemini answer generation
→ citation and source validation

The script is guarded by:

AI_LIVE_SMOKE_TESTS_ENABLED

Its safe default is:

false

The live script does not print:

User IDs
Study-file IDs
Subject IDs
Chunk IDs
Source filenames
Complete source content
Complete student question
Embedding vectors
Gemini or Supabase credentials

Only safe counts, outcomes, and metadata-presence flags are printed.

Test Coverage

Phase 5D adds:

backend/tests/test_grounded_answer_contracts.py
backend/tests/test_grounded_prompt.py
backend/tests/test_grounded_answer_generation.py
backend/tests/test_grounded_answer_generation_dependency.py
backend/tests/test_live_grounded_answer_smoke_script.py

The tests cover:

Question and chunk validation
Duplicate and similarity-order rejection
Deterministic source references
Normal no-context behavior
Prompt context limits
Prompt truncation
Control-character normalization
Prompt-injection handling
UUID exclusion
Provider request construction
Provider failure wrapping
Citation validation
Citation-correction retry
Source-footer fallback
Unknown and malformed citation rejection
Provider cleanup
Dependency construction and cleanup
Disabled live-smoke behavior
Safe live-smoke output
Offline end-to-end smoke behavior

Normal automated tests use fake providers and do not call Gemini or Supabase.

Security Boundaries
Gemini is called only by the backend.
Supabase service credentials remain backend-only.
Raw embeddings are never placed in the answer result.
Internal UUIDs are excluded from the Gemini prompt.
Only retrieved chunks selected by the prompt builder are preserved as sources.
Uploaded material is treated as untrusted reference data.
No-context requests do not call Gemini.
Live external testing is disabled by default.
Unexpected CLI failures are converted into safe error codes.
Live Validation Result

Phase 5D successfully completed one guarded live workflow using an existing ready and indexed study file.

The live validation confirmed:

Query embedding generation
Supabase vector retrieval
Grounded context construction
Gemini answer generation
Source preservation
Citation handling
Safe metadata output
Resource cleanup
Restoration of the disabled live-test default