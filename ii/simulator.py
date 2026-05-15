import time
import random

#Prints a formatted log line showing who sent the message and what it says
def log(source, message):
    print(f"  [{source}] {message}")

#A section divider with a title, used to separate simulation phases
def section(title):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")

#Pauses execution briefly to make the simulation feel like real network communication
def pause():
    time.sleep(0.4)



class Participant:
    """
    Represents a database node participating in a distributed transaction
    Each participant can:
        - Receive a PREPARE request and vote YES or NO
        - Receive a COMMIT or ABORT decision and act on it
        - Simulate a crash (meaning it never responds)
    """
    def __init__(self, name, will_vote="YES", will_crash=False):
        self.name = name
        self.will_vote = will_vote
        self.will_crash = will_crash
        self.state = "IDLE"

    def prepare(self):
        pause()
        if self.will_crash:
            log(self.name, "CRASHED. No response sent.")
            self.state = "CRASHED"
            return None

        if self.will_vote == "YES":
            self.state = "PREPARED"
            log(self.name, "Checked constraints. Voted YES. Resources locked")
            return "YES"
        else:
            self.state = "ABORTED"
            log(self.name, "Cannot commit. Voted NO. Rolling back locally")
            return "NO"

    def commit(self):
        pause()
        self.state = "COMMITTED"
        log(self.name, "Received COMMIT. Transaction applied. Locks released")

    def abort(self):
        pause()
        self.state = "ABORTED"
        log(self.name, "Received ABORT. Changes discarded. Locks released")


class Coordinator:
    """
    The coordinator manages the full Two-Phase Commit protocol.
    It contacts all participants in Phase 1 to collect votes,
    then makes a single global decision in Phase 2 based on those votes.
    """

    def __init__(self, participants, crash_after_prepare=False):
        self.participants = participants
        self.crash_after_prepare = crash_after_prepare
        self.state = "IDLE"

    def run(self):
        #Executes the full Two-Phase Commit protocol from start to finish.

        section("PHASE 1: PREPARE")
        log("Coordinator", "Sending PREPARE to all participants...")

        votes = {}

        for participant in self.participants:
            vote = participant.prepare()
            votes[participant.name] = vote

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

        if self.crash_after_prepare:
            section("COORDINATOR CRASH")
            log("Coordinator", "CRASHED after Phase 1. Phase 2 never sent.")
            log("Coordinator", "All participants are now BLOCKED — holding locks, waiting forever.")
            self.state = "CRASHED"
            return

        section("PHASE 2: DECISION")

        if all_yes:
            log("Coordinator", "All votes YES. Writing COMMIT to log.")
            self.state = "COMMITTED"

            for participant in self.participants:
                if participant.state == "PREPARED":
                    participant.commit()
        else:
            # At least one participant said NO or crashed
            log("Coordinator", "Not all votes YES. Writing ABORT to log.")
            self.state = "ABORTED"

            for participant in self.participants:
                if participant.state == "PREPARED":
                    participant.abort()

        section("FINAL STATE")

        for participant in self.participants:
            log(participant.name, f"Final state: {participant.state}")

        log("Coordinator", f"Final state: {self.state}")


#transaction commits successfully across all nodes
def scenario_happy_path():
    print("\n★  SCENARIO 1: Happy Path — All Participants Vote YES")

    participants = [
        Participant("Node-A"),
        Participant("Node-B"),
        Participant("Node-C"),
    ]

    coordinator = Coordinator(participants)
    coordinator.run()

#coordinator aborts the transaction on all nodes
def scenario_one_votes_no():
    print("\n★  SCENARIO 2: One Participant Votes NO")

    participants = [
        Participant("Node-A"),
        Participant("Node-B", will_vote="NO"),  # this node refuses
        Participant("Node-C"),
    ]

    coordinator = Coordinator(participants)
    coordinator.run()

#participants are BLOCKED - This demonstrates the core weakness of 2PC
def scenario_coordinator_crash():

    print("\n★  SCENARIO 3: Coordinator Crashes After Phase 1 (Blocking)")

    participants = [
        Participant("Node-A"),
        Participant("Node-B"),
        Participant("Node-C"),
    ]

    coordinator = Coordinator(participants, crash_after_prepare=True)
    coordinator.run()

#coordinator treats the silence as NO and aborts
def scenario_participant_crash():
    print("\n★  SCENARIO 4: Participant Crashes During Phase 1")

    participants = [
        Participant("Node-A"),
        Participant("Node-B", will_crash=True),  # this node crashes mid-prepare
        Participant("Node-C"),
    ]

    coordinator = Coordinator(participants)
    coordinator.run()



def main():
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
