# DAfny Resource Usage Measurement

Tools to detect and diagnose brittle verification.

## What does Darum do?

Dafny verifies code by translating it into Assertion Batches in the Boogie language, that then are verified by the Z3 solver.

Complex Dafny code typically takes a long time to verify. Until recently, the common advice to help Dafny code verify successfully was to add information to the code through assertions, to help Z3 find a solution. However, since Dafny 3.x there’s been a growing effort to add facilities to the language to actually limit what information reaches Z3. This is because the solver can sometimes have "too much information" and go down unproductive paths while looking for a solution. This bogs down the development process by causing longer verification times or timeouts instead of definite answers, and is a very common pain point for Dafny users.

The user can guide Z3 down the right path by removing alternatives, that is, controlling what the solver “knows”. The problem then is that Dafny inherently makes it difficult to know at any point what is actually the right path and what does the solver actually know. Indeed, at the Dafny level (as opposed to digging into Boogie and Z3), the only information we get about the process is the result (verification successful, failure or timeout), plus how costly was it for the solver to reach that result. These results are what Darum tries to glean information from.

**Darum helps the user find patterns in the solver costs, discovering hints to guide the debugging of verification brittleness. It does so by analysing and comparing the cost of verification at different granularities of the Assertion Batches, in a mostly automated way, by using existing Dafny facilities.**

## Terminology

* **Dafny Assertions**: Dafny internally works with both explicit assertions (those in the code) and implicit ones (generated internally from the code). For clarity, we'll refer to both of them as DAs.
* **AB**: Assertion Batch. The way in which DAs are grouped by Dafny for verification. They are the minimal unit of observable behavior in Dafny's results.
* **Brittleness**: A verification result is said to be brittle when its cost isn't stable: an unchanging Dafny file can happen to always verify correctly, but with wildly different Resource Usage. [^1]
* **IA**: Dafny's Isolate Assertions mode. In standard verification mode, Dafny groups all DAs generated by a member into a single Assertion Batch. A radical alternative is to use the `--isolate-assertions` argument, which causes Dafny to isolate each DA into a separate Assertion Batch. This is the finest verification granularity that Dafny offers.
* **Member**: Dafny's methods or functions
* **RU**: Resource Usage: the cost of a verification run, as reported by Z3. RU costing is more deterministic than timing-based costing.
* **OoR**: Out of Resources. It's the result when Dafny/Boogie/Z3 are given a resource limit and the verification takes more RU than this limit. Equivalent to a timeout.

[^1]: It's worth noting that Dafny can also flip-flop between explicit success and failure of verification. In this case, the official advice is to believe the success result but work on fixing the failures. [link]

## How does Darum work?

Dafny's official [docs](https://dafny.org/dafny/DafnyRef/DafnyRef.html#sec-brittle-verification) and [tools](https://github.com/dafny-lang/dafny-reportgenerator/blob/main/README.md) use statistical measures like stddev and RMS% to measure verification brittleness. However, we argue that it's more useful to think of simple min/max values. For example, consider the case of running 10 iterations of the verification process, in which 9 of the results are closely clustered but one single result deviates far away, being either much cheaper or much more expensive than the rest. Taking the stddev or RMS of these 10 cases would obviously dampen the extremes, while we argue that they are precious hints that needs to be highlighted instead. Indeed, each time that the verification runs, these rare but extreme values are the ones that will turn things unexpectedly slow or fast, and so they point towards problems or fixes. Furthermore, AB variability seems to compose disproportionally into more extreme variability at the member level, multiplying the effect of AB's span. This all suggests that, for reliability, it's necessary to minimize the span of Resource Usage costs.

It's worth noting that, while we're focusing on RU variability to combat brittleness, these tools are also useful for plain optimization, since they help account for plain RU usage and rank where the verification time is being spent.

