# Robot-Q Memory Policy

## Purpose

Robot-Q should remember information that helps it understand people, maintain continuity across conversations, support ongoing tasks, and behave more like a persistent companion.

Memory should not be treated as a raw transcript of everything that happens.

Robot-Q should distinguish between:

- long-term personal memory
- medium-term contextual memory
- current state
- information that should be ignored

A memory does not need to remain true forever in order to be useful.

If a stored fact later changes, Robot-Q should update or supersede the old memory rather than assuming the old fact is permanently true.

---

# Memory Classes

## Long-Term Memory

Long-term memory is information that is likely to remain useful across future conversations.

Long-term does **not** mean permanent.

These facts may change later and should be updated when new information becomes available.

### Examples

- relationships
- family members
- important people
- identity information
- hobbies
- interests
- preferences
- dislikes
- education
- occupation
- pets
- important possessions
- important projects
- recurring routines
- important locations
- personal goals
- facts about the person's relationship with Robot-Q

### Example statements

User says:

> My girlfriend is Shelby.

Memory:

> Shelby is Camille's girlfriend.

User says:

> I really like physics.

Memory:

> Camille likes physics.

User says:

> I have two cats.

Memory:

> Camille has two cats.

User says:

> I built Robot-Q.

Memory:

> Camille built Robot-Q.

---

## Medium-Term Memory

Medium-term memory is information that is useful for an ongoing period, project, situation, or goal but may stop being useful once that situation ends.

### Examples

- current school semester
- current classes
- active job applications
- an ongoing interview process
- current travel plans
- active troubleshooting problems
- a robot subsystem currently being built
- an ongoing purchase decision
- a temporary project goal
- a current deadline
- an unresolved task

### Example statements

User says:

> I'm currently troubleshooting the ESP32 motor controller.

Memory:

> Camille is currently troubleshooting Robot-Q's ESP32 motor controller.

User says:

> I have an interview with PSI next week.

Memory:

> Camille has an upcoming PSI interview.

---

## Current State

Current-state information describes what is happening right now and usually should not become persistent memory.

It may still be useful to Robot-Q temporarily while deciding what to do.

### Examples

- tired right now
- hungry right now
- currently standing in a room
- currently watching television
- current battery level
- currently talking to someone
- current motor direction
- current sensor state
- current weather
- current activity

### Example statements

User says:

> I'm tired right now.

Classification:

> CURRENT_STATE

User says:

> I'm standing in the kitchen.

Classification:

> CURRENT_STATE

---

## Ignore

Some information has little or no memory value.

### Examples

- greetings
- thanks
- conversational filler
- meaningless repetition
- accidental text
- ordinary questions with no personal information
- information already stored with the same meaning

### Example statements

User says:

> Hi Q.

Classification:

> IGNORE

User says:

> Thanks.

Classification:

> IGNORE

---

# Important Memory Rules

## 1. Long-Term Does Not Mean Permanent

Relationships, jobs, preferences, hobbies, addresses, pets, and other useful facts can change.

A fact can still belong in long-term memory if it would help Robot-Q in future conversations.

---

## 2. Use Explicit Names

Stored memories should make sense without the original conversation.

Avoid ambiguous pronouns.

Bad:

> I built you.

Good:

> Camille built Robot-Q.

Bad:

> My girlfriend is Shelby.

Good:

> Shelby is Camille's girlfriend.

---

## 3. Prefer Standalone Facts

Each memory should be understandable by itself.

Bad:

> She likes it.

Good:

> Camille likes physics.

---

## 4. Do Not Store Robot-Q's Reply as User Memory

The memory system should primarily extract facts stated or clearly established by the human.

Robot-Q's generated response should not automatically become a fact about the human.

---

## 5. Do Not Invent Missing Information

Only store information supported by the conversation.

If Robot-Q is uncertain, it should avoid storing the fact or classify it for later review.

---

## 6. Avoid Duplicate Memories

If a new candidate memory has essentially the same meaning as an existing memory, it should not create another identical record.

Example:

Existing:

> Shelby is Camille's girlfriend.

Candidate:

> Camille's girlfriend is Shelby.

These should be treated as the same underlying fact.

---

## 7. Update Changed Facts

If a new fact clearly replaces an older fact, the memory system should eventually update or supersede the old value.

Example:

Old:

> Camille's favorite color is purple.

New:

> Camille's favorite color is green.

The system should not treat both as simultaneously current facts.

---

# Memory Pipeline

```text
Conversation
    ↓
Fact extraction
    ↓
Canonical third-person facts
    ↓
Memory classification
    ↓
LONG_TERM / MEDIUM_TERM / CURRENT_STATE / IGNORE
    ↓
Validation
    ↓
Duplicate / update check
    ↓
SQLite