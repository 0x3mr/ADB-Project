"""
Two-Phase Commit (2PC) Coordinator Simulator
=============================================
This program simulates how a distributed database coordinates a transaction
across multiple participant nodes using the Two-Phase Commit protocol.

Scenarios you can run:
    1. Happy path         - all participants vote YES, transaction commits
    2. One participant NO - one participant votes NO, transaction aborts
    3. Coordinator crash  - coordinator crashes between Phase 1 and Phase 2 (blocking)
    4. Participant crash  - a participant crashes during Phase 1 (treated as NO)
    5. Run all scenarios  - runs all four in order
"""

import time
import random


# ─────────────────────────────────────────────
#  LOGGING HELPER
# ─────────────────────────────────────────────

def log(source, message):
    """
    Prints a formatted log line showing who sent the message and what it says.

    Parameters:
        source  (str): The name of the node logging the message (e.g. "Coordinator", "Node-A")
        message (str): The message to display
    """
    print(f"  [{source}] {message}")


def section(title):
    """
    Prints a visible section divider with a title, used to separate simulation phases.

    Parameters:
        title (str): The label to display inside the divider
    """
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def pause():
    """
    Pauses execution briefly to make the simulation feel like real network communication.
    """
    time.sleep(0.4)


# ─────────────────────────────────────────────
#  PARTICIPANT NODE
# ─────────────────────────────────────────────

class Participant:
    """
    Represents a database node participating in a distributed transaction.

    Each participant can:
        - Receive a PREPARE request and vote YES or NO
        - Receive a COMMIT or ABORT decision and act on it
        - Simulate a crash (meaning it never responds)

    Parameters:
        name        (str):  The name of this node, e.g. "Node-A"
        will_vote   (str):  What this node will vote: "YES" or "NO"
        will_crash  (bool): If True, this node crashes and never responds
    """

    def __init__(self, name, will_vote="YES", will_crash=False):
        self.name = name
        self.will_vote = will_vote
        self.will_crash = will_crash

        # Tracks the node's current state throughout the protocol
        self.state = "IDLE"

    def prepare(self):
        """
        Phase 1: The coordinator asks this node if it is ready to commit.

        The node checks its own readiness (simulated here by will_vote).
        If it crashes, it returns None to signal no response.

        Returns:
            str or None: "YES", "NO", or None if the node crashed
        """
        pause()

        if self.will_crash:
            log(self.name, "CRASHED. No response sent.")
            self.state = "CRASHED"
            return None

        if self.will_vote == "YES":
            # Node is ready: it locks its resources and logs the prepare
            self.state = "PREPARED"
            log(self.name, "Checked constraints. Voted YES. Resources locked.")
            return "YES"
        else:
            # Node cannot commit: it rolls back immediately
            self.state = "ABORTED"
            log(self.name, "Cannot commit. Voted NO. Rolling back locally.")
            return "NO"

    def commit(self):
        """
        Phase 2 (success): The coordinator tells this node to finalize the transaction.

        The node applies its changes permanently and releases its locks.
        """
        pause()
        self.state = "COMMITTED"
        log(self.name, "Received COMMIT. Transaction applied. Locks released.")

    def abort(self):
        """
        Phase 2 (failure): The coordinator tells this node to undo the transaction.

        The node discards any prepared changes and releases its locks.
        """
        pause()
        self.state = "ABORTED"
        log(self.name, "Received ABORT. Changes discarded. Locks released.")


# ─────────────────────────────────────────────
#  COORDINATOR
# ─────────────────────────────────────────────

