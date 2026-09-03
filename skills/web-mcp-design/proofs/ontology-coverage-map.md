# Ontology Coverage Map

Output path: `proofs/ontology-coverage-map.md`

## Coverage Map

| Layer | Status | Source IDs | Output file | Missing or weak areas |
| --- | --- | --- | --- | --- |
| Foundations | supported | R01-R04, B01 | `foundations/*.md` | Motion, interaction, sound, haptics, and product microcopy are inferred because the corpus is static. |
| Tokens | supported translation | R01-R04, B01 | `tokens/*.md` | Exact source measurements are not design tokens; responsive and platform values require implementation testing. |
| Components | reconstructed | R01-R04 | `components/*.md` | No source UI components exist. Contracts translate the visual grammar into common controls without claiming direct evidence. |
| Patterns | reconstructed | R01-R04 | `patterns/*.md` | Behavioral states and platform patterns are inferred; perceptual patterns have the strongest source support. |
| Accessibility | required extension | R01-R04 | `accessibility/*.md` | No accessibility behavior is depicted. Contrast, keyboard, text alternatives, zoom, and reduced motion are explicit production requirements. |
| Applications | supported translation | R01-R04, B01 | `applications/application-rules.md` | Web MCP affects naming only; specific product screens and content architecture remain open. |
| Outputs | supported | R01-R04, B01 | `outputs/*.md` | Generated output needs human visual review; no source assets are packaged. |
| Proofs | supported | R01-R04, B01 | `proofs/*.md` | Static evidence can validate reconstruction rules but not live performance, browser rendering, or interaction quality. |
| Handoff | supported | R01-R04, B01 | `handoff/*.md` | Rights are limited to reference/analysis. Trademark, font delivery, and production asset custody are not established here. |

## Coverage Reading

“Supported” means the source directly or repeatedly establishes the visual rule. “Supported translation” means the source establishes a principle and the package makes it operational. “Reconstructed” means the source does not depict the layer, so the package derives a compatible implementation contract and labels the evidence gap. The package is complete as a design language when all layers are usable, not when all layers are falsely described as observed.
