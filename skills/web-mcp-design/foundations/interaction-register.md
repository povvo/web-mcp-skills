# Interaction Register

Output path: `foundations/interaction-register.md`

## Ambient Atmosphere

- Persistent background state: stable, quiet, and visibly ready rather than animated or conversational.
- Visual equivalent: a matte field, one clear reading axis, restrained labels, and inactive open nodes waiting on a path.
- Sound and haptics are absent by default. If a host platform provides them, use one light confirmation tick for completed direct manipulation and never loop sound for processing.
- Before interaction the interface feels watchful, exact, and under control; it does not solicit attention with ambient movement.

## Percussive Events

| Event type | Feedback character | Visual form | Haptic/sound equivalent |
| --- | --- | --- | --- |
| Hover | quiet | one-pixel rule strengthens or label brightens | none |
| Keyboard focus | explicit | two-pixel offset path or rectangular outline plus visible label | none |
| Press | sharp | node closes or region inverts for 80-120ms | optional light tick |
| Processing | measured | labelled route with current node and determinate value when known | none |
| Success | decisive | destination node closes; concise result label remains | optional success tick if host conventions require |
| Error | persistent | double rule or diagonal hatch with error label and recovery action | optional alert sound only under user preference/system convention |

## Feedback Density

- Maximum response per action: one local geometry change, one state label, and one optional motion path. Avoid simultaneous toast, modal, colour shift, and sound.
- Minimum response per action: immediate pressed/focus state and a final semantic state exposed to assistive technology.
- Withhold redundant celebration after low-risk reversible actions and suppress hover feedback on touch-only devices.
- Be explicit for loading beyond 300ms, validation failure, permission denial, destructive consequences, external side effects, partial completion, and recovery availability.

## Silence

- Remove decorative success animation, ambient cursor effects, and repeated “still working” chatter.
- Silence means stable completion or no change; it must never stand in for an unknown operation state.
- Prevent the interface from seeming broken with a pressed state under 100ms, a processing label by 300ms, and time/progress detail when the operation exceeds two seconds.

## Trust Construction

- Show the current state and primary next action first; expose raw operation details, timings, and logs through an inspect action.
- Keep labels aligned and state geometry stable across retries so changes are attributable.
- Preserve entered data after validation failure, offer retry/resume where safe, and name what completed versus what did not.
- Escalate from inline label to bounded status field to modal confirmation only as consequence or interruption increases.

## State Semantics

| State | Interaction meaning | Visual behavior | Copy behavior |
| --- | --- | --- | --- |
| Default | available, no action underway | open node, one-pixel boundary, normal ink | concrete verb or noun |
| Hover/focus | candidate / keyboard destination | hover brightens; focus adds independent two-pixel outline or path | label remains stable; optional shortcut appears |
| Active/pressed | input accepted locally | node closes or compact region inverts | verb does not change prematurely |
| Loading | operation underway | current path segment visible; value or bounded step advances | present tense plus exact step or percentage when known |
| Error | intended result not reached | persistent double rule or hatch; focus moves only when necessary | state what failed and provide a specific recovery action |
| Success | result reached | destination node closes and path becomes stable | name the completed result; avoid praise or exclamation |

## Temporal Phase

- First use includes short labels and one visible explanation of the path/node grammar.
- Repeated use compresses help but preserves state names and keyboard discoverability.
- High-stakes actions use explicit consequence copy, review data, and a recoverable confirmation step proportional to risk.
- End states settle into stillness and leave a durable result, timestamp, identifier, or next action rather than disappearing immediately.

## Anti-Patterns

- Confetti, bouncing confirmation, conversational filler, unexplained silence, transient error-only toasts, colour-only states, focus removal, optimistic success before receipt, looping spinners without labels, modal use for routine feedback, or fake progress.
