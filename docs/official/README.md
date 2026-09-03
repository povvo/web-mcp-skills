# Official material snapshots

This directory preserves the official material supplied with the project. The files under `snapshots/` are source evidence, not the repository’s public tutorial. They remain editorially unchanged so their provenance is inspectable; the deadpan, task-oriented synthesis lives in the parent documentation.

## Snapshot ledger

| Snapshot | Canonical source | SHA-256 |
| --- | --- | --- |
| `web-mcp.md` | [WebMCP explainer / upstream README](https://github.com/webmachinelearning/webmcp/blob/main/README.md) | `6502112d59a47da0b55f267c5e62ffe6d2238e3b948d80bcee78b0fbc5c8eea7` |
| `web-mcp-spec.md` | [WebMCP draft specification](https://webmachinelearning.github.io/webmcp/) | `b84275deb4a47fb19989cfe821dda67e6322ad4bc261cf5f50043d8951efa9fa` |
| `implementation-status.md` | [Browser and agent implementation status](https://github.com/webmachinelearning/webmcp/blob/main/implementation-status.md) | `41956527ccd39a4dad7751a652988777c1f7050b3f9a2a20c47c5d735625250f` |
| `declarative-api-explainer.md` | [Declarative API explainer](https://github.com/webmachinelearning/webmcp/blob/main/declarative-api-explainer.md) | `adc121fff82e357471e9eb578fdd6427204eb03f475ec43cdf6bce21f0fa436c` |
| `service-workers.md` | [Service Worker explainer](https://github.com/webmachinelearning/webmcp/blob/main/docs/service-workers.md) | `f56085fecc1b01a8ece4da1845785b66e7ce29c4ea7016f5d21a181fa5a7191a` |
| `security-privacy-questionnaire.md` | [Security and privacy questionnaire](https://github.com/webmachinelearning/webmcp/blob/main/security-privacy-questionnaire.md) | `33907b97fc85fe2277f47eca8f72f5c0522b0444ebfd2be9b65b0110c475a247` |
| `site-tools.md` | [OpenAI Site tools documentation](https://help.openai.com/en/articles/20001423-using-site-tools-in-the-chatgpt-desktop-app) | `6935d7e39c25d19c931335960fb7a66d52e265f92cf31d07a6f72c8b5f7e5798` |

Five GitHub-hosted snapshots—`web-mcp.md`, `implementation-status.md`, `declarative-api-explainer.md`, `service-workers.md`, and `security-privacy-questionnaire.md`—were verified as text-identical after line-ending normalization to upstream commit `41d12f057167ccf5954dbcf49d99502cb6c84491`, checked on 31 August 2026.

## Licensing

The five snapshots copied from `webmachinelearning/webmcp` retain the upstream [W3C Software and Document License](W3C-SOFTWARE-AND-DOCUMENT-LICENSE.md). The OpenAI Site tools snapshot is not covered by this repository's project license; its canonical source and rights holder remain identified above. Repository-wide attribution is collected in [Third-party notices](../third-party-notices.md). Apparently provenance also has dependencies.

## Drift note

On 3 September 2026, upstream `main` resolved to `55fb7ee2289679fbbbf3b1f8fc2f92daf96e6ba9`, and the npm registry reported `webmcp-types` `0.1.6`. The living sources have changed since these snapshots. Use the canonical links for current implementation decisions; use the snapshots to inspect what informed this skill release.

The snapshot manifest does not claim that every proposal described in an official file is implemented by every production host. Provenance answers “where did this come from?” Maturity answers “what works here?” They remain separate questions despite sharing a table.
