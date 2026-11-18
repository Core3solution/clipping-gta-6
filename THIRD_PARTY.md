# Third-party code and techniques

## Editonny (MIT)

`clipper/render.py` `fx_filter(..., zoom_engine="perspective")` adapts the sub-pixel camera crop technique of
Editonny's `engine/helpers/compose_final.py` (`camera_filter`, FFmpeg `perspective` filter with cubic interpolation).

```
MIT License

Copyright (c) 2026 Matheus Gomes

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## Superpowers (MIT) — `.claude/skills/` (14 skills)

Copyright (c) 2025 Jesse Vincent. Vendored at commit 22f0b46 of https://github.com/obra/superpowers by
`scripts/devkit/sync-skills.sh`; each skill folder carries `LICENSE.superpowers`. Only change: the plugin namespace
`superpowers:` is removed from skill references (project skills have plain names).

## Ponytail (MIT) — `.claude/skills/ponytail*` (5 skills)

Copyright (c) 2026 DietrichGebert. Vendored at commit 96608e0 of https://github.com/DietrichGebert/ponytail;
each skill folder carries `LICENSE.ponytail`. The plugin's Node hooks are not included.

## Agentville (Apache-2.0) — ideas only

`.claude/hooks/guard.py`, `verify_on_stop.py` and the agents in `.claude/agents/` are new Python/Markdown code written
for this project, inspired by agentville's secret-scan, guard-main-branch, verify-on-stop hooks and its
code-reviewer/debugger/explorer agents (https://github.com/soumatheusgomes/agentville). No agentville file is copied.
