# Voice, Tone, And Microcopy

Output path: `foundations/voice-tone-microcopy.md`

## Voice Identity

- Personality: exact, observant, terse, and editorial. It reports what happened without pretending to be a person.
- Authority level: confident about observed state; explicit about unknown, inferred, pending, or failed state.
- Warmth level: cool but not hostile. Courtesy comes from clarity, preservation of work, and useful recovery.
- Formality: professional plain language with technical nouns only when they help the intended reader act.
- Humour boundary: no jokes in controls, errors, waiting states, permissions, or high-consequence flows. Dry wit may appear in nonessential campaign copy only.

## Tone By Context

- Default: concrete noun + active verb + current state. “3 items available.”
- Onboarding: explain one concept at a time, then offer an action. Avoid tours that narrate obvious controls.
- Error: name the failed operation, preserve known-good results, state whether anything changed, and offer one primary recovery.
- Success: name the completed result and durable evidence. Avoid praise, confetti language, or exclamation.
- Warning: name the consequence and when it occurs. Do not use vague “Are you sure?” copy.
- Empty state: distinguish “nothing exists,” “nothing matches,” “not loaded,” and “not permitted”; pair each with a valid next step.
- High-stakes flow: show target, scope, consequence, and reversibility before confirmation; after action, show the receipt or unresolved state.

## Microcopy Grammar

- Prefer direct present-tense verbs: inspect, connect, run, retry, copy, open, remove. Reserve future tense for scheduled behavior.
- Interface sentences target 5-14 words; explanations use short paragraphs and one idea per sentence.
- Labels are nouns or verb phrases without punctuation. Uppercase is reserved for 11-13px metadata labels, not body copy.
- Help text explains constraint, expected format, or consequence. It does not repeat the label.
- Buttons use a specific verb and object: “Run operation,” “Copy result,” “Retry step.” Avoid “OK,” “Submit,” and “Continue” when a clearer action exists.

## Feedback Copy

- Loading: “Running operation · step 2/4” or “Waiting for result · 12 s.” Never invent a percentage.
- Recovery: “Result saved. Processing stopped before details arrived.” Follow with the safest useful action.
- Retry: specify scope—“Retry details,” not “Try again”—and disclose if the action can repeat side effects.
- Confirmation: past tense plus result—“Operation completed · 24 records.”
- Undo: name the reversal and its window—“Item removed. Undo for 10 seconds.”
- Escalation: state what additional permission, input, or external action is needed and why work cannot continue without it.

## Sound And Haptic Language

- Sound is off by default and used only for an opted-in completion or urgent system alert.
- Haptics may confirm direct manipulation on supported devices; never encode unique meaning.
- Routine navigation, hover, loading, and success remain silent.
- Every sound/haptic event has simultaneous visible text and geometry; motion is never the sole carrier of state.

## Localization

- Avoid idioms, slang, metaphors of magic, and culturally specific humour in functional copy.
- Reserve 35% horizontal expansion for labels and 100% for short buttons; do not rely on fixed character counts despite the monospace grid.
- Avoid hostile command language, anthropomorphism, ableist metaphors, and false certainty.
- Prefer common words, define necessary domain terms at first use, and keep codes/identifiers copyable separately from explanations.

## Translation Rules

- Treat state copy as evidence: distinguish prepared, running, completed, partially completed, blocked, and unknown.
- Pair every error with scope and recovery; pair every irreversible action with consequence before it runs.
- Use numerals, timestamps, record identifiers, and measurements only when they are real and useful.

## Anti-Patterns

- Fake terminal jargon, lorem-code, chatbot pleasantries, motivational praise, vague errors, blame, hidden side effects, “successfully” without a result, emoji status, excessive uppercase, humorous destructive confirmations, and ornamental coordinates or metrics.
