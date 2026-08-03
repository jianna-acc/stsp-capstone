<!-- File: /docs/AI_PREPARATION_PIPELINE.md -->
<!-- Purpose: Documents the offline study-material chunking and embedding-request preparation pipeline. -->

# AI Study-Material Preparation Pipeline

## Overview

Phase 4C introduces the offline preparation pipeline used to convert extracted study-material text into deterministic chunks and controlled embedding requests.

The pipeline prepares data for a future retrieval-augmented generation workflow, but it does not call Gemini or persist vector embeddings during Phase 4C.

## Phase 4C Scope

Phase 4C provides:

- Validated chunking and embedding-batch configuration.
- Provider-independent chunking contracts.
- Deterministic text normalization.
- Boundary-aware text chunking.
- Configurable chunk overlap.
- Maximum chunk-count enforcement.
- Deterministic embedding batches.
- Retrieval-document embedding requests.
- File-processing integration.
- Controlled preparation failures.
- Offline unit and integration tests.

Phase 4C does not provide:

- Live Gemini embedding calls.
- Vector database persistence.
- Similarity search.
- Retrieval APIs.
- AI-generated reviewer content.
- Chatbot responses.

These capabilities belong to later phases.

## Processing Flow

```mermaid
flowchart TD
    A[Private study file] --> B[FileProcessorService]
    B --> C[Download from private Supabase Storage]
    C --> D[extract_document]
    D --> E[ExtractedDocument]

    E --> F[Existing source-aware chunking]
    F --> G[ExtractedChunk list]
    G --> H[complete_study_file_processing RPC]
    H --> I[Existing database chunk records]

    E --> J[StudyMaterialPreparer]
    J --> K[ChunkingRequest]
    K --> L[TextChunker]
    L --> M[ChunkingResult]
    M --> N[EmbeddingBatchPreparer]
    N --> O[EmbeddingBatch list]
    O --> P[EmbeddingRequest list]
    P --> Q[Held in memory only]

    Q -. Phase 4C makes no provider call .-> R[GeminiProvider]
    Q -. Phase 4C makes no vector write .-> S[Future vector storage]
Two Chunk Representations

Phase 4C intentionally maintains two separate chunk representations.

ExtractedChunk

ExtractedChunk belongs to the existing file-extraction pipeline.

It stores:

Chunk index.
Text content.
Locator type.
Locator label.
Estimated token count.
Source metadata.

Examples of source locators include:

PDF page.
PowerPoint slide.
Excel worksheet.
Complete text document.

These chunks continue to be sent to the existing complete_study_file_processing Supabase RPC.

StudyMaterialChunk

StudyMaterialChunk belongs to the new AI preparation pipeline.

It stores:

Material ID.
Contiguous chunk index.
Normalized text.
Start character offset.
End character offset.
Optional source filename.
Deterministic chunk key.

These chunks are prepared for future embeddings but are not persisted during Phase 4C.

The two models are kept separate so the current source-aware database behavior remains stable while the AI pipeline evolves independently.

Configuration

The following settings control preparation:

SettingDefaultPurpose
AI_CHUNK_TARGET_CHARACTERS2400Preferred maximum size of one AI chunk
AI_CHUNK_OVERLAP_CHARACTERS300Text shared between neighboring chunks
AI_CHUNK_MIN_CHARACTERS200Minimum acceptable final fragment
AI_EMBEDDING_BATCH_SIZE16Maximum chunks in one embedding request
AI_MAX_CHUNKS_PER_MATERIAL1000Safety limit for one material

Configuration relationships are validated during application startup.

The overlap must be smaller than the target size, and the minimum chunk size must not exceed the target size.

Text Normalization

TextChunker.normalize_text() performs deterministic normalization by:

Converting Windows and legacy line endings to \n.
Replacing non-breaking spaces.
Collapsing repeated inline whitespace.
Removing leading and trailing whitespace from lines.
Collapsing repeated blank lines.
Removing leading and trailing document whitespace.

Identical text and configuration must always produce identical normalized output and chunks.

Boundary Selection

When a document exceeds the configured target size, the chunker prefers the strongest available boundary in this order:

Paragraph boundary.
Sentence boundary.
Newline boundary.
Word boundary.
Hard character boundary.

The chunker never depends on Gemini or another external service to decide boundaries.

Chunk Overlap

Overlap preserves context between neighboring chunks.

The chunker calculates the next start position from the previous chunk's end offset and moves toward a safe word boundary where possible.

When overlap is zero, neighboring chunks do not share character ranges.

Final Fragment Handling

When a final fragment is smaller than AI_CHUNK_MIN_CHARACTERS, it is merged into the preceding chunk.

This prevents extremely small final chunks that provide little retrieval value.

Maximum Chunk Protection

The chunker raises AIChunkingError when one material would exceed AI_MAX_CHUNKS_PER_MATERIAL.

This prevents unexpectedly large files from creating unbounded processing work.

Embedding-Batch Preparation

EmbeddingBatchPreparer divides ordered chunks according to AI_EMBEDDING_BATCH_SIZE.

It guarantees:

Batch indexes begin at zero.
Batch indexes are contiguous.
Chunk order is preserved.
Every chunk appears exactly once.
No batch exceeds the configured limit.
A final partial batch is retained.

Each batch is converted into an EmbeddingRequest using:

EmbeddingTaskType.RETRIEVAL_DOCUMENT

Phase 4C constructs these requests but does not send them.

File-Processing Integration

FileProcessorService.process_file() performs the following sequence:

Load the study-file and processing-job records.
Validate the file and job owner.
Start or accept the current processing state.
Download the private Storage object.
Extract normalized document content.
Run offline AI preparation.
Generate the existing source-aware chunks.
Mark the file as indexing.
Persist extracted content and source-aware chunks.
Mark processing as completed.

The offline preparation step occurs before indexing and database completion.

Failure Handling

Preparation failures are converted into:

FileProcessorPreparationError

When processing has already started, the processor attempts to save:

error_code = PREPARATION_FAILED

A preparation failure prevents:

The indexing transition.
Database completion.
Successful worker completion.

The worker already handles FileProcessorError, so no Phase 4C worker modification is required.

External-Call Boundary

The following objects are created in Phase 4C:

ChunkingResult
EmbeddingBatch
EmbeddingRequest
StudyMaterialPreparation

The following actions are intentionally not performed:

GeminiProvider.embed(...)
Vector persistence
Similarity search

The application setting below must remain disabled during offline validation:

AI_LIVE_SMOKE_TESTS_ENABLED=false
Test Coverage

Phase 4C adds tests for:

Chunking configuration.
Chunking contracts.
Text normalization.
Paragraph and sentence boundaries.
Hard character splitting.
Overlap behavior.
Character offsets.
Maximum chunk limits.
Embedding batching.
Request preparation.
Preparation-result validation.
Complete offline preparation.
File-processor integration.
Controlled preparation failure.

The complete backend suite contains 125 passing tests at the end of Phase 4C.5B.

Next Phase Boundary

The next implementation stage may add:

A database schema for vector-ready AI chunks.
Gemini embedding execution.
Safe embedding persistence.
Retry and idempotency behavior.
Similarity-search database functions.
Retrieval services and APIs.

Those changes must preserve the existing source-aware extraction records and must not expose backend credentials.

<!-- PHASE 4D PREPARATION INTEGRATION START -->
# Current Downstream Integration Status

The preparation pipeline is no longer an isolated or future-only component.

Its implemented downstream flow is:

```text
Extracted document text
? StudyMaterialPreparer
? StudyMaterialPreparation
? StudyMaterialEmbedder
? Gemini retrieval_document embeddings
? StudyMaterialVectorIndexer
? validated persistence payload
? Supabase study_file_ai_chunks
```

Any earlier statement in this document that describes embedding execution or vector persistence as future work is superseded by this section.

The preparation layer remains responsible only for deterministic local work:

- Text normalization.
- Chunk creation.
- Character offsets.
- Stable chunk ordering.
- Source filename preservation.
- Embedding batching.
- Provider-independent embedding requests.

The preparation layer does not:

- Read Gemini credentials.
- Call Gemini directly.
- Write to Supabase directly.
- Change processing database state.
- Complete the processing job.

Those responsibilities belong to:

| Responsibility | Component |
|---|---|
| Execute embedding requests | `StudyMaterialEmbedder` |
| Validate provider vectors | `StudyMaterialEmbedder` |
| Build validated RPC payloads | `vector_persistence.py` |
| Orchestrate embedding and persistence | `StudyMaterialVectorIndexer` |
| Persist through trusted RPC | `SupabaseAdminService` |
| Control processing order and failure codes | `FileProcessorService` |

See `/docs/AI_VECTOR_PIPELINE.md` for the complete implemented downstream workflow.
<!-- PHASE 4D PREPARATION INTEGRATION END -->
