# RiffGraph music workbench

RiffGraph runs on `lab-um890` as a CPU-first, offline music-analysis and
software-rendering workbench. It turns an authorized reference audio file into
a structured song graph, MuScriptor MIDI transcription, deterministic
metalcore sketch, and software-instrument preview.

## Deploy

First authenticate to Hugging Face on the Ansible controller and accept the
MuScriptor Small model terms. The role copies the token from
`~/.cache/huggingface/token` to an agent-owned mode-`0600` file on the target;
it never enters Git.

```bash
make riffgraph
```

The role:

- installs FFmpeg, FluidSynth, FluidR3 GM, DrumGizmo, and build dependencies
  with APT;
- builds the checksum-pinned sfizz 1.2.3 offline renderer;
- installs checksum-pinned CC0 guitar, bass, and pad libraries plus the
  CC BY 4.0 CrocellKit 1.1 metal/rock drum kit;
- installs a checksum-pinned `uv`;
- archives the allowlisted `/home/k/code/riffgraph` inputs into a deterministic
  source bundle, verifies its manifest, builds and validates an immutable
  release under `/opt/riffgraph/releases`, then promotes
  `/opt/riffgraph/current` only after its health check passes;
- installs a root-frozen Python 3.12.13 runtime and creates a locked core
  environment inside each release;
- creates an isolated, content-addressed CPU-only MuScriptor 0.2.1 worker and
  couples each release to its matching worker for rollback safety;
- copies the controller token to an agent-owned mode-`0600` cache file;
- installs `/usr/local/bin/riffgraph`;
- runs `riffgraph doctor --json`.

No token or model weight is committed to Git.
Previous immutable releases remain available for a manual symlink rollback.

## Run

```bash
ssh agent@lab-um890
riffgraph doctor
riffgraph run /path/to/authorized-idea.wav \
  --output /opt/riffgraph/projects/my-idea \
  --backend muscriptor \
  --muscriptor-model small \
  --no-separate
```

Render MuScriptor's raw MIDI with the specialized open instruments, without
using the generated arranger:

```bash
riffgraph render-transcription \
  /opt/riffgraph/projects/my-idea/raw/muscriptor/canonical-muscriptor.mid \
  --output /opt/riffgraph/projects/my-idea/preview/raw-open-instruments.mp3
```

The first MuScriptor run downloads the 412 MB Small checkpoint. Use Large only
for a deliberate quality pass:

```bash
riffgraph run /path/to/authorized-idea.wav \
  --output /opt/riffgraph/projects/my-idea-large \
  --backend muscriptor \
  --muscriptor-model large \
  --no-separate
```

Large is about 5.47 GB and will be substantially slower on the CPU-only host.