class Coordinator:
    """
    The coordinator manages the full Two-Phase Commit protocol.

    It contacts all participants in Phase 1 to collect votes,
    then makes a single global decision in Phase 2 based on those votes.

    Parameters:
        participants (list): A list of Participant objects involved in this transaction
        crash_after_prepare (bool): If True, the coordinator crashes after Phase 1
                                    before sending any Phase 2 messages (simulates blocking)
    """

    def __init__(self, participants, crash_after_prepare=False):
        self.participants = participants
        self.crash_after_prepare = crash_after_prepare
        self.state = "IDLE"

    def run(self):
        """
        Executes the full Two-Phase Commit protocol from start to finish.

        Phase 1: Send PREPARE to all participants, collect votes
        Phase 2: Send COMMIT if all voted YES, otherwise send ABORT
        """

        # ── PHASE 1: PREPARE ──────────────────────────────
        section("PHASE 1: PREPARE")
        log("Coordinator", "Sending PREPARE to all participants...")

        votes = {}

        for participant in self.participants:
            vote = participant.prepare()
            votes[participant.name] = vote

        # ── EVALUATE VOTES ────────────────────────────────
        section("VOTE RESULTS")

        all_yes = True

        for node_name, vote in votes.items():
            if vote is None:
                log("Coordinator", f"{node_name} did not respond (crash). Treating as NO.")
                all_yes = False
            elif vote == "NO":
                log("Coordinator", f"{node_name} voted NO.")
                all_yes = False
            else:
                log("Coordinator", f"{node_name} voted YES.")

        # ── SIMULATE COORDINATOR CRASH ────────────────────
        if self.crash_after_prepare:
            section("COORDINATOR CRASH")
            log("Coordinator", "CRASHED after Phase 1. Phase 2 never sent.")
            log("Coordinator", "All participants are now BLOCKED — holding locks, waiting forever.")
            self.state = "CRASHED"
            return

        # ── PHASE 2: COMMIT OR ABORT ──────────────────────
        section("PHASE 2: DECISION")

        if all_yes:
            # Every participant agreed — safe to commit globally
            log("Coordinator", "All votes YES. Writing COMMIT to log.")
            self.state = "COMMITTED"

            for participant in self.participants:
                if participant.state == "PREPARED":
                    participant.commit()
        else:
            # At least one participant said NO or crashed — must abort globally
            log("Coordinator", "Not all votes YES. Writing ABORT to log.")
            self.state = "ABORTED"

            for participant in self.participants:
                if participant.state == "PREPARED":
                    participant.abort()

        # ── FINAL SUMMARY ─────────────────────────────────
        section("FINAL STATE")

        for participant in self.participants:
            log(participant.name, f"Final state: {participant.state}")

        log("Coordinator", f"Final state: {self.state}")


# ─────────────────────────────────────────────
#  SCENARIOS
# ─────────────────────────────────────────────

def scenario_happy_path():
    """
    Scenario 1: All participants vote YES.
    Expected outcome: transaction commits successfully across all nodes.
    """
    print("\n★  SCENARIO 1: Happy Path — All Participants Vote YES")

    participants = [
        Participant("Node-A"),
        Participant("Node-B"),
        Participant("Node-C"),
    ]

    coordinator = Coordinator(participants)
    coordinator.run()


def scenario_one_votes_no():
    """
    Scenario 2: One participant votes NO.
    Expected outcome: coordinator aborts the transaction on all nodes.
    """
    print("\n★  SCENARIO 2: One Participant Votes NO")

    participants = [
        Participant("Node-A"),
        Participant("Node-B", will_vote="NO"),  # this node refuses
        Participant("Node-C"),
    ]

    coordinator = Coordinator(participants)
    coordinator.run()


def scenario_coordinator_crash():
    """
    Scenario 3: Coordinator crashes after Phase 1, before sending Phase 2.
    Expected outcome: participants are BLOCKED — they voted YES and are
    holding locks, but will never receive a commit or abort decision.
    This demonstrates the core weakness of 2PC.
    """
    print("\n★  SCENARIO 3: Coordinator Crashes After Phase 1 (Blocking)")

    participants = [
        Participant("Node-A"),
        Participant("Node-B"),
        Participant("Node-C"),
    ]

    coordinator = Coordinator(participants, crash_after_prepare=True)
    coordinator.run()


def scenario_participant_crash():
    """
    Scenario 4: One participant crashes during Phase 1 and never responds.
    Expected outcome: coordinator treats the silence as NO and aborts.
    """
    print("\n★  SCENARIO 4: Participant Crashes During Phase 1")

    participants = [
        Participant("Node-A"),
        Participant("Node-B", will_crash=True),  # this node crashes mid-prepare
        Participant("Node-C"),
    ]

    coordinator = Coordinator(participants)
    coordinator.run()


# ─────────────────────────────────────────────
#  MENU
# ─────────────────────────────────────────────

def main():
    """
    Entry point. Displays a menu and runs the chosen scenario(s).
    """

    print("=" * 50)
    print("  Two-Phase Commit (2PC) Simulator")
    print("=" * 50)
    print()
    print("  Choose a scenario to simulate:")
    print("  1. Happy path           (all vote YES, commits)")
    print("  2. One participant NO   (transaction aborts)")
    print("  3. Coordinator crash    (participants block)")
    print("  4. Participant crash    (treated as NO, aborts)")
    print("  5. Run all scenarios")
    print()

    choice = input("  Enter your choice (1-5): ").strip()

    if choice == "1":
        scenario_happy_path()
    elif choice == "2":
        scenario_one_votes_no()
    elif choice == "3":
        scenario_coordinator_crash()
    elif choice == "4":
        scenario_participant_crash()
    elif choice == "5":
        scenario_happy_path()
        scenario_one_votes_no()
        scenario_coordinator_crash()
        scenario_participant_crash()
    else:
        print("  Invalid choice. Please enter a number between 1 and 5.")


main()