In a nutshell, the key insights that Darum exploits are:
* The RU needed to verify any Dafny code pertains to a probability distribution of evolving shape.
* These distributions tend to grow wide and multimodal, causing the user to think that some problem appears and disappears – as opposed to a cost varying across a smooth range.
* The distributions of ABs compound to members' distributions worse than linearly. Hence, relatively narrow distributions at the AB level compound to much wider distributions for the containing members.

### An evolving probability distribution?

Consider the evolution of a piece of Dafny code:
* When the code is simple, the distribution is close to a spike: every verification run has a predictable cost.
* As the code grows and turns more complicated, the cost distribution starts to widen, and so time/RU needed for verification starts to vary. Perversely, this is hard to notice initially because probably the worst case is still fast enough that the user doesn't stop to think about it: the code is growing, so growing verification time is in principle to be expected. Worse, in a bigger codebase in which individual members are only starting to misbehave, the total distribution naturally tends to smooth and statistically compensate for the individual variation.
* At some point, some AB/member's verification gets complex enough that its distribution turns multimodal: sometimes verification runs fast, sometimes it runs much more slowly. Even worse, when this happens in one AB/member, because of how Dafny + Boogie + Z3 work internally, that randomness will keep affecting the total distribution even while working on other ABs/members. It is at this point that the user starts noticing that errors or timeouts appear and disappear without explanation.
* As work progresses, other members' distributions will keep widening and also turn multimodal, each of them affecting the total distribution with new modes.

The result is that one starts editing line X of a Dafny file and suddenly verification fails in a surprising, seemingly unrelated way. Doing some small change might seem to restore the good behavior - but this is an illusion caused by the multimodality of the distribution. In fact, redoing the latest changes now seems to work well after all! One shrugs the problem off and pushes forward, but 2 lines later again the failure appears. *One can't pinpoint why changes to a member sometimes cause a timeout while other times verify correctly; what seemed a stable configuration suddenly stops working even though everything seems to be the same. After some busywork suddenly things seem OK, so again one pushes forward... until next stop.*

It might be amusing to note the unfortunate similarity of this situation to that of Skinner's variable ratio reinforcement: random actions seem to trigger unexplained positive outcomes, [causing the subject to develop superstition-like behaviors](https://psychclassics.yorku.ca/Skinner/Pigeon/) with the hope of triggering further positive outcomes. 

### Why would a cheap verification turn expensive?

The fact that a cheap verification run exists at all is great news: if we managed to keep Z3 in that verification path every time, we'd have fast and stable verification.

The problem is that Z3 randomly [^3] follows a different path each time, and so if there's unneeded, "distracting" information, Z3 is bound to eventually follow it, possibly getting lost. This unneeded information comes from other DAs introduced by the context built up by the containing member. Hence **reducing the unneeded information introduced into an AB by previous DAs is key to stop Z3 from getting lost.**

[^3]: This "Z3 randomness" is an oversimplification, but the effect for us is still the same: the Dafny programmer has no way to really pin down the path that Z3 takes, though on the contrary it's very easy to cause Z3 to take different paths. Hence Darum exploits this randomness instead of trying to control it.

IA mode breaks down a member's standard single AB into as many ABs as DAs. E.g., if member M contains DA1 and DA2, AB2 would be equivalent to `assume DA1; assert DA2`.

One intriguing result of using IA mode is that the sum of the cost of the isolated ABs in a member is *typically* much more expensive than verifying the whole member as a single AB, but also much more stable. This suggests 2 possibilities:
  - Stabilisation by pessimisation: break down every member into smaller members [^2][^4].
  - Conversely, sometimes ABs require higher RU than the containing member, or even fail to verify. This likely means that previous DAs in the member built up some context that helped / was necessary for the current DA to pass verification. Notably, this context includes facts that the solver “discovered” while proving previous DAs, and which will be missing when those DAs are `assume`d. It’s **a case where DAs grouped into an AB help each other**.

