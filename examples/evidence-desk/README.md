# Evidence Desk

Evidence Desk demonstrates selected state and evidence-preserving annotation. Human controls and WebMCP tools call the same operations. Selection and annotation never alter a record's `observed`, `prepared`, or `blocked` state.

The records are sample data and are labelled as such in the interface. Run from `examples/` with `npm start`; test with `npm test`.

Regenerate the WebMCP adapter from this directory with:

```powershell
python -B ../../skills/web-mcp/scripts/webmcp_toolkit.py compile-product product.json --target vanilla-js --output-dir . --write --force
```
