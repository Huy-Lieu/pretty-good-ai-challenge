# Bug Report: Pivot Point Orthopedics Scheduling Agent

## Summary

I ran 16 distinct test calls against the agent, each a different patient persona
crossed with a different task (booking, rescheduling, canceling, refills,
insurance questions, and several edge cases). The calls were designed to vary on
two axes at once: what the caller wants, and what kind of caller they are
(brisk, elderly, flustered, frustrated, vague, interrupting, and so on).

The dominant finding is not a scattered list of unrelated defects. **Thirteen of
the sixteen calls converged on the same failure:** the agent could not complete
identity verification, abandoned the task, and handed off to a "patient support
team" line that immediately disconnects. The three calls that succeeded were the
three that either required no verification or happened to clear it. In other
words, a single systemic break in the verification flow blocks the agent's core
purpose across nearly every scenario, regardless of who is calling or why.

On top of that systemic issue, individual calls surfaced several independent
bugs: the agent mishears and corrupts clearly-spelled names and dates, breaks
character by referencing "demo purposes," changes a provider's name mid-call,
and plays an inconsistent bilingual disclaimer.

Every finding below cites the scenario that triggered it. Each scenario maps to
a Twilio call SID and its recording and transcript via `results/manifest.json`.

## Severity definitions

- **Critical** — blocks the caller from completing the core task.
- **High** — produces wrong data or breaks the agent's role/character.
- **Medium** — degrades quality or ignores caller intent, but task may still complete.
- **Low** — cosmetic or inconsistent surface behavior.

## Findings at a glance

| # | Severity | Bug | Evidence (scenarios) |
|---|----------|-----|----------------------|
| 1 | **Critical** | Identity-verification loop prevents task completion | 13 of 16 calls; clearest in `out_of_scope`, `reschedule_elderly`, `cancel_fee_worried`, `closed_saturday` |
| 2 | **Critical** | Fallback handoff dead-ends at a disconnect | every failed call (e.g. `reschedule_elderly`, `refill_elderly`, `cancel_flustered`) |
| 3 | **High** | Mishears and records clearly-spelled names and dates incorrectly | `closed_saturday` (Reyes→Rice), `reschedule_elderly` (Brennan→Bredin, 1948→1938), `interrupt_redirect` (Cho→Joe/Toe) |
| 4 | **High** | Breaks character by revealing it is a demo | `new_patient_paperwork` |
| 5 | **Medium** | Provider name changes within a single call | `new_patient_paperwork` (Doogie Howser → Duddy Hauser) |
| 6 | **Medium** | Ignores explicitly stated caller intent while stuck on verification | `cancel_fee_worried`, `vague_request` |
| 7 | **Low** | Inconsistent / garbled bilingual recording disclaimer | `book_brisk`, `book_for_family`, `conflicting_info` |

---

## Detailed findings

### 1. [Critical] Identity-verification loop prevents task completion

The agent repeatedly asks the caller to spell their name and confirm their date
of birth, fails to register the answer, and asks again, often three or more times
for the same field, before giving up entirely. This blocked 13 of 16 calls. The
caller answers correctly each time; the agent does not advance.

Representative exchange (`out_of_scope`):

```
[01:05] BOT: First name Ben, B E N. Last name Castillo, C A S T I L L O.
[01:10] AGENT: Could you please spell your first and last name for me?
[01:11] BOT: Yeah. First name Ben, B E N. Last name Castillo, C A S T I L L O.
[01:17] AGENT: Thank you. Could you also spell your first name?
[01:21] AGENT: Could you please spell your first name, Ben?
```

The same loop appears in `reschedule_elderly`, `cancel_fee_worried`,
`closed_saturday`, `interrupt_redirect`, `conflicting_info`, and others.

**Expected:** once the caller clearly provides and spells their identifying
details, the agent should accept them and proceed to the task.

**Impact:** this is the agent's primary failure mode. Because nearly every task
requires verification, this single defect prevents the agent from doing its job
in the large majority of calls.

### 2. [Critical] Fallback handoff dead-ends at a disconnect

When the agent gives up, it says it will connect the caller to a "patient support
team," then the line immediately disconnects with a generic test-line goodbye.
The escape hatch leads nowhere.

Representative exchange (`reschedule_elderly`):

```
[03:43] AGENT: Connecting you to a representative. Please wait.
[03:51] AGENT: Hello, you've reached the Pretty Good AI Test Line. Goodbye.
```

This identical dead-end terminates every one of the failed calls.

**Expected:** the handoff should reach a real queue, take a callback number, or
at minimum not present itself as a transfer when it is actually a disconnect.

**Impact:** even when the agent correctly recognizes it cannot proceed, the
caller is left with no path to resolution.

### 3. [High] Mishears and records clearly-spelled names and dates incorrectly

After the caller spells a name letter by letter, the agent reads it back wrong,
and similarly corrupts dates of birth. This is more serious than the loop because
it is a data-integrity error: the agent commits incorrect identifying information.

Evidence:

- `closed_saturday`: caller spells "R-E-Y-E-S"; agent confirms the name as
  "Tom **Rice**."
