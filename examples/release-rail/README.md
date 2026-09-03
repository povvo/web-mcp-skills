# Release Rail

Release Rail demonstrates ordered state transitions. The visible buttons and the WebMCP `advance_release_step` and `reopen_release_step` tools call the same revision-checked operations. `inspect_release_rail` returns the complete path.

The state is sample data and is labelled as such in the interface. Run from `examples/` with `npm start`; test with `npm test`.

Regenerate the WebMCP adapter from this directory with:

```powershell
python -B ../../skills/web-mcp/scripts/webmcp_toolkit.py compile-product product.json --target vanilla-js --output-dir . --write --force
```
