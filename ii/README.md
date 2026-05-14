**Two-Phase Commit (2PC) Simulator**

A simple Python simulation of the Two-Phase Commit protocol, demonstrating how a distributed database coordinates a transaction across multiple nodes.

---

**Requirements**

Python 3. No external libraries needed.

---

**How to Run**

```
python two_phase_commit.py
```

Then enter a number from 1 to 5 when prompted.

---

**Scenarios**

1. Happy path: all nodes vote YES, transaction commits
2. One participant votes NO: transaction aborts across all nodes
3. Coordinator crash: coordinator crashes after Phase 1, participants are left blocked holding locks indefinitely
4. Participant crash: a node crashes mid-prepare, coordinator treats it as NO and aborts
5. Run all scenarios in order

---

**What It Demonstrates**

- How Phase 1 (Prepare) collects votes before any commitment is made
- How Phase 2 (Commit/Abort) enforces a single global decision
- Why a coordinator crash between the two phases leaves participants permanently blocked, the core weakness of 2PC
- How crashes and NO votes trigger a safe global abort