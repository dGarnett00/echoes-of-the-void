# 🌌 Echoes of the Void

```
  ███████╗ ██████╗██╗  ██╗ ██████╗ ███████╗███████╗
  ██╔════╝██╔════╝██║  ██║██╔═══██╗██╔════╝██╔════╝
  █████╗  ██║     ███████║██║   ██║█████╗  ███████╗
  ██╔══╝  ██║     ██╔══██║██║   ██║██╔══╝  ╚════██║
  ███████╗╚██████╗██║  ██║╚██████╔╝███████╗███████║
  ╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝

         ██████╗ ███████╗    ████████╗██╗  ██╗███████╗
         ██╔══██╗██╔════╝    ╚══██╔══╝██║  ██║██╔════╝
         ██║  ██║█████╗         ██║   ███████║█████╗
         ██║  ██║██╔══╝         ██║   ██╔══██║██╔══╝
         ██████╔╝██║            ██║   ██║  ██║███████╗
         ╚═════╝ ╚═╝            ╚═╝   ╚═╝  ╚═╝╚══════╝

            ██╗   ██╗ ██████╗ ██╗██████╗
            ██║   ██║██╔═══██╗██║██╔══██╗
            ██║   ██║██║   ██║██║██║  ██║
            ╚██╗ ██╔╝██║   ██║██║██║  ██║
             ╚████╔╝ ╚██████╔╝██║██████╔╝
              ╚═══╝   ╚═════╝ ╚═╝╚═════╝

  UNS Meridian · Year 2847 · Cycle Unknown
  "Not all who drift are lost."
```

A critically-thinking sci-fi survival text-based game built in Python.

---

## Overview

**Echoes of the Void** is a deeply immersive, text-based survival game set aboard
the *UNS Meridian*, a generation ship that has been adrift for 200 years after a
catastrophic FTL drive failure stranded it between galaxies. The player awakens
from cryosleep with fragmented memories, dwindling resources, a ship full of
mysteries, and an entity lurking in the void that *responds to human thought*.

Every decision demands **critical thinking** — resource management, moral
dilemmas, unreliable information, logic puzzles, and narrative consequences that
ripple across the entire game.

---

## Full Game Design Document

### Core Design Pillars

| Pillar | Description |
|---|---|
| **Critical Thinking Over Reflexes** | No decision is purely good or bad. Players must weigh incomplete information, question NPCs, and analyse the environment. |
| **Survival Pressure** | Oxygen, power, food, sanity, and trust are finite resources that decay each turn. Every action costs something. |
| **Sci-Fi Meets Literary Fiction** | Hard science fiction blended with psychological fiction — unreliable narration, philosophical dilemmas, identity. |
| **Emergent Narrative** | The story branches not by simple A/B choices, but by the *combination* of dozens of micro-decisions, resource states, and NPC relationships. |

### Setting & World-Building

**The Ship: UNS Meridian** — A 12-deck generation ship, 3.2 km long, originally
carrying 10,000 colonists:

- **Deck 1–3 (The Spine):** Command bridge, navigation, comms — severely damaged.
- **Deck 4–5 (The Lungs):** Hydroponics & atmospheric processors — partially functional.
- **Deck 6 (The Heart):** Fusion reactor core — running at 11% capacity.
- **Deck 7–8 (The Ribs):** Crew quarters & medical bay — home to ~130 survivors.
- **Deck 9 (The Stomach):** Cargo hold & fabrication lab — encrypted archives.
- **Deck 10 (The Marrow):** Cryogenic bay — where the player wakes.
- **Deck 11–12 (The Abyss):** Sealed off. Strange signals emanate from within.

**The Void Entity: "The Resonance"** — An extradimensional intelligence that exists
in the space between galaxies. It communicates through *probability*. When humans
think near it, it subtly alters outcomes. The ship's AI has been compromised by it.

### Core Systems

#### Resource Management
Five critical resources, tracked per cycle (1 cycle ≈ one turn):

| Resource | Start | Decay | Notes |
|---|---|---|---|
| **O₂** | 85% | −2%/cycle | Affected by life support power |
| **Power** | 60% | −1.5%/cycle | Distributed across subsystems |
| **Rations** | 50 units | −1/cycle | Depletion erodes trust |
| **Sanity** | 90% | Variable | Affects narration reliability |
| **Trust** | 50% | Variable | NPCs withhold info at low trust |

Resources are interconnected: low O₂ → accelerated sanity drain; low power →
cascading O₂ loss; depleted rations → trust collapse.

Power allocation system: 6 subsystems (life support, navigation, cryo-bay,
medical, comms, fabrication) compete for a shared pool.

#### Faction Dynamics

| Faction | Leader | Goal |
|---|---|---|
| **The Navigators** | Captain Adaeze Okonkwo | Power to engines. Will sacrifice cryosleepers. |
| **The Keepers** | Dr. Yuki Tanaka | Power to cryo-bay. Cannot accept pod shutdowns. |
| **The Listeners** | Silas Venn | Open sealed decks. Embrace the Resonance. |
| **The Ghosts** | "Razor" (informal) | Hoard resources. Pragmatic survivalists. |

No faction is entirely right or wrong. Every alliance has a cost.

#### The Information Paradox (Epistemic Gameplay)
- **Ship Logs:** Fragmented and partially corrupted. Cross-reference dates, authors, events.
- **NPC Testimonies:** Each NPC has biases, hidden agendas, incomplete knowledge.
- **CORA (Ship AI):** Partially compromised — gives subtly wrong information when corrupted.
- **Environmental Clues:** Scorch marks, blood stains, growth patterns tell a story.

#### Sanity System (Unreliable Narration)

| Level | Range | Effect |
|---|---|---|
| **High** | 80–100% | Clear, precise prose. CORA functions normally. |
| **Medium** | 40–79% | Occasional eerie injections. Subtle unreliability. |
| **Low** | 10–39% | Narrative actively misleads. Exits may be listed wrong. |
| **Critical** | 0–9% | The Resonance speaks. May reveal truths — or traps. |

#### Puzzles (Logic & Deduction)
1. **Atmospheric Processor Repair:** Three subsystems, three states each. CORA's suggestion is wrong.
2. **Archive Decryption:** Tri-split cipher key. One fragment is a forgery. Identify the fake.
3. **Reactor Diagnostic:** Bayesian reasoning — run tests to eliminate false hypotheses.
4. **The Saboteur Investigation:** Three suspects, contradictory evidence. Use `THEORIZE` then `CONFRONT`.

### Narrative Arc — Act I (30 Cycles)

**Cycles 1–5: Awakening**
Wake in cryo-bay, meet CORA, learn the situation, first resource allocation decision, meet Engineer Vasquez.

**Cycles 6–15: Discovery**
Explore Decks 8–9, meet faction leaders, first resource crisis (O₂ drop), discover ship logs hinting at FTL cause, first faction conflict.

**Cycles 16–25: Escalation**
Sabotage confirmed, investigation begins, Deck 6 reactor access, Resonance makes first contact, cascade failure requires triage.

**Cycles 26–30: Climax**
Evidence converges on saboteur, archive decryption reveals the FTL failure was deliberate, Captain Okonkwo demands a choice, signal from Decks 11–12.

### Endings Matrix (12+ Endings — Acts II & III)

| Ending | Description |
|---|---|
| **The Arrival** | Reach a habitable world. Outcome depends on choices. |
| **The Merge** | Resonance merges with ship AI. Utopia or dystopia by trust/sanity. |
| **The Lifeboat** | Small group survives. Who's aboard is the final moral test. |
| **The Loop** | Player discovers they've done this before. The Resonance is testing humanity. |
| **The Silence** | Everyone dies. Logs survive — what they say depends on the journey. |
| **The Unanswered** | Deliberately ambiguous. A final choice with insufficient information. |

### Critical Thinking Mechanics

| Mechanic | Tests |
|---|---|
| Power allocation | Optimization under constraints, opportunity cost |
| NPC triangulation | Source evaluation, bias detection |
| CORA reliability | Trust calibration, independent verification |
| Sanity trade-offs | Risk-reward analysis, metacognition |
| Faction diplomacy | Game theory, negotiation, moral reasoning |
| Environmental puzzles | Scientific method, logical deduction |
| Information archaeology | Pattern recognition, synthesis of fragmented data |
| Endgame commitment | Decision-making under deep uncertainty |

