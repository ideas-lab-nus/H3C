# Tracked fixtures

Golden inputs and outputs used by equivalence gates live here. Runtime-generated
artifacts never enter this directory.

`oracle_equivalence.json` freezes Prompt bytes and semantic results extracted
from the read-only production owners at the recorded source commit: the program
interpreter, accepted update replay, whole-program direction proof, energy
budget, ordered action assurance, weather summaries, three-case mapping,
physical actions, occupancy, objectives, and KPI accumulation. The hydronic
occupancy configuration additionally records the later, explicitly authorized
missing-value resolution policy; its ordinary finite-value behavior remains
covered by the historical oracle. Tests consume the fixture through the new
production paths; they do not import the historical tree.

`overlong_rationale_replay.json` contains all eleven final-source `8a58a84`
release-smoke Orchestrator/Executor raw outputs whose parsed rationale exceeded
240 characters. The oracle records its exact SHA-256. Production replay tests
prove that the new contract preserves each raw and parsed rationale in full and
does not reinterpret the immutable old run classifications.

`prompts/*_old.txt` contains the exact dynamic user bytes emitted by the
read-only final cooling production builders for one representative retained
input per role. `prompts/representative_input.json` is the single frozen input
owner. `prompts/provenance.json` records the oracle commit, exact legacy source
paths and Git-blob hashes, representative-input identity, and fixture hashes.
Default standalone tests validate all tracked identities and independently
render the same semantic input through H3C owners. Migration auditors may run
the zero-API oracle verifier with an explicit read-only legacy-repository path;
it renders directly from a temporary snapshot of the recorded commit.

`offline_prompts/` contains the representative approved Mapping and causal
proposal inputs plus byte/SHA-256 identities for initial and human-revision
renders of both offline roles. These fixtures cover the new current-schema
Prompt owners; they do not regenerate any existing confirmed graph.
