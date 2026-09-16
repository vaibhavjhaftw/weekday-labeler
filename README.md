# Weekday Labeler

Mark where each set starts and stops in a gym session video. It runs as a web
page, so a new labeller needs a link and nothing else installed.

The video is **not** part of the page. It is opened from the labeller's own
disk, the way a desktop player opens a file — never uploaded, never streamed.
That is what keeps seeking frame-accurate, and it is what keeps participant
footage off third-party servers.

---

## For whoever is labelling

1. Open the link. Type your name once.
2. On the setup screen, pick the session and point it at the video. Both are
   remembered, so a reload drops you straight back in.
3. For each set, mark four moments with <kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd> <kbd>4</kbd>:

   | | |
   |---|---|
   | **1 — Exercise starts** | they walk up / pick up the weight |
   | **2 — First rep** | the first rep begins |
   | **3 — Last rep** | the last rep finishes |
   | **4 — Exercise ends** | they rack it / walk away |

4. After the fourth mark a **review card** pops up with a picture of all four
   moments. Click any picture to jump back and look again. If it looks right,
   **Save & next** — it moves to the next set on its own.
5. When all 25 are done, open **Check**, then **Export**.

You never type an exercise name or RPE — those come from the trainer's set log
and are filled in already. Your job is *when*, plus confirming the rep count if
it differs from what was logged.

### Keys

| | |
|---|---|
| <kbd>1</kbd><kbd>2</kbd><kbd>3</kbd><kbd>4</kbd> | mark the four moments |
| <kbd>space</kbd> | play / pause |
| <kbd>←</kbd> <kbd>→</kbd> | 10 seconds · with <kbd>⇧</kbd>, 1 second |
| <kbd>,</kbd> <kbd>.</kbd> | one frame — use these to land a boundary exactly |
| <kbd>J</kbd> <kbd>K</kbd> <kbd>L</kbd> | slower · normal · faster |
| <kbd>⏎</kbd> | review the set · <kbd>⌫</kbd> undo the last mark |

Pressing a step you already marked re-takes it at the current frame. That is how
you fix a mistake; there is no separate edit mode.

Work is saved in your browser as you go, so closing the tab loses nothing. It is
saved **per browser** — your marks are not visible to anyone else until you
Export and send the file.

### Nothing is lost if you close the tab

Every mark is written to this browser the instant you make it — the small
**saved** flash next to the counter is that happening. Close the tab, reload,
crash, come back tomorrow: the session picker shows how many sets you had done
and you carry on from the next one. Marks are kept per session, so switching
video or session never throws any away. The only thing that deletes them is the
**Clear this session's marks** button, which asks first.

The bottom-right **Switch video or session** button goes back to the setup
screen. It tells you exactly what it will and will not touch before it does.

### Three ways to reach the video

| | file on your machine | direct web link | YouTube |
|---|---|---|---|
| seek accuracy (paused) | exact | exact | exact |
| frame stepping | yes | yes | yes |
| still previews | yes | yes, if the host allows it | no — jump instead |
| labeller downloads anything | yes | no | no |

A **direct web link** to an `.mp4` is the best of both: nothing to download and
the stills still work. Two things the host must do —

- **byte ranges.** Without them the video cannot be seeked at all; it rewinds to
  whatever is buffered. The app checks and says so plainly. S3, R2 and B2 all do
  ranges; `python3 -m http.server` does not, which is why `serve.py` is here.
- **`Access-Control-Allow-Origin`.** Without it the video plays and seeks fine
  but the stills are gone, and you get jump buttons as on YouTube.

Cloudflare R2 is the easy answer: ranges and CORS out of the box, 10 GB free,
and no charge for bandwidth.

For YouTube, timings come out just as exact — measured, not assumed. The one
loss is the stills, because it will not let a page read its pixels.

If a re-upload was trimmed at the front, every mark shifts by the same amount —
the **nudge** box next to the video corrects it in one number.

### The three tabs

- **Label** — the video, the current set, the four marks.
- **Check** — every set as a row of four pictures. Click any picture to see that
  moment. Sets with a problem say what is wrong: reps falling outside the
  exercise, two sets overlapping, a set only a few seconds long.
- **Signals** — the wrist sensor traces, for whoever is checking the work. A
  real set is obvious in the accelerometer; this is how you confirm a boundary
  when the video is ambiguous. It can also draw a delivered pass over yours to
  compare.

---

## Where the exercise, reps and RPE come from