Consider that, as code evolves, DAs (both explicit and implicit) change, creating different possible paths for the solver. A member whose DAs support each other but don't unduly widen the horizon would then create a robust path, resilient to small changes. In contrast, a member whose DAs only tangentially build on each other and that widen the horizon unnecessarily will be vulnerable, or even prone, to a wide variation of costs.

While the first impulse might be to limit the length of members, and this would help in a way, note that the length is not the real problem. The key consideration is whether the DAs in the member build on each other robustly.

[^2]: Either by physically defining new members, or using facilities like {:split_here} XXX or IA mode itself.
[^4]: Dafny seems to be following this path towards using IA mode by default. link XXX

### So how does Darum help?

Darum can be used to:
1. Analyse cost and variability of verification at various AB granularities.
   * Standard verification mode: Simply running multiple verifications on a Dafny file is enough to discover whether the cost is stable or not. Typically, a Dafny file will contain multiple members, so Darum helps decide which ones will yield the greatest gains if stabilized.
   * Isolated Assertions mode: The extreme case of turning every DA into a new AB.
   * Anything in between: While IA mode is enabled by a simple CLI argument, the Dafny programmer can also manually break down a member into multiple ABs by either writing smaller members, or using facilities like `{:split_here}`.
2. Compare cost and variability of verifying at different granularities.
    * Knowing how the distribution of verification costs varies across different AB granularities can point to stabilization opportunities, and even to what needs to be done for stabilization.


## What exactly is Darum?

Darum consists of 3 loosely coupled tools:
* `dafny_measure`: a wrapper around `dafny measure-complexity` for easier management of the generated logs, by recording:
  - The timestamp
  - The arguments used
  - part of the input file's hash, to ensure that multiple logs can be meaningfully compared

  Additionally, `dafny_measure` warns if `dafny` misbehaves, like when z3 processes are leaked (bug XXX).
* `plot_distribution`: a tool to be run on the logs generated by `dafny measure-complexity`. It runs some tests on the verification results contained in the log, scores them heuristically for their potential for improvement, presents the results in summary tables, and plots the most interesting results for further analysis.
* `compare_distribution`: a tool to compare verification runs at different Assertion Batch granularity, i.e. with and without "Isolate Assertions" mode.

## Installation

Darum's tools are written in Python and available in Pypi.

Probably the easiest way to install Darum is using `pipx`, which should be available in all common package managers, like `brew` in MacOS.

```
$ brew install pipx
...
$ pipx install darum
```

This will make Darum's tools available as common CLI commands.

## Usage

Each of the tools has a `--help` argument that lists the available options.

In general, the workflow will be:
1. Run `dafny_measure`
2. Plot the logfile with `plot_distribution`
3. If some member looks interesting/suspicious, run `dafny_measure` again in IA mode, possibly with `--filter-symbol` to focus only on that member
4. Plot the new logfile with `plot_distribution`
5. And/or compare both logfiles with `compare_distribution`.

```bash
$ dafny_measure myfile.dfy
...
Generated logfile XYZ.log
$ plot_distribution XYZ.log
...
$ dafny_measure myfile.dfy --isolate-assertions --extra "--filter-symbol expensiveFunction"
...
$ compare_distribution XYZ.log -i XYZ_IA.log
...
```

#### How many iterations to run with dafny_measure? (`-i` argument)
In practice, 5-10 iterations seem to work well. Bigger numbers (100 iterations or more) might be interesting just to get an idea of how the distribution really looks like, what are its modes, and how extreme it can get.

## Interpreting the results



### The plots

#### Plain plots

##### What is an acceptable span?
Badly behaving members seem to blow up their span rather abruptly, so after a couple of experiments one will quickly get a feeling of which members are OK and which ones need work. However, as a rule of thumb: in IA mode, spans seem to get exponential once they go over 5%. In standard mode, this happens over 10%.
(XXX possible interesting question: is it exponential, or is there a discontinuity? if so, why?)


##### Worst offenders

ABs are scored according to their characteristics, including the fact that a non-successful AB makes following ABs inside the same member unreliable.

