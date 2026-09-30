# Phoenix Cache Refresh

The Phoenix cache refresh project replaces our nightly batch cache rebuild with an event-driven refresh pipeline, cutting stale data windows from 6 hours to under 5 minutes.

## Goals

- Cut the stale data window to under 5 minutes.
- Remove the nightly batch job entirely.
- Keep p99 read latency under 20ms during refresh.

## Risks

- Event ordering bugs could serve newer data after older data.
- The message queue must handle 3x peak traffic without dropping events.

## Timeline

We plan to ship the first region in November, then roll out to the remaining regions in December.

Open questions: Who owns the on-call rotation for the new pipeline? Should we backfill historical data or start fresh?
