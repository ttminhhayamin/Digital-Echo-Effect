# Digital Echo Effect: Project Report

**Course:** Digital Signal Processing (DGT302)
**Author:** [Student name] · [Student ID]
**Instructor:** [Instructor name]

This document describes everything about the project in one place: the problem, the math,
the implementation, the demo application, the verification results, the presentation, and
the questions an examiner is likely to ask. For a short introduction see [README.md](README.md).

---

## Contents

1. [Overview](#1-overview)
2. [Background](#2-background)
3. [Mathematical models](#3-mathematical-models)
4. [Comparison of the three models](#4-comparison-of-the-three-models)
5. [Implementation](#5-implementation)
6. [The demo application](#6-the-demo-application)
7. [Verification and results](#7-verification-and-results)
8. [Course concepts used](#8-course-concepts-used)
9. [Presentation slides](#9-presentation-slides)
10. [Five-minute demo script](#10-five-minute-demo-script)
11. [Questions an examiner may ask](#11-questions-an-examiner-may-ask)
12. [Limitations and future work](#12-limitations-and-future-work)
13. [Project files and reproduction](#13-project-files-and-reproduction)
14. [References](#14-references)

---

## 1. Overview

**Goal.** Build a digital echo effect and show, with sound and with plots, that echo is a
discrete-time LTI system that can be analysed in the time domain, the z-domain and the
frequency domain.

**What was built.**

- A DSP core (`echo_dsp.py`) with three echo models: one echo (FIR), N echoes (FIR) and
  infinitely repeating echo (IIR with feedback).
- An interactive web application (`app.py`, Streamlit) to hear the effect and analyse the
  system.
- A command-line fallback (`demo_cli.py`) that needs no browser and also generates the
  figures used in the slides.
- A 14-slide presentation with speaker notes.

**Key results.**

- All implementations agree with `scipy.signal.lfilter` to about 1e-16 (floating-point rounding).
- The IIR model produces unlimited echoes at the cost of a single multiplier and one delay
  line, but it is stable only when the absolute value of α is below 1. The app demonstrates
  the instability directly.
- The echo's frequency response is a **comb filter** whose teeth are spaced Fs/D Hz apart.
  This is visible in the FFT of real audio.

---

## 2. Background

### 2.1 What an echo is

An echo is a reflected copy of a sound that reaches the listener later than the original
and weaker than the original. Two parameters describe it:

- **Delay τ**: the extra travel time. For a reflecting wall at distance d and speed of sound
  c, the sound travels there and back, so τ = 2d / c. For d = 51 m and c = 343 m/s,
  τ ≈ 0.30 s.
- **Attenuation α**: the reflection loses energy, so the copy is scaled by a factor with
  |α| < 1.

The ear separates an echo from the original once τ is roughly 50 ms or more. With shorter
delays the copy blends into the original and is heard as coloration or reverberation
(this is the comb-filter effect in Section 3.4).

### 2.2 From continuous time to discrete time

Audio is sampled at Fs. A delay of τ seconds becomes a shift of

$$D = \operatorname{round}(\tau \cdot F_s)$$

samples, so x(t − τ) becomes x[n − D]. Example used throughout: Fs = 22 050 Hz and
τ = 300 ms give **D = 6 615 samples**. The delay resolution is 1/Fs ≈ 45 µs, which is far
below what the ear can distinguish. This step relies on the sampling theory of Chapter 6.

---

## 3. Mathematical models

Notation: D is the delay in samples, α the attenuation factor, N the number of echoes,
and z⁻ᴰ the delay of D samples. All systems start from rest (zero initial state) and are
causal.

### 3.1 Model 1: one echo (FIR)

$$y[n] = x[n] + \alpha\,x[n-D]$$

| Property | Value |
|---|---|
| Transfer function | $H(z) = 1 + \alpha z^{-D}$ |
| Impulse response | $h[n] = \delta[n] + \alpha\,\delta[n-D]$ |
| Poles | D poles at z = 0 |
| Zeros | D zeros with $z^D = -\alpha$, i.e. on the circle $\lvert z\rvert = \lvert\alpha\rvert^{1/D}$ |
| Frequency response | $H(e^{j\omega}) = 1 + \alpha e^{-j\omega D}$ |
| Magnitude squared | $\lvert H\rvert^2 = 1 + \alpha^2 + 2\alpha\cos(\omega D)$ |
| Magnitude range | between $1-\lvert\alpha\rvert$ and $1+\lvert\alpha\rvert$ |
| Stability | always BIBO stable: $\sum\lvert h[n]\rvert = 1+\lvert\alpha\rvert<\infty$ |

For α > 0 the peaks are at ω = 2πk/D and the notches at ω = (2k+1)π/D. For α < 0 the
echo is phase-inverted and the peaks and notches swap places.

### 3.2 Model 2: N echoes (FIR)

$$y[n] = \sum_{k=0}^{N}\alpha^{k}\,x[n-kD]$$

| Property | Value |
|---|---|
| Transfer function | $H(z)=\sum_{k=0}^{N}\alpha^k z^{-kD}=\dfrac{1-(\alpha z^{-D})^{N+1}}{1-\alpha z^{-D}}$ |
| Impulse response | $h[n]=\sum_{k=0}^{N}\alpha^k\,\delta[n-kD]$ |
| Poles | N·D poles at z = 0 |
| Zeros | N·D zeros, solutions of $z^D=\alpha w$ with $w^{N+1}=1,\ w\neq 1$ |
| Stability | always stable: $\sum\lvert h\rvert=\dfrac{1-\lvert\alpha\rvert^{N+1}}{1-\lvert\alpha\rvert}$ |

This is the transversal (tapped delay line) structure of Chapter 9. The cost grows linearly
with N: N multiplications per sample and N·D memory cells.

### 3.3 Model 3: infinite echoes (IIR, feedback)

$$y[n] = x[n] + \alpha\,y[n-D]$$

| Property | Value |
|---|---|
| Transfer function | $H(z)=\dfrac{1}{1-\alpha z^{-D}}=\dfrac{z^D}{z^D-\alpha}$ |
| Impulse response | $h[n]=\sum_{k=0}^{\infty}\alpha^k\,\delta[n-kD]$ |
| Poles | D poles with $z^D=\alpha$, on the circle $\lvert z\rvert=\lvert\alpha\rvert^{1/D}$ |
| Zeros | D zeros at z = 0 |
| Frequency response | $H(e^{j\omega})=\dfrac{1}{1-\alpha e^{-j\omega D}}$ |
| Magnitude squared | $\lvert H\rvert^2=\dfrac{1}{1+\alpha^2-2\alpha\cos(\omega D)}$ |
| Magnitude range | between $\dfrac{1}{1+\lvert\alpha\rvert}$ and $\dfrac{1}{1-\lvert\alpha\rvert}$ |

**Stability.** For a causal system the region of convergence is
$\lvert z\rvert>\lvert\alpha\rvert^{1/D}$. It contains the unit circle exactly when
$\lvert\alpha\rvert^{1/D}<1$, which is equivalent to $\lvert\alpha\rvert<1$. Equivalently,
$\sum\lvert h\rvert=\dfrac{1}{1-\lvert\alpha\rvert}$ converges only in that case. For
$\lvert\alpha\rvert\ge1$ the echoes do not decay, and the app shows the output growing in
time and the poles lying on or outside the unit circle.

For α = 0.6 the peak gain is 1/(1−0.6) = 2.5 and the minimum is 1/1.6 = 0.625.

### 3.4 The comb filter

Because H depends on ω only through cos(ωD), every model has a magnitude response that is
periodic in ω with period 2π/D: there are D peaks and D notches over [0, 2π). In hertz the
teeth are spaced

$$\Delta f = \frac{F_s}{D}$$

apart. With Fs = 22 050 Hz and D = 6 615 this is 3.33 Hz. The input spectrum is multiplied
by this response, $Y(e^{j\omega})=H(e^{j\omega})X(e^{j\omega})$, so the output spectrum of
real audio shows a ripple with the same spacing. The app displays this by zooming the FFT
around the strongest frequency. A short delay (a few milliseconds) gives widely spaced
teeth that change the timbre of the sound, which is why short delays are heard as
coloration and not as echo.

### 3.5 Linearity, time invariance, causality

The systems consist only of adders, multiplication by constants and delays, so they are
linear and time-invariant (Chapter 2). They are causal because the output depends only on
current and past samples. Convolution gives the output for any input:
y[n] = x[n] ∗ h[n], meaning every pulse of h[n] adds a delayed, scaled copy of the whole
signal.

---

## 4. Comparison of the three models

| Model | Difference equation | Memory | Multiplications / sample | Stable |
|---|---|---|---|---|
| One echo (FIR) | y[n] = x[n] + α·x[n−D] | D | 1 | always |
| N echoes (FIR) | y[n] = Σ αᵏ·x[n−kD] | N·D | N | always |
| Infinite echoes (IIR) | y[n] = x[n] + α·y[n−D] | D | 1 | only if \|α\| < 1 |

The IIR model gives unlimited echoes for the price of one echo. The cost is the stability
condition. Chapter 9 of the course (FIR versus IIR) makes the same trade-off. The IIR
structure here is a special case of Direct Form I: the feed-forward part is just the
constant 1, so only one delay line is needed.

---

## 5. Implementation

### 5.1 Architecture

```
echo_dsp.py   pure DSP functions, no UI, no plotting
diagrams.py   block diagrams drawn with matplotlib
app.py        Streamlit interface built on echo_dsp.py and diagrams.py
demo_cli.py   command-line demo and figure generator built on echo_dsp.py
```

Keeping the DSP in a separate module means the same code is used by the web app, the
command-line demo and the verification tests.

### 5.2 Main functions in `echo_dsp.py`

| Function | Purpose |
|---|---|
| `delay_samples(delay_ms, fs)` | D = round(τ·Fs), at least 1 |
| `coefficients(mode, alpha, D, N)` | numerator b and denominator a of H(z), in the form `lfilter` expects |
| `echo_direct(x, alpha, D, mode, N)` | sample-by-sample difference equation with a circular buffer |
| `echo_fast(x, alpha, D, mode, N)` | block-vectorised version used for real audio |
| `apply_echo(x, fs, delay_ms, alpha, mode, N)` | pads the signal with a tail, applies the echo, returns the padded input, output and D |
| `tail_length(...)` | number of extra samples so the echo can fade out |
| `impulse_response(...)` | h[n] by feeding a unit impulse through the system |
| `freq_response(...)` | closed-form H(e^{jω}) |
| `poles_zeros(...)` | roots of B(z) and A(z), including the poles or zeros at the origin |
| `is_stable(mode, alpha)` | BIBO test: always true for FIR, \|α\| < 1 for IIR |
| `verify(...)` | compares both implementations with `lfilter` on random noise |
| `make_clap`, `make_beep`, `make_melody` | built-in test sounds |
| `read_wav`, `to_wav_bytes`, `normalize` | WAV input and output |

### 5.3 Coefficients

The three models map onto the standard form H(z) = B(z)/A(z) as follows:

| Model | b | a |
|---|---|---|
| One echo | length D+1 vector with b[0] = 1, b[D] = α | [1] |
| N echoes | length N·D+1 vector with b[kD] = αᵏ | [1] |
| IIR | [1] | length D+1 vector with a[0] = 1, a[D] = −α |

### 5.4 Algorithm 1: sample by sample with a circular buffer

This is how the effect runs on a real-time DSP chip: a fixed memory block of D cells and a
moving pointer, with one multiply-accumulate per sample.

```python
buf = np.zeros(D)              # holds y[n-1] ... y[n-D]
idx = 0
for n in range(len(x)):
    yn = x[n] + alpha * buf[idx]   # buf[idx] currently holds y[n-D]
    buf[idx] = yn                  # overwrite the oldest value with y[n]
    idx = (idx + 1) % D
    y[n] = yn
```

For the FIR models the buffer stores past **inputs** (length N·D) instead of past outputs,
and each sample adds αᵏ·x[n−kD] for k = 1..N. It is slow in Python but exact, and it
serves as an independent check of the other implementations.

### 5.5 Algorithm 2: block-vectorised

For FIR the output is the input plus delayed, scaled copies of the input, which numpy does
with array slicing:

```python
for k in range(1, taps + 1):
    y[k*D:] += alpha**k * x[:-k*D]
```

For IIR, y[n] depends on y[n−D], so a plain vector operation does not work. The key
observation is that the feedback delay is exactly D samples: every block of D consecutive
output samples depends only on the block immediately before it. The block is therefore
computed in one vector operation, and the blocks are processed in order:

```python
for start in range(D, len(x), D):
    stop = min(start + D, len(x))
    y[start:stop] += alpha * y[start - D:stop - D]
```

The cost is proportional to the signal length, regardless of D.

Why not simply call `lfilter` for audio? `lfilter` multiplies by all D+1 coefficients per
sample, even though only two are non-zero, so it is slow for D in the thousands. The block
method exploits the sparse structure.

### 5.6 Tail handling

Echoes continue after the input ends, so the output must be longer than the input.
`tail_length` appends:

- one echo: D extra samples,
- N echoes: N·D extra samples,
- IIR: enough repetitions for the echo to fall below 1/1000 of its start (−60 dB), that is
  ⌈ln(0.001)/ln|α|⌉ repetitions, capped at 8 s. For α = 0.6 this is 14 repetitions,
  which is 4.2 s at τ = 300 ms. For unstable settings only 30 repetitions are rendered so
  the growth is visible.

### 5.7 Test sounds

All at Fs = 22 050 Hz and normalised to 0.8 peak:

- **Clap**: a 120 ms burst of white noise with a decay time constant of 20 ms. Its sharp
  attack makes the echo easiest to hear.
- **Beep**: an 880 Hz sine with a Hann window, 80 ms long.
- **Melody**: C4–E4–G4–C5, 0.35 s per note, with four harmonics (each 0.6 times the
  previous) and an exponential decay for a plucked-string feel.

### 5.8 Input and output

- `read_wav` accepts 16-bit, 32-bit and 8-bit integer WAV as well as float WAV, converts to
  floating point in [−1, 1], mixes stereo down to mono and keeps at most 15 s.
- Output is written as 16-bit PCM. Quantising to 16 bits adds noise at roughly
  6.02·16 + 1.76 ≈ 98 dB below full scale (Chapter 6, quantisation noise).
- `normalize` scales the signal down only if its peak exceeds 0.95, to avoid clipping on
  playback. This scaling is applied for listening and downloading only. It is **not** part
  of the echo system, which stays linear.

---

## 6. The demo application

Start it with `python -m streamlit run app.py` (or double-click `run_demo.bat`) and open
`http://localhost:8501`.

### 6.1 Controls (sidebar)

| Control | Range | Default |
|---|---|---|
| Model | one echo FIR / N echoes FIR / IIR | one echo FIR |
| Delay τ | 20 to 1 000 ms, step 10 | 300 ms |
| Attenuation α | −0.95 to 0.95, step 0.05 | 0.6 |
| Number of echoes N | 1 to 8 (N-echo model only) | 4 |
| Allow \|α\| ≥ 1 | checkbox (IIR only) widens α to ±1.1 | off |

The sidebar also shows the difference equation and H(z) of the selected model, and an error
box when the chosen α makes the system unstable.

### 6.2 Tab 1: Audio demo

- Choose a source: built-in sound, microphone recording, or WAV upload.
- Four readouts: Fs, delay D in samples (with τ in ms), α and the output peak.
- Two audio players (original and with echo) and a button to download `echo.wav`.
- Waveform plot of input and output, with dashed red lines at the expected echo times n₀ + kD.
- Collapsible FFT plot: full 0–4 kHz view and a zoom that shows the comb teeth spaced Fs/D apart.

### 6.3 Tab 2: System analysis

- Block diagram of the selected model (adder, multipliers, delay element).
- With a small illustrative delay D (1 to 16 samples, so the shapes are readable): impulse
  response h[n], magnitude and phase of H(e^{jω}), and the pole–zero diagram with the unit
  circle. Poles and zeros at the origin are annotated with their multiplicity.
- A message on stability: for IIR the pole radius |α|^(1/D) is shown with a green or red
  verdict, and the peak and minimum gain are printed.
- A second frequency-response plot with the **real** delay (τ and Fs from the app), zoomed
  to the first few comb teeth.

### 6.4 Tab 3: Implementation check

A button runs all three implementations on 4 000 random noise samples and shows the
maximum error against `lfilter` and the run time. The source code of `echo_direct` and
`echo_fast` can be expanded in place to explain the circular buffer during the demo.

### 6.5 Command-line fallback

```bash
python demo_cli.py            # verify, write WAV files, play them on Windows, make figures
python demo_cli.py --no-play  # only write files
python demo_cli.py --delay 250 --alpha 0.7
```

It writes `output/*.wav` (original and the three echo models for the clap and the melody)
and `figures/*.png` (impulse responses, frequency response, pole–zero diagrams, block
diagrams, clap waveform).

---

## 7. Verification and results

### 7.1 Correctness against `scipy.signal.lfilter`

For each of the three models, α ∈ {0.6, −0.5} and D ∈ {1, 7, 50}, both implementations
were run on 4 000 samples of Gaussian noise. The largest absolute difference from
`lfilter` was:

| Model | `echo_direct` | `echo_fast` |
|---|---|---|
| One echo (FIR) | 0 | 0 |
| N echoes (FIR, N = 3) | 8.9e-16 | 8.9e-16 |
| IIR | 0 | 0 |

These differences are floating-point rounding only.

### 7.2 Pole locations

For the IIR model with α = 0.8 and D = 8 all eight poles had radius 0.972, matching
|α|^(1/D) = 0.8^(1/8) = 0.972. With α = 0.6 and D = 6 the radius is 0.918 and with
α = 1.1 and D = 8 it is 1.012, outside the unit circle.

### 7.3 Run time (one measurement, one echo FIR, D = 50, 4 000 samples)

| Implementation | Time |
|---|---|
| `echo_direct` (Python loop) | 1.69 ms |
| `echo_fast` (blocks) | 0.02 ms |
| `lfilter` | 0.34 ms |

The block method is about 85 times faster than the loop and 17 times faster than
`lfilter` here. The gap to `lfilter` should widen as D grows, because `lfilter` does work for
every one of the D+1 coefficients; this was not measured separately.

### 7.4 Behaviour at the edges of the parameter space

Streamlit's automated test harness drove the whole application through these cases, all
without exceptions:

- one echo with α = 0.6 and with α = −0.9, τ = 20 ms;
- N echoes with N = 8 on the melody, and N = 1 with α = 0 and τ = 1 000 ms;
- IIR with α = 0.95 on the beep;
- IIR with α = 1.05 and α = −1.1 (unstable): the error messages appeared as designed.

WAV reading was checked for 16-bit, 32-bit, 8-bit and float files, stereo and mono.

### 7.5 What the plots show

- **Waveform (clap, IIR, τ = 300 ms, α = 0.6):** a series of copies spaced 0.3 s apart,
  each 0.6 times the previous one, as predicted by h[n].
- **Impulse responses (α = 0.6, D = 8):** one extra pulse of height 0.6 (one echo), three
  pulses 0.6, 0.36, 0.216 (N = 3), and an unending sequence 0.6ᵏ (IIR).
- **Frequency response:** comb shapes; the IIR peaks are sharper than the FIR ones.
- **Pole–zero diagram:** FIR has zeros on a circle and poles at the origin; IIR with
  |α| < 1 has poles on a circle inside the unit circle; IIR with α = 1.1 has them outside.

---

## 8. Course concepts used

| Chapter | Concept | Where it appears in the project |
|---|---|---|
| 2: Discrete-time signals and systems | Difference equations, block diagrams (adder, multiplier, unit delay), LTI, convolution, recursive vs non-recursive | Models, block diagrams, h[n], FIR vs IIR |
| 3: z-transform and LTI systems | H(z), poles and zeros, ROC, causality, BIBO stability (all poles inside the unit circle) | Pole–zero diagrams and the \|α\| < 1 condition |
| 5: Frequency-domain analysis | Frequency response, magnitude and phase, comb filters, Y = H·X | Comb-filter analysis, spectrum of the output |
| 6: Sampling and reconstruction | Sampling, mapping time to samples, quantisation noise | D = round(τ·Fs), 16-bit output |
| 7 and 8: DFT and FFT | Spectrum estimation with the FFT | FFT plots in the demo |
| 9: Implementation of discrete-time systems | FIR transversal structure, IIR with feedback, Direct Form, delay-line memory | Circular-buffer implementation, cost comparison |

Chapters 10 (filter design), 11 (multirate) and 13 (linear prediction) are not used in this
project. They are natural next steps (see Section 12).

---

## 9. Presentation slides

The deck has 14 slides. Each has speaker notes. This is the outline with the gist of what
is said.

| # | Slide | Message |
|---|---|---|
| 1 | Cover | Title: Digital Echo Effect. The graphic is the impulse response of the echo system. |
| 2 | Problem | An echo is a delayed, weaker copy of the sound: τ = 2d/c. Example: wall at 51 m gives about 0.30 s. |
| 3 | Discretisation (Ch. 6) | τ becomes D = round(τ·Fs) samples. 22 050 Hz × 0.3 s = 6 615 samples ≈ 13 KB of memory. |
| 4 | Model 1: one echo | y[n] = x[n] + α·x[n−D], H(z) = 1 + αz⁻ᴰ. No feedback, so FIR and always stable. |
| 5 | Model 2: N echoes | Sum of delayed copies weighted by αᵏ. Still FIR, but cost grows with N. |
| 6 | Model 3: IIR | Feed the output back: y[n] = x[n] + α·y[n−D]. Infinite echoes with one multiplier. Stable only if \|α\| < 1. |
| 7 | Comparison | Table of memory, multiplications and stability; the IIR gives unlimited echoes for the price of one. |
| 8 | Impulse response (Ch. 2) | Pulses spaced D samples apart, each α times smaller; FIR stops, IIR continues. |
| 9 | Pole–zero diagram (Ch. 3) | IIR poles at radius \|α\|^(1/D): inside the circle is stable, outside is unstable. |
| 10 | Frequency response (Ch. 5) | The echo is a comb filter; teeth spaced Fs/D = 3.33 Hz. |
| 11 | Implementation (Ch. 9) | Circular buffer of D cells, one multiply and one add per sample; three implementations agree to below 1e-15. |
| 12 | Demo | Four steps: choose a sound, set parameters, listen, analyse. |
| 13 | Summary | Table mapping each chapter to its use in the project. |
| 14 | Thank you / questions | Future work: reverb, real-time, stereo ping-pong. |

---

## 10. Five-minute demo script

Open the app beforehand and turn the speakers up.

1. **Audio demo tab**, source = built-in sound, choose the clap. One echo (FIR), τ = 300 ms,
   α = 0.6. Play the original, then the echo. Point at the dashed lines in the waveform:
   the echo lands exactly D samples later.
2. Switch to IIR: a chain of fading echoes. Raise α to 0.9 for a longer tail. Lower τ to
   50 ms to hear the room-like effect.
3. Choose the melody with IIR to hear the effect on music.
4. Source = microphone: say a sentence (grant microphone permission once) and listen to it
   with the echo.
5. Open the FFT panel: the zoomed view shows ripples spaced Fs/D hertz apart (the comb filter).
6. **System analysis tab**: block diagram, h[n], |H|, pole–zero diagram. For IIR tick
   "Allow |α| ≥ 1" and set α = 1.05: the poles leave the unit circle, a red warning appears,
   and back in the audio tab the echoes grow instead of decaying.
7. **Implementation check tab**: run the check and show errors around 1e-16. Expand the
   source of `echo_direct` to explain the circular buffer.

If the browser or microphone fails, run `python demo_cli.py` and play files from `output/`.

---

## 11. Questions an examiner may ask

**Why is the FIR echo always stable?**
Its impulse response has finitely many terms, so Σ|h[n]| = 1 + |α| is finite (BIBO). All
poles of H(z) sit at z = 0.

**What is the stability condition for the IIR echo?**
The poles solve z^D = α, so each has magnitude |α|^(1/D). They are inside the unit circle
exactly when |α| < 1. Then Σ|h[n]| = 1/(1 − |α|) is finite.

**Why is it called a comb filter?**
|H(e^{jω})|² = 1 + α² + 2α·cos(ωD) (one-echo FIR) is periodic with period 2π/D, which gives
D peaks and D notches over a full turn of frequency. In Hz the peaks are spaced Fs/D apart.

**How long must the delay be to hear an echo?**
About 50 ms or more. Shorter delays are heard as coloration (the comb filter) and not as a
separate echo.

**What does a negative α mean?**
The echo is phase-inverted. For the FIR model the peaks move to ω = (2k+1)π/D.

**How much memory is needed?**
D samples for one echo and IIR, N·D for N echoes. D = 6 615 samples at 2 bytes each is about
13 KB (the Python code uses 8-byte floats, so about 52 KB).

**Why not use `lfilter` for long audio?**
It processes all D+1 coefficients for every sample although only two are non-zero. The block
method in `echo_fast` uses the sparse structure; for IIR each block of D samples depends
only on the previous block.

**Is the system linear and time-invariant?**
Yes: it contains only adders, constant multipliers and delays (the playback normalisation is
outside the system).

**Why does the IIR echo need its feedback to be below 1?**
Otherwise each echo is at least as large as the previous one, the output grows without
bound and a bounded input gives an unbounded output, so BIBO stability fails.

**How is the delay turned into samples if τ·Fs is not an integer?**
It is rounded. The error is at most half a sample, 1/(2·Fs) ≈ 23 µs at 22 050 Hz, which is
inaudible. Fractional delays would need interpolation.

---

## 12. Limitations and future work

**Current limitations**

- Only integer sample delays; no fractional delay.
- Uploaded WAV files must be uncompressed PCM or float, and only the first 15 s are processed.
- Stereo input is mixed down to mono, and the output is mono.
- For IIR with α close to 1 the rendered tail is capped at 8 s, so at α = 0.95 the echo is
  cut while it is still about 0.26 times the first echo (about −12 dB), and you can hear the
  abrupt end.
- The audio demo processes a recording after it is captured; it is not a live stream.
- The block implementation is fast in Python but is not real-time code for a DSP chip; the
  per-sample version shows the real-time structure.

**Possible extensions**

- **Reverb:** several parallel comb filters (this IIR model with different D and α) feeding
  series all-pass filters, as in Schroeder's reverberator.
- **Low-pass filter in the feedback loop:** makes each repeat darker, as in a real room or tape echo.
- **Real-time processing** from the microphone stream.
- **Stereo ping-pong echo:** echoes alternating between the left and right channel.
- **Fractional delay** using interpolation (Chapter 6 and Chapter 11 topics).

---

## 13. Project files and reproduction

```
Digital_Echo_Effect/
├── app.py              Streamlit application
├── echo_dsp.py         DSP core
├── diagrams.py         block diagram drawing
├── demo_cli.py         command-line demo and figure generator
├── run_demo.bat        double-click launcher for Windows
├── requirements.txt    numpy, scipy, matplotlib, streamlit
├── figures/            generated plots
├── output/             generated WAV files (not committed)
├── .streamlit/         Streamlit configuration
├── README.md           short introduction
├── DEMO_GUIDE.md       demo script and Q&A
└── PROJECT_REPORT.md   this document
```

To reproduce everything from scratch:

```bash
python -m pip install -r requirements.txt
python demo_cli.py --no-play          # regenerates figures/ and output/
python -m streamlit run app.py        # starts the web demo
```

Software versions used during development: Python 3.13, NumPy 2.5, SciPy 1.18,
Matplotlib 3.11, Streamlit 1.66.

---

## 14. References

1. J. G. Proakis and D. G. Manolakis, *Digital Signal Processing: Principles, Algorithms, and Applications*. The structure of the course (Chapters 2, 3, 5 to 9) follows this book.
2. A. V. Oppenheim and R. W. Schafer, *Discrete-Time Signal Processing*.
3. M. R. Schroeder, "Natural sounding artificial reverberation," *Journal of the Audio Engineering Society*, 1962 (comb and all-pass filters for reverb).
4. DGT302 lecture slides, Chapters 2, 3, 5, 6, 7, 8 and 9.
5. NumPy, SciPy (`scipy.signal.lfilter`, `scipy.io.wavfile`), Matplotlib and Streamlit documentation.