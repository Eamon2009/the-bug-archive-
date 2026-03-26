# The Bug Archive

> *"To err is human — but to really foul things up requires a computer."*
> — Paul Ehrlich

---

## What Is This Repository?

**The Bug Archive** is a curated collection of the most consequential software bugs, glitches, and engineering failures in recorded history. This is not just a list of technical curiosities — it is a sobering record of moments when a missing character, a wrong unit, a race condition, or a two-digit assumption changed the course of history, cost billions of dollars, and in some cases, ended human lives.

This archive exists to educate. Every entry is a lesson. Every disaster was preventable.

---

##  Why This Archive Matters

Software is invisible infrastructure. It runs inside airplanes, hospital machines, stock exchanges, space probes, and nuclear reactors. When it works, no one notices. When it fails, the consequences can be catastrophic.

Unlike a bridge collapse or a factory fire, a software bug leaves no rubble — only numbers on a screen, a silent machine, or in the worst cases, a name in an obituary.

Studying these failures is not about assigning blame. It is about understanding how systems fail so that we — as engineers, developers, and technologists — can build better ones.

---

## Timeline of Major Software Disasters

---

### 1962 — Mariner 1 | *The Hyphen That Cost $90 Million*

| Detail | Info |
|---|---|
| **Date** | July 22, 1962 |
| **System** | NASA Mariner 1 space probe guidance software |
| **Root Cause** | A single missing superscript bar (overline) in a handwritten formula, incorrectly transcribed into code |
| **Loss** | ~$90 million (rocket + economic damage) |
| **Lives Lost** | None |

**What happened:** The Mariner 1 rocket, destined for Venus, veered off its flight path seconds after launch. Mission Control destroyed it 293 seconds into flight. The cause was traced to a single missing notation — a superscript bar — in a mathematical formula. Without it, the software misread normal velocity fluctuations as errors and overcorrected, sending the rocket off course.

**Lesson:** Transcribing formulas manually from paper to code is a dangerous process. Formal specification languages and code review exist for this exact reason.

---

### 1983 — Soviet Nuclear False Alarm | *The Bug That Almost Started World War III*

| Detail | Info |
|---|---|
| **Date** | September 26, 1983 |
| **System** | Soviet satellite early-warning system (Oko) |
| **Root Cause** | Software incorrectly interpreted sunlight reflections off clouds as incoming U.S. missiles |
| **Loss** | Nearly irreversible nuclear escalation |
| **Lives Lost** | Potentially hundreds of millions (averted by one man) |

**What happened:** Soviet Lt. Col. Stanislav Petrov received a system alert that five U.S. ballistic missiles had been launched toward the USSR. The satellite warning system reported a high-confidence launch. Petrov trusted his instinct over the software and labeled it a false alarm — a decision that may have prevented nuclear war. The bug was a software flaw that could not distinguish between sunlight reflections and missile launches.

**Lesson:** Critical systems must have human override mechanisms. Blind trust in software in life-or-death scenarios is itself a systemic failure.

---

### 1985–1987 — Therac-25 | *When a Race Condition Killed Patients*

| Detail | Info |
|---|---|
| **Date** | 1985–1987 |
| **System** | Therac-25 radiation therapy machine |
| **Root Cause** | A race condition in software — operators who typed too fast could accidentally arm the machine in high-power mode without safety shielding |
| **Loss** | Unquantifiable human suffering |
| **Lives Lost** | At least 6 patients killed or severely injured by radiation overdoses |

**What happened:** The Therac-25 was a computer-controlled radiation therapy machine designed to treat cancer. A software bug involving a race condition meant that if a technician entered commands too quickly, the machine could fire a full-power electron beam without the physical shielding that protected patients. Patients received radiation doses hundreds of times higher than prescribed. Several died. Others were left with permanent injuries.

**Lesson:** Medical software must undergo independent safety auditing. Removing hardware safety interlocks and replacing them with software-only checks is categorically dangerous.

---

### 1987 — UK DHSS Rounding Error | *£100 Million Lost to Floating Point*

| Detail | Info |
|---|---|
| **Date** | 1987 |
| **System** | UK Department of Health and Social Security (DHSS) benefits calculation system |
| **Root Cause** | A small floating-point rounding error in inflation calculations |
| **Loss** | ~£100 million in incorrect pension payouts |
| **Lives Lost** | None |

**What happened:** The British government had been underestimating inflation by approximately 0.1% for over a year due to a programming error in their systems. Over 9 million pensioners received incorrect payments, and the cumulative financial error compounded to around £100 million before it was discovered.

**Lesson:** Financial systems with compounding calculations need automated validation checks. Rounding errors seem trivial until they accumulate at national scale.

---

### 1994 — Intel Pentium FDIV Bug | *$475 Million for a Math Error*

| Detail | Info |
|---|---|
| **Date** | 1994 |
| **System** | Intel Pentium CPU floating-point division unit |
| **Root Cause** | Missing entries in a lookup table used for division operations caused rare but incorrect results |
| **Loss** | ~$475 million in chip replacements |
| **Lives Lost** | None |

**What happened:** Intel's Pentium processor, praised as a breakthrough in computing, contained a flaw in its floating-point division unit. A lookup table used in division had several missing entries, causing the chip to return slightly wrong answers for certain calculations. Intel initially downplayed the issue, claiming the error would affect average users only once every 27,000 years — but scientists, engineers, and financial analysts who relied on precise arithmetic disagreed. Public outcry forced Intel to replace all affected chips.

**Lesson:** Hardware-level bugs are extraordinarily difficult to patch. Rigorous pre-release testing of mathematical units is non-negotiable, especially for processors used in scientific applications.

---

### 1996 — Ariane 5 Rocket Explosion | *$370 Million in 37 Seconds*

| Detail | Info |
|---|---|
| **Date** | June 4, 1996 |
| **System** | Ariane 5 rocket inertial guidance software |
| **Root Cause** | A 64-bit floating-point number was converted to a 16-bit signed integer, causing an overflow. The software was reused from Ariane 4 without re-validation. |
| **Loss** | ~$370 million (rocket + scientific payload) |
| **Lives Lost** | None (unmanned) |

**What happened:** The European Space Agency's Ariane 5 rocket — a decade in development — self-destructed 37 seconds after its maiden launch. The cause was a single software exception: a 64-bit horizontal velocity value exceeded the range of the 16-bit variable it was being stored in. This caused an overflow, crashed the inertial reference system, and passed an error code to the flight control system, which interpreted it as flight data. The rocket veered off course and was destroyed. Critically, the offending software was reused from the Ariane 4 rocket and was never retested in the context of Ariane 5's faster, more powerful engines.

**Lesson:** Reused code must be re-validated in every new context. Assumptions embedded in old software do not automatically carry over to new systems.

---

### 1999 — Mars Climate Orbiter | *Lost in Space for a Unit Mismatch*

| Detail | Info |
|---|---|
| **Date** | September 23, 1999 |
| **System** | NASA Mars Climate Orbiter navigation software |
| **Root Cause** | One engineering team used imperial units (pound-force seconds), another used metric (newton-seconds). No cross-validation was done. |
| **Loss** | $125 million spacecraft |
| **Lives Lost** | None |

**What happened:** After a 10-month journey to Mars, the Climate Orbiter was lost during orbital insertion. Ground-based navigation software used by a subcontractor generated data in imperial units, while NASA's flight systems expected metric units. The mismatch caused the spacecraft to approach Mars at the wrong angle, sending it too deep into the Martian atmosphere where it was destroyed by atmospheric stress.

**Lesson:** Interface contracts between software systems must be explicit, documented, and validated. Especially in multi-team projects, unit standards are not optional — they are critical infrastructure.

---

### 1999–2000 — The Y2K Bug | *$300–600 Billion to Fix a Two-Digit Shortcut*

| Detail | Info |
|---|---|
| **Date** | 1999–2000 |
| **System** | Virtually every legacy computer system worldwide |
| **Root Cause** | Developers in the 1960s–1980s stored years as two digits (e.g., "99") to save memory, never anticipating what would happen when "00" arrived |
| **Loss** | $300–$600 billion globally in remediation costs |
| **Lives Lost** | None (the crisis was largely averted) |

**What happened:** Decades before the millennium, programmers saved memory by storing years as two digits. "1967" became "67." It seemed clever at the time. But as the year 2000 approached, the world realized that systems might interpret "00" as "1900" — potentially crashing banking software, air traffic control, medical systems, and nuclear infrastructure simultaneously. Global mobilization to patch, replace, and rewrite millions of lines of legacy code cost an estimated $300–600 billion. The disaster was mostly averted — not because the bug wasn't real, but because the world spent enormous resources fixing it.

**Lesson:** Short-term technical shortcuts have long-term costs. Today's "good enough" is tomorrow's catastrophic liability.

---

### 2003 — Northeast Blackout | *55 Million People in the Dark*

| Detail | Info |
|---|---|
| **Date** | August 14, 2003 |
| **System** | FirstEnergy alarm system software (GE Energy's XA/21) |
| **Root Cause** | A race condition bug caused the alarm system to silently fail; operators were not alerted to critical grid failures |
| **Loss** | ~$6 billion in economic damage |
| **Lives Lost** | ~100 deaths attributed to the blackout |

**What happened:** A software bug in the power grid's monitoring system caused the alarm system to stop functioning — silently. Operators at FirstEnergy in Ohio had no alerts when transmission lines began failing. Without that information, they could not take corrective action. The cascading failures spread across the northeastern United States and Canada, cutting power to 55 million people over two days.

**Lesson:** Silent failures are often more dangerous than loud ones. Software systems that fail without notification give operators a false sense of stability.

---

### 2012 — Knight Capital Group | *$440 Million in 45 Minutes*

| Detail | Info |
|---|---|
| **Date** | August 1, 2012 |
| **System** | Knight Capital automated trading software |
| **Root Cause** | A deprecated software flag was reused in a new deployment, accidentally triggering old, unused trading code |
| **Loss** | $440 million |
| **Lives Lost** | None |

**What happened:** Knight Capital deployed a new trading software update to their servers — but one of their eight servers did not receive the update. On that server, an old, repurposed flag triggered an abandoned piece of code called "Power Peg," which began executing a strategy of buying high and selling low at enormous volume. The system was trading at a rate of 40 transactions per second, losing approximately $10 million per minute. By the time engineers identified the source and killed the process 45 minutes later, $440 million was gone. The firm was forced to seek emergency financing and ultimately merged with a competitor to survive.

**Lesson:** Deployment must be atomic and verified across all nodes. Dead code should be deleted, not dormant. Kill switches in financial systems are not optional.

---

### 2014 — Mt. Gox Bitcoin Exchange Collapse | *$460 Million in Lost Bitcoin*

| Detail | Info |
|---|---|
| **Date** | 2011–2014 |
| **System** | Mt. Gox Bitcoin exchange software |
| **Root Cause** | Transaction malleability bug — the exchange created transactions that could never be fully settled; combined with inadequate security leading to a major hack |
| **Loss** | ~$460 million+ in Bitcoin |
| **Lives Lost** | None |

**What happened:** Mt. Gox handled over 70% of all Bitcoin transactions at its peak. A software flaw allowed attackers to exploit transaction malleability — altering transaction IDs before they were confirmed — making the exchange think withdrawals had failed when they had not. Over time, 850,000 Bitcoin were lost. The exchange declared bankruptcy in 2014, erasing the holdings of hundreds of thousands of users.

**Lesson:** Cryptographic and financial protocols require extreme adversarial testing. Handling money means assuming every edge case will eventually be exploited.

---

### 2019 — Boeing 737 MAX MCAS Crashes | *346 Lives Lost*

| Detail | Info |
|---|---|
| **Date** | October 2018 & March 2019 |
| **System** | MCAS (Maneuvering Characteristics Augmentation System) flight control software |
| **Root Cause** | MCAS relied on a single angle-of-attack sensor with no redundancy. When that sensor failed, the software repeatedly pushed the plane's nose downward, overriding pilots. Pilots were not informed MCAS existed. |
| **Loss** | 346 lives; Boeing lost approximately $20 billion |
| **Lives Lost** | **346 people** across two crashes (Lion Air Flight 610 and Ethiopian Airlines Flight 302) |

**What happened:** Boeing added MCAS to the 737 MAX to compensate for the aerodynamic effects of heavier engines. The system was designed to automatically lower the nose of the aircraft when it detected a stall. But MCAS relied on input from a single sensor with no redundancy. When that sensor malfunctioned, MCAS repeatedly forced the nose down. Pilots, who had not been trained on MCAS and were not told it existed, could not overcome the system's repeated inputs. Two planes crashed within months of each other. The entire 737 MAX fleet was grounded for 20 months.

**Lesson:** Safety-critical systems must have redundancy and human override capability. Hiding safety-critical software from pilots is not a product decision — it is a moral failure.

---

##  Impact at a Glance

| Year | Incident | Financial Loss | Lives Lost |
|---|---|---|---|
| 1962 | Mariner 1 | ~$90M | 0 |
| 1983 | Soviet Nuclear False Alarm | Incalculable | Potentially billions (averted) |
| 1985 | Therac-25 | — | 6+ killed/maimed |
| 1987 | DHSS Rounding Error | ~£100M | 0 |
| 1994 | Intel Pentium FDIV | ~$475M | 0 |
| 1996 | Ariane 5 Explosion | ~$370M | 0 |
| 1999 | Mars Climate Orbiter | ~$125M | 0 |
| 2000 | Y2K Remediation | ~$300–600B | 0 (averted) |
| 2003 | Northeast Blackout | ~$6B | ~100 |
| 2012 | Knight Capital | ~$440M | 0 |
| 2014 | Mt. Gox Collapse | ~$460M | 0 |
| 2019 | Boeing 737 MAX | ~$20B+ | **346** |

---

##  Recurring Root Causes

Across every disaster in this archive, the same categories of failure appear again and again:

- **Untested assumptions** — code written for one context, deployed in another
- **Missing validation** — no checks on data types, units, or ranges
- **Race conditions** — timing-dependent bugs that only manifest under specific sequences
- **Silent failures** — systems that fail without raising an alarm
- **Ignored warnings** — engineers or operators who saw the warning signs and were overruled
- **Dead code in production** — old logic that was never deleted and was accidentally re-activated
- **Single points of failure** — critical systems with no redundancy

---

##  A Note for Coders

If you've made it this far, you already understand something many people don't: **software is not just text on a screen.**

Every function you write runs somewhere. Every edge case you skip will eventually be triggered. Every assumption you make will one day be violated. The code you write today will be maintained by someone else tomorrow — perhaps someone who doesn't have your context, your notes, or your intentions.

**Coding is a responsibility.**

Not in an abstract, philosophical sense — but in a concrete, immediate, human sense. The Therac-25 operators did not know they were in danger. The passengers on Flight 610 did not know MCAS existed. The millions of people who lost power in 2003 did not know that their grid's alarm system had silently stopped working.

They trusted the software. They trusted the engineers.

**Every bug is someone's problem. Many bugs are someone's tragedy.**

This does not mean you must be paralyzed by fear. It means you must write with intentionality. Test as if lives depend on it — because sometimes they do. Document as if the next person has never seen your code — because they haven't. Delete dead code. Validate your inputs. Ask what happens when your assumptions are wrong.

Engineering is not just about making things work. It is about making things fail safely.

The world is running on code. Make yours worthy of that trust.

---

## Contributing

Found a bug disaster that belongs in this archive? Open a pull request with:

- The incident name and date
- Root cause (technical, not just descriptive)
- Verified financial and human impact
- The lesson learned

Please cite sources. This is an educational archive — accuracy is everything.

---

##  References & Further Reading

- [List of Software Bugs — Wikipedia](https://en.wikipedia.org/wiki/List_of_software_bugs)
- [An Investigation of the Therac-25 Accidents — Nancy Leveson, MIT](http://sunnyday.mit.edu/papers/therac.pdf)
- [The Worst Computer Bugs in History — Bugsnag](https://www.bugsnag.com/blog/bug-day-ariane-5-disaster)
- [20 Famous Software Disasters — DevTopics](https://www.devtopics.com/20-famous-software-disasters/)
- [Knight Capital: How to Lose $440M in 45 Minutes](https://www.henricodolfing.com/2019/06/project-failure-case-study-knight-capital.html)

---

*"The first step in avoiding a trap is knowing it exists."*

**— The Bug Archive**