---

## Installation & Setup

For a quick, step-by-step run walkthrough (especially on Windows), see [RUNNING_THE_GAME.md](RUNNING_THE_GAME.md).

```bash
# Clone the repository
git clone https://github.com/dGarnett00/echoes-of-the-void.git
cd echoes-of-the-void

# Install dependencies
pip install -r requirements.txt

# Run the game
python run.py
```

### Requirements
- Python 3.8+
- `colorama` ≥ 0.4.6 (terminal colours)
- `pyyaml` ≥ 6.0 (save files and game data)
- `pytest` ≥ 7.0 (tests)

---

## Commands Reference

| Command | Description |
|---|---|
| `EXAMINE [target]` / `LOOK` | Inspect an object, person, or room |
| `MOVE [direction]` / `GO` | Move to an adjacent area |
| `TALK [NPC name]` | Speak with a crew member |
| `QUERY CORA "question"` | Ask the ship AI a question |
| `ALLOCATE [system] [%]` | Distribute power to subsystems |
| `USE [item]` | Use an item from your inventory |
| `REPAIR [target]` | Attempt to repair a damaged system |
| `THEORIZE [note]` | Record a theory on your theory board |
| `REST` | Rest to recover sanity (costs 1 cycle) |
| `CONFRONT [NPC name]` | Confront an NPC with evidence |
| `INVENTORY` / `INV` | Show your inventory and evidence |
| `STATUS` | Show resource status panel |
| `HELP` | Show the command reference |
| `SAVE [slot]` | Save game to slot 1–3 |
| `LOAD [slot]` | Load game from a save slot |
| `QUIT` / `EXIT` | Quit the game |

Direction shortcuts: `NORTH`, `SOUTH`, `EAST`, `WEST`, `UP`, `DOWN`

---

## Project Structure

```
echoes-of-the-void/
├── README.md                  # This file — full game design document
├── requirements.txt           # Dependencies
├── setup.py                   # Package setup
├── run.py                     # Entry point
├── src/
│   ├── __init__.py
│   ├── game.py                # Main game loop, cycle management
│   ├── parser.py              # Text command parser (verb-noun-modifier)
│   ├── player.py              # Player state: inventory, memories, theory board
│   ├── resources.py           # Resource management (O2, Power, Rations, Sanity, Trust)
│   ├── ship.py                # Ship model: decks, rooms, connections, states
│   ├── npcs.py                # NPC system: factions, relationships, dialogue
│   ├── cora.py                # Ship AI CORA — queries, reliability, Resonance corruption
│   ├── narrative.py           # Story engine: events, branching, act progression
│   ├── puzzles.py             # Puzzle/challenge system
│   ├── sanity.py              # Sanity system affecting narration reliability
│   ├── combat.py              # Light encounter system (decision-based)
│   ├── save_system.py         # Save/load game state to YAML
│   └── utils.py               # Text formatting, display helpers, typewriter effect
├── data/
│   ├── rooms.yaml             # Room definitions for all Act I areas
│   ├── npcs.yaml              # NPC definitions, dialogue trees, faction data
│   ├── items.yaml             # Items and their properties
│   ├── events.yaml            # Narrative events and triggers
│   ├── logs.yaml              # Ship logs (some authentic, some corrupted)
│   └── puzzles.yaml           # Puzzle definitions and solutions
└── tests/
    ├── __init__.py
    ├── test_parser.py          # Command parsing tests (36 tests)
    ├── test_resources.py       # Resource system tests (34 tests)
    └── test_game.py            # Integration tests (109 tests)
```

---

## Running Tests

```bash
pytest tests/ -v
```

All 179 tests should pass.

---

## Contributing

This project is an Act I prototype. Planned for future acts:
- Act II (Cycles 31–80): Faction escalation, Resonance grows stronger
- Act III (Cycles 81–120): Signal detected, multiple endings

Contributions welcome:
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Write tests for new systems
4. Submit a pull request

---

## License

MIT License — see LICENSE file for details.

---

*"Not all who drift are lost."*