The top N are plotted. For plots with failures/OoRs, the rightmost bar is wider to highlight those failures.

The plot starts in transparent mode to make it easier to see where bars overlap. Clicking on the legend makes the corresponding plot easier to see.

Verification results that happen rarely are specially important. Hence, the Y axis is logarithmic to more easily capture single atypical results.


#### Comparative plots

This type of plot compares RUs of members verified in standard mode (plotted with X symbols) against the RU sum of those same members verified in IA mode (plotted as spikes). The comparisons are always member-wise. Note the Log X axis. Things to notice in each member, in order of attention needed:
* Ideal behavior happens when the X are clustered together (meaning stability) and are much farther to the left (meaning cheaper) than the spikes, which will also be clustered together. This is the typical situation for short and simple members.
* Bigger X dispersion means bigger brittleness in standard mode. If meanwhile the spikes are clustered, they give a reference of the stability what could be attained by pessimisation. Notably, if some of the X turn out to be more expensive than the spikes, this is a clear indication that action is needed.
* If even the spikes are dispersed, this means that even the individual ABs show brittleness. It's advisable to plot individually the IA mode log to find what part of the code is causing it, and use any of the possible remedies mentioned further down.

### The table/s

Standard mode distribution plots contain a table analyzing the logs. For convenience, the column "diag" in the table summarizes the situation for each row with a series of icons:
* 📊 : This element was plotted because was among the top scores.
* ⌛️ : This element finished as Out of Resources.
* ❌ : This element explicitly failed verification.
* ❗️ : This element had *both* successful and failed/OoR results. Note that purely successful results are not highlighted because they're the hoped default; but fliflopping results merit extra attention. [According to the Dafny developers](https://github.com/dafny-lang/dafny/issues/5615#issuecomment-2223290919), as long as there is a successful result, the goal should be to stabilize it to avoid the failures – as opposed to discarding the success because of the failures.
* ❓ : This element had a single success across all iterations. It's probably prioritary to stabilize its success.
* ⛔️ : This element was excluded from the plot on request.

IA mode distribution plots contain 2 tables. The first one is equivalent to the one just described, only applied to the individual ABs. The second table shows the summary data at the member level, still in IA mode.

These tables will naturally suggest questions about how members' results compare in IA mode and in standard mode. These questions should be easier to answer through the `compare_distribution` plots.

### Comments

If interesting/atypical situations were detected while preparing the plots, they will be listed in a Comments section at the bottom of the plot page.


## Pitfalls

### Start in standard mode, dig into IA mode once a problem is apparent

As mentioned, a member can verify stably in normal mode, while in IA mode present ABs that are surprisingly brittle or even fail. The significance of this situation is unclear (XXX), therefore:
1. Probably there's no immediate harm in leaving the member as it is. However, you might still want to keep an eye on it in case that any small change in the member triggers brittleness.
2. More importantly, It's probably best to **focus on fixing problems that can be first be found at the member level with standard verification mode**. On the contrary, starting by looking for problems at the IA mode might cause you to spend effort on trouble that maybe isn't really there. Dafny's `--filter-symbol` is a great way to avoid the temptation of fishing for unnecessary trouble in IA mode.

### Keep in mind that, in IA mode, ABs are "chained". If one fails, the rest are removed.

To minimize noise, once an AB fails in IA mode, we ignore subsequent ABs in the same iteration. In such a case, the tables will show that some ABs have a smaller number of results than previous ones. In the extreme case of only 1 result remaining for a given AB, it will be tagged with the ❗️ icon.

## Some remedies to keep in mind

### Dafny standard library

Since version 4.XXX, Dafny includes a standard library that provides pre-verified code. This library includes helper lemmas for things like bitwise manipulation and non-linear arithmetic, which are typical pain points in normal development. Using this library instead of implementing one's own version might save much work; or, if a reimplementation is needed, can at least offer examples of how things were implemented by the very Dafny developers.

### Section on Verification debugging in Ref Manual

Link XXX, plus extra docs?
