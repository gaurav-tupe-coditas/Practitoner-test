# ADR-0002: Gmail drafts through a one-method port

- **Status:** Accepted
- **Date:** 2026-11-24
- **Decided by:** User (option A of OQ-1)

## Context
`followup` must create a Gmail draft through the Gmail MCP connector and never send (FR-8). A Python CLI cannot call an MCP connector itself, and the notes hold no recipient addresses. The connector also needs authorising before it can be tested live.

## Options
- A. Port with a file adapter and a `claude` CLI adapter (chosen)
- B. File only, a Claude session creates the draft by hand
- C. Gmail API directly (not the MCP connector, adds credentials)

## Decision
Option A. `DraftSink` has one method, `create_draft(draft)`. There is no send method anywhere in the code base. `FileDraftSink` writes `drafts/<owner>-<date>.json` and is the default and the test double. `ClaudeGmailDraftSink` runs the `claude` CLI headless with only the Gmail create-draft tool allowed, with a fixed argument list and no shell. Recipient comes from a required `--to <email>` flag and is never stored.

## Consequences
- AC-8.4 is enforced structurally and by a test that scans the code for send operations.
- The Claude sink cannot be verified live until the connector is authorised; its command line is covered by a unit test with a fake runner.
- Sink failure prints the full draft and exits 3 (AC-8.6), so nothing is lost.
- Reversing to B means deleting one adapter; moving to C means writing a new adapter and handling credentials.
