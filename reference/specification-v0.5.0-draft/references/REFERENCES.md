# References

These references inform the draft. External specifications and product documentation are not copied into the normative record model; version-sensitive integration claims should be reverified before release.

## sc-referee companion artifacts

- sc-referee schema package v0.5.0, copied under [`schema-package-v0.5.0/`](schema-package-v0.5.0/).
- Controller invariants in [`schema-package-v0.5.0/CONTROLLER_INVARIANTS.md`](schema-package-v0.5.0/CONTROLLER_INVARIANTS.md).

## Data and schema standards

- JSON Schema specification: <https://json-schema.org/specification>
- W3C PROV Data Model: <https://www.w3.org/TR/prov-dm/>
- RO-Crate 1.3 specification: <https://www.researchobject.org/ro-crate/1.3/>

## Evaluation material

- GeneBench-Pro public package: <https://huggingface.co/datasets/ajh-oai/genebench-pro-public-package>
- GeneBench-Pro introduction: <https://openai.com/index/introducing-genebench-pro/>

The evaluation harness must follow the answer-key isolation requirements in the specification even when the public package includes answer and grader material.

## Claude integration

See [`CLAUDE_CODE_INTEGRATION_NOTES.md`](CLAUDE_CODE_INTEGRATION_NOTES.md) for a dated summary and official documentation links.


## Project identity and implementation foundations


- Existing sc-referee repository: <https://github.com/AlexanderJulianKing/sc-referee>
- Existing sc-referee Claude skill repository: <https://github.com/AlexanderJulianKing/sc-referee-skill>
- sc-referee Claude Life Sciences hackathon gallery entry: <https://cerebralvalley.ai/e/built-with-claude-life-sciences/hackathon/gallery?project=90>
- W3ID persistent identifier service: <https://w3id.org/>
- Apache License 2.0: <https://www.apache.org/licenses/LICENSE-2.0>
- CPython AST documentation: <https://docs.python.org/3/library/ast.html>
- R `getParseData` documentation: <https://stat.ethz.ch/R-manual/R-devel/library/utils/html/getParseData.html>
- Jinja API and autoescaping: <https://jinja.palletsprojects.com/en/stable/api/>
- Docker rootless mode: <https://docs.docker.com/engine/security/rootless/>
- XDG Base Directory specification: <https://specifications.freedesktop.org/basedir-spec/latest/>


## Release-status note

- W3ID registration status for this draft: [`W3ID_REGISTRATION.md`](W3ID_REGISTRATION.md). Local namespace consistency is validated; remote redirect registration remains a release prerequisite.


## Agent adjudication reference configuration

- Anthropic model overview and Claude Opus 5 ID: <https://docs.anthropic.com/en/docs/about-claude/models/overview>
- Anthropic model IDs and versioning: <https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions>
- OpenAI GPT-5.6 introduction: <https://openai.com/index/gpt-5-6/>
- OpenAI GPT-5.6 Sol model documentation: <https://developers.openai.com/api/docs/models/gpt-5.6-sol>
- Local protocol summary: [`AGENT_ADJUDICATION_PROTOCOL.md`](AGENT_ADJUDICATION_PROTOCOL.md)
