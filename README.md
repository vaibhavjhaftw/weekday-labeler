# Fort Session Labeler — web

The labeler as a plain web page. Nothing runs on a server: the page loads the
session's sensor data and the delivered label sets as static files, and the
**video is opened from the viewer's own disk**.

That split is deliberate.

- **The page can be public.** Timeline, IMU traces, every labelled interval,
  both labeller passes — all of it is a few hundred kB of numbers.
- **The recording never leaves the machine.** It is opened with
  `URL.createObjectURL`, the same way a desktop player opens a file. No upload,
  no copy, nothing cached by a third party. Fort's instructions are explicit:
  *"Do not upload captures or labels to an unapproved cloud drive, messaging
  service, or personal account."* This design does not touch that line.
- **Seeking stays frame-accurate.** A local file seeks in single frames, which
  a YouTube or Vimeo embed cannot do — their players snap to keyframes, roughly
  half a second out. Boundaries here are graded to ±150 ms, so a streamed
  player would put the target out of reach.

Someone without the MP4 still gets a working page — traces, intervals, rep
counts, RPE. Only the frame previews need the file.

## Hosting it

Any static host. For GitHub Pages:

```bash
cd fort-labeler-web
git init && git add -A && git commit -m "Fort session labeler (web)"
gh repo create <org>/fort-labeler-web --private --source=. --push
gh api -X POST repos/<org>/fort-labeler-web/pages -f 'source[branch]=main' -f 'source[path]=/'
```

Private repo → Pages is visible to repo collaborators only, which is the right
default for study data. A public repo would publish the label timings and RPEs
to anyone; that is a call for Fort to make, not us.

Nothing to build. `index.html` plus `data/` is the whole site.

## Using it

1. Open the URL.
2. **Load video…** and pick `Video_Guru_31_08_2026.MP4` from your own disk.
   The page checks the file size against the labelled capture and says so if it
   does not match. Chrome and Edge remember the file across reloads; Safari and
   Firefox ask again each session.
3. Pick a label set in the header. The two delivered passes are **read-only**.
   *My labels* is yours, stored in this browser only.
4. **Copy into my labels** starts a new pass from an existing one.
5. **Export JSON** downloads a `working_draft.v2` file — the shape `server.py`
   in `fort-annotator-demo` reads, which is what writes Fort's parquet.

### Keys

`space` play · `←` `→` 10 s · `⇧`+arrow 1 s · `,` `.` one frame ·
`J` `K` `L` speed · `I` mark in · `O` mark out · `R` tap rep · `E` end reps ·
`Esc` clear.

### Annotated moments

Every exercise interval gets a card with a real frame from the moment its first
rep starts. Click the card to jump there; `in` / `rep 1` / `rep n` / `out` seek
to that exact boundary. Hovering either timeline shows the frame under the
cursor. The card for the interval you are inside highlights as the video plays.

## The data

| file | what |
|---|---|
| `data/session.json` | exercise catalog, movement patterns, operator set log |
| `data/overview.json` | \|accel\| min/max envelope, 3000 buckets |
| `data/imu.bin` | 6 channels × 2 wrists, Int16, 50 Hz — 3.3 MB |
| `data/imu.json` | header: scales, layout, sample count |
| `data/labels/*.json` | the two delivered annotation sets |

`imu.bin` is a render copy, not the capture. The capture is 544,264 rows at
~100 Hz in `samples.parquet`; this is resampled to 50 Hz and quantised to Int16
purely so a browser can hold the session in memory and draw any window without
a round trip. Labels are never derived from it — every boundary in
`data/labels/` was marked against the video.

Session seconds are `corrected_timestamp_s − 1000.0`. Video maps on as
`session = video + (−0.582)`, measured from the sync clap.

Rebuild the data with `bake.py` after re-running `fort_capture_package.py`.