- `reschedule_elderly`: "Brennan" becomes "Walter **Bredin**," and the agent reads
  the birth year back as **1938** instead of the stated **1948**.
- `interrupt_redirect`: caller spells "C-H-O"; agent asks whether it is spelled
  "J-O-E," then later "T-O-E."

```
[03:13] AGENT: Please say your full date of birth, including the month, day, and year.
[03:14] BOT: February 2nd, 1948.
[03:19] AGENT: Just to confirm, is your date of birth February 2, 1938?
[03:20] BOT: No, it's 1948.
```

**Expected:** identifying details that are spelled out should be transcribed and
confirmed accurately.

**Impact:** in a medical context, silently recording a wrong name or birth year
is a chart-integrity and patient-matching risk, not merely an inconvenience.

### 4. [High] Breaks character by revealing it is a demo

In the one new-patient call that proceeded, the agent acknowledged a data
mismatch by openly referencing its demo nature to the caller.

Exchange (`new_patient_paperwork`):

```
[00:40] AGENT: The birthday doesn't match our records, but for demo purposes
        I'll accept it. How can I help you today?
```

**Expected:** the agent should never surface internal/test framing to a caller;
to a real patient this is confusing and erodes trust.

**Impact:** breaks the professional illusion and exposes that verification is not
actually being enforced.

### 5. [Medium] Provider name changes within a single call

> Note: confirm against the audio recording before final submission. The two
> renderings below come from the live transcript; if the agent actually spoke a
> single consistent name and the variation is transcription noise, downgrade or
> remove this item.

In the same successful booking, the assigned provider's name is rendered two
different ways within about forty seconds.

Exchange (`new_patient_paperwork`):

```
[03:17] AGENT: The first openings are on Thursday, July ninth, with
        Dr. Doogie Howser. ...
[03:55] AGENT: Your appointment is set for Thursday, July 9 at 2:15 PM with
        Dr. Duddy Hauser ...
```

**Expected:** a named entity introduced earlier in the call should remain stable
when confirmed later.

**Impact:** the caller cannot be sure who they are scheduled with; in practice
the confirmation contradicts the offer.

### 6. [Medium] Ignores explicitly stated caller intent while stuck on verification

When verification stalls, the agent fixates on it and never addresses the
caller's actual question, even when asked repeatedly.

In `cancel_fee_worried`, the caller asks at least five times whether she will be
charged a late-cancellation fee and how the policy works. The agent repeatedly
defers ("I'll explain the policy as soon as I confirm your chart") and never
answers before the call dead-ends.

```
[02:30] AGENT: I'll share the late cancellation policy right after I confirm
        your chart. Please spell your first and last name ...
```

In `vague_request`, the caller opens with "the thing from last time" and the
agent never asks a single clarifying question about what the visit is for.

**Expected:** the agent should at least acknowledge and, where possible, answer
general policy questions that do not require a verified chart, and should probe
vague requests.

**Impact:** callers leave without the information they called for, even in cases
where verification was not actually necessary to answer.

### 7. [Low] Inconsistent / garbled bilingual recording disclaimer

> Note: the "garbled" rendering may be transcription noise rather than agent
> behavior; the inconsistency in *whether* a Spanish line appears at all is the
> more reliable observation. Confirm against recordings before emphasizing.

The opening recorded disclaimer is inconsistent across calls. Sometimes it
appends a Spanish prompt ("Para español, oprima el dos"), sometimes a Spanish
greeting ("Gracias por llamar Pivot Point Orthopedics"), and sometimes neither.
In `book_brisk` the disclaimer line is garbled, ending in "purposes.endige".

**Expected:** a consistent, cleanly rendered disclaimer on every call.

**Impact:** minor, but it is the caller's first impression and currently varies
call to call.

---

## What worked

Not everything failed, and two calls are worth highlighting as the agent
performing well, which is also the clearest contrast against the systemic bug:

- **`hours_location_calm`** — asked for hours and location, the agent answered
  accurately, consistently, and concisely, and ended cleanly. This is also the
  only task that requires no identity verification, which is consistent with the
  theory that verification is the single point of failure.
- **`insurance_specifics`** — pressed hard on HMO vs PPO, copays, and referrals.
  The agent handled it carefully and correctly: it did not overpromise coverage,
  it accurately described that PPO plans generally allow direct scheduling while
  HMO plans often require a referral, it offered a reasonable self-pay estimate,
  and it routed the caller appropriately. This is the agent at its best.

That these two succeeded while thirteen failed at verification reinforces the
central finding: the agent's conversational and domain reasoning are capable;
the verification flow is what breaks.

## Methodology note

Sixteen scenarios were run, each a unique caller persona and task, placed via an
automated outbound-calling harness that bridges Twilio to a speech-to-speech
model. Each call was recorded and transcribed live. Transcripts of the caller
side ("BOT") are exact; the agent side is transcribed by a separate speech-to-text
model and may contain minor transcription noise, so the audio recordings are the
authoritative record for any agent-side quote. Scenario-to-call-SID mapping and
final call status are in `results/manifest.json`.