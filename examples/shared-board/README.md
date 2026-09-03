# Shared Board

Shared Board demonstrates a revision-protected local write. The visible form and the WebMCP `add_board_item` tool both call `addBoardItem`; `inspect_board` reads the same store.

Run all examples from the parent directory with `npm start`, then open `/shared-board/`. Run the domain tests with `npm test`.

The generated adapter is `src/webmcp-tools.js`. Regenerate it from this directory with:

```powershell
python -B ../../skills/web-mcp/scripts/webmcp_toolkit.py compile-product product.json --target vanilla-js --output-dir . --write --force
```
