# Imagery Art Direction

Output path: `foundations/imagery-art-direction.md`

## Image Role Taxonomy

- Hero: one original subject or abstracted system object, oversized and partially halftoned, with extensive quiet field.
- Product: truthful screenshots or interface crops inside square, unshadowed frames; do not stylize away evidence users need to inspect.
- Editorial: documentary details, hands/tools/screens, or physical infrastructure rendered in high-contrast monochrome.
- Instructional: diagrams and annotated screenshots take priority over photography.
- Avatar: unprocessed monochrome portrait inside a square; provide initials fallback.
- Empty state: labelled path with open endpoint and a concrete next action, not a mascot illustration.
- Texture: generated one-bit dots or restrained grain, always nonsemantic.
- Background: near-solid matte field with optional dim crop or sparse raster residue.

## Subject Guidance

- Show the real object, interface state, person, or working context relevant to the message. Abstract imagery must represent a named concept such as path, transform, or boundary.
- Preserve the decisive evidence: face/hand intent, product state, output, connector, control, or material junction.
- Never crop away the only state indicator, action target, identifying product feature, accessibility cue, or meaningful human expression.
- Prefer close documentary crops, frontal or slight high-angle views, and macro details. Avoid heroic low-angle advertising shots.

## Photography Direction

- Lens feel: neutral 35-60mm documentary perspective; macro crops may feel scanned rather than cinematic.
- Lighting: hard frontal or broad side light with clear black/white separation and little specular glamour.
- Depth of field: moderate-to-deep; evidence remains legible.
- Colour grade: convert to achromatic luminance before thresholding or halftone. Retain a clean original when detail matters.
- Realism: documentary, not synthetic spectacle.
- Imperfections: allow real material texture and controlled raster breakup; remove accidental compression, banding, and unreadable shadows.

## Illustration Direction

- Orthogonal frames, 45-degree transitions, small-radius turns, and circular state nodes.
- Crisp monoline with device-pixel alignment; filled regions use binary values.
- Low detail by default. Add measurement labels only when they explain scale or state.
- Halftone belongs inside bounded fills; grain belongs below the illustration.
- No characters or mascots. Human figures, when required, stay diagrammatic and non-cute.

## Composition And Cropping

- One focal point, placed off-centre on a strong horizontal or vertical axis.
- Reserve 40-70% quiet negative space in hero/editorial contexts.
- Text zones must be solid and texture-free, separated from the focal object by at least 24px.
- Art direction must work at 16:9, 4:3, 1:1, and 9:16 through alternative crops, not stretching.
- Define `object-position` per asset. On mobile, show the decisive evidence first and drop decorative raster residue before cropping the subject.

## Material And Lighting Cues

- Matte, dry, and high-friction surfaces.
- Shadows are graphic separations rather than soft elevation effects.
- Avoid reflection unless it reveals physical material; never add chrome highlights.
- Atmosphere is sparse and cool with no fog, glow, or coloured haze.
- Time of day is irrelevant; light should feel controlled and frontal.

## Generated Asset Prompting

- Positive facts: monochrome editorial frame, JetBrains Mono annotation zone, extreme scale contrast, one bounded one-bit halftone region, matte neutral ground, vast negative space, original path/node geometry.
- Negative constraints: no copied wordmark or emblem, no custom techno font, no neon, gradient, glass, glow, circuit board, rocket, robot, stock cyberpunk, illegible pseudo-data, or texture beneath text.
- References guide palette, density, crop, rhythm, and surface only; they are not compositional templates or assets.
- Vary subject, crop edge, halftone cell size, density state, field inversion, and path configuration while preserving the invariants.
- Reject copied marks, malformed JetBrains Mono, unreadable embedded text, accidental colour, multiple focal points, mushy dots, decorative measurements, or fabricated product details.

## Accessibility And Localization

- Describe the information and purpose of meaningful images; use empty alt for purely atmospheric texture.
- Avoid using culturally specific gestures or symbols as universal protocol meanings; label abstract icons.
- Keep all essential copy as live text. Generated/raster assets may contain no required instructions or data.
- Monochrome still requires sufficient luminance contrast. Preserve alternate non-halftoned media when dots obscure medically, legally, or operationally important detail.

## Translation Rules

- Apply halftone only after selecting the truthful crop and checking that evidence survives thresholding.
- Pair dense media with a quiet text region; pair sparse line art with stronger typographic scale.
- Use original SVG geometry and procedurally generated texture so production does not depend on source assets.

## Anti-Patterns

- Full-bleed stock technology photography, colourful gradients, glowing network globes, generic browser mockups, excessive portraits, fake UI inside generated art, text baked into images, noisy thresholding on every asset, and decorative imagery where a diagram or actual screenshot is required.