They are **not** guessed and interns do not type them. They come from the
trainer's set log, which you load on the setup screen under **New session from a
set log**. That builds the whole 25-set plan in the browser — no Python, no
rebuild, nothing for a labeller to install. `set_log_template.csv` is the
format:

```
session_id,exercise,set_index,set_role,reps_counted,rpe,load,assistance,laterality,variation,notes
guru_20260831_1552,pull_ups,1,warm_up,10,4,body only,assisted,bilateral,,
```

The split is deliberate:

- **RPE cannot be labelled from video.** It is how hard the set *felt*, reported
  by the participant at the time. Nobody watching a recording can recover it, so
  it has to be captured in the gym.
- **Load, assistance and variation** are the same — visible sometimes, reliable
  only from the log.
- **Rep count can be checked from video**, so the review card shows the logged
  number in an editable field. Change it and Check flags the disagreement rather
  than silently overwriting; both numbers reach the export, which is what Fort's
  rep reconciliation compares.

One row per set, filled at capture time. `bake.py` turns it into the 25-set plan
the app walks through.

## Running it

**Live at https://weekday-fort-labeler.vercel.app** — that is the link to send.

Redeploy after any change:

```bash
vercel deploy --prod
```

`vercel.json` sets the headers that matter: the page itself must-revalidates, so
a labeller always gets the current version without being told to hard-refresh,
while `data/` keeps an hour of cache since it is the heavy part and rarely
changes. Range and allow-origin are on for the whole site, so a video parked
next to the app works as a **Web link** source.

`vercel git connect` makes every push to main deploy on its own.

**Hosted anywhere else** — any static host, nothing to build. For GitHub Pages:

```bash
cd fort-labeler-web
gh repo create <org>/weekday-labeler --private --source=. --push
gh api -X POST repos/<org>/weekday-labeler/pages -f 'source[branch]=main' -f 'source[path]=/'
```

A private repo means Pages is visible to repo collaborators only, which is the
right default for study data. A public repo would put one participant's set
timings and RPEs on the open web — Fort's call, not ours.

**On one Mac, no hosting** — double-click `start-labeler.command`. It serves the
folder and opens the browser. macOS already has the Python it uses; there is
nothing to install.

Opening `index.html` by double-clicking it does *not* work — browsers block a
local page from reading the data files next to it. It has to be served.

### Giving labellers the video

**YouTube** is the least friction: upload once, paste the link. Unlisted works;
private and embedding-disabled do not. Upload at the native 1080p60 so the frame
rate matches what the keyboard steps assume.

**Or a local copy.**

Each labeller needs the file locally. The original is 13 GB of HEVC; a 720p
H.264 proxy of the same recording is about 1.7 GB, plays far more smoothly, and
labels identically — the app checks **duration**, not file size, so a proxy is
accepted and a different recording is not.

```bash
ffmpeg -i session.MP4 -vf scale=-2:720 -c:v libx264 -crf 23 -preset fast \
       -c:a aac -movflags +faststart session-720p.mp4
```

Send it the way the study agreement allows. Not a personal cloud drive.

---

## Getting labels back into Fort's format

The browser cannot write parquet, so the app exports the same working-draft JSON
the local tool keeps:

```bash
python3 import_to_fort.py ~/Downloads/guru_20260831_1552__Priya__labels.json
```

That drops it in as the local tool's working state. Open `fort-annotator-demo`,
enter the same labeler id, and press **Export revision** — the code already
checked against Fort's own fixture writes `ground_truth.parquet` and the
manifests.

---

## What ships in `data/`

| file | what |
|---|---|
| `session.json` | the 25-set plan from the trainer's log, plus the exercise catalog |
| `overview.json` | \|accel\| envelope, 3000 buckets |
| `imu.bin` | 6 channels × 2 wrists, Int16, 50 Hz — 3.3 MB |
| `imu.json` | scales, layout, sample count |
| `labels/*.json` | the two delivered passes, for comparison |

`set_log_template.csv` is the trainer's sheet for a new session.

`imu.bin` is a **render copy**, never a label source. The capture itself is
544,264 rows at ~100 Hz in `samples.parquet`; this is resampled so a browser can
hold the session in memory and draw any window without a server round trip.

Session seconds are `corrected_timestamp_s − 1000.0`. Video maps on as
`session = video + (−0.582)`, measured from the sync clap. Rebuild everything
with `bake.py` after re-running `fort_capture_package.py`.
