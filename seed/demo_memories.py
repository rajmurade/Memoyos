"""Demo seed data for MemoryOS.

Populates the existing ChromaDB store with 14 fictional organizational
memories (manufacturing company) so the app can be demoed immediately.
All organizations, machine IDs, and incidents are fictional.

Run (from the project root):

    .\\.venv\\Scripts\\python.exe seed/demo_memories.py          # insert / refresh demo memories
    .\\.venv\\Scripts\\python.exe seed/demo_memories.py --reset  # clear the store, then insert

Memory IDs are stable, so running repeatedly never creates duplicates.
The script is never invoked automatically by app.py.
"""

import argparse
import os
import sys

# Make `src` importable when this script is run directly from any directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.memory_service import Memory, get_service  # noqa: E402

DEMO_MEMORIES = [
    Memory(
        id="mem-demo-001",
        title="Hydraulic Press H-204 Overheating",
        author_role="Senior Maintenance Technician",
        category="Maintenance",
        situation=(
            "Press H-204 starts overheating after roughly four hours of continuous stamping, "
            "with the hydraulic oil temperature climbing toward the alarm threshold."
        ),
        experience=(
            "In previous repairs the root cause was almost always restricted hydraulic fluid "
            "circulation or clogged cooling filters, not the press components themselves. Checking "
            "the oil cooler first saved hours of unnecessary disassembly."
        ),
        recommendation=(
            "Before any major repair, check hydraulic fluid level, cooling filter condition, and "
            "circulation. Clean or replace the filter, confirm flow through the cooler, then re-check "
            "temperature under load."
        ),
        warnings=(
            "Do not keep operating the press if the temperature keeps rising rapidly; prolonged high "
            "oil temperature can damage pump seals and the accumulator."
        ),
        tags=["hydraulics", "h-204", "overheating", "maintenance"],
    ),
    Memory(
        id="mem-demo-002",
        title="Conveyor Belt C-17 Abnormal Vibration",
        author_role="Maintenance Technician II",
        category="Troubleshooting",
        situation=(
            "Conveyor belt C-17 vibrates noticeably at the tail end, most noticeably during loaded "
            "start-ups and when heavy product builds up toward the end of the line."
        ),
        experience=(
            "Repeating incidents traced the vibration to worn return idlers and a misaligned take-up "
            "pulley rather than a belt tracking problem. A seized idler bearing showed up as localized "
            "heat and a rhythmic thumping noise."
        ),
        recommendation=(
            "Inspect the return idlers and take-up pulley for wear and free rotation, check alignment "
            "with a straightedge, and replace any seized bearings. Re-tension the belt to manufacturer "
            "specification."
        ),
        warnings=(
            "Do not run the belt under full load while inspecting the tail section; lock out the drive "
            "before reaching into the idler zone."
        ),
        tags=["conveyor", "c-17", "vibration", "idlers", "troubleshooting"],
    ),
    Memory(
        id="mem-demo-003",
        title="CNC Machine M-12 Calibration Drift",
        author_role="Senior Machinist",
        category="Troubleshooting",
        situation=(
            "CNC machine M-12 produces parts with dimensional drift across the shift, with "
            "measurements shifting most on longer workpieces near the spindle."
        ),
        experience=(
            "Calibration drift was usually caused by thermal growth in the spindle housing and "
            "loose couplers on the ball screws after heavy cutting batches, not by the part program itself."
        ),
        recommendation=(
            "Run a calibration cycle with a test probe after warm-up, check ball-screw coupler torque, "
            "and update the machine's thermal compensation table."
        ),
        warnings=(
            "Do not adjust the part program to compensate for the drift; fixing the mechanics first "
            "keeps tolerances stable and predictable."
        ),
        tags=["cnc", "m-12", "calibration", "tolerance", "machining"],
    ),
    Memory(
        id="mem-demo-004",
        title="Compressor C-08 Pressure Drop",
        author_role="Facilities Technician",
        category="Maintenance",
        situation=(
            "Compressor C-08 loses pressure gradually during operation and now cycles far more often "
            "than normal, especially on hot afternoons."
        ),
        experience=(
            "Recurring pressure issues traced to worn check valves and failing gaskets around the "
            "aftercooler; some decline was also caused by a dirty intake filter placing extra stress "
            "on the unit."
        ),
        recommendation=(
            "Leak-test the discharge side, inspect and replace the check valve and gaskets, and clean "
            "or replace the intake filter before suspecting the compressor pump itself."
        ),
        warnings=(
            "Do not let the compressor run continuously while line pressure drops below the plant "
            "threshold; catch it early before the pump runs low on lubrication."
        ),
        tags=["compressor", "c-08", "pressure", "plant-air", "leak"],
    ),
    Memory(
        id="mem-demo-005",
        title="Coolant Contamination in CNC Line",
        author_role="Process Engineer",
        category="Process",
        situation=(
            "The CNC line's central coolant sump develops a foul odor and a milky, foamy appearance "
            "within weeks of a top-up, reducing tool life and surface finish."
        ),
        experience=(
            "Regular contamination was traced to tramp oil bleeding in from hydraulic units and "
            "bacterial growth in the stagnant corners of the sump; a wrong concentration was rarely "
            "the real problem."
        ),
        recommendation=(
            "Skim the tramp oil, clean and dose the sump with biocide, and verify coolant concentration "
            "with a refractometer. Schedule weekly aeration and dump the sump on a fixed cycle."
        ),
        warnings=(
            "Do not simply top up with concentrate; over-concentration causes skin irritation and "
            "foaming that spreads tramp oil across the whole line."
        ),
        tags=["coolant", "cnc", "contamination", "sump", "process"],
    ),
    Memory(
        id="mem-demo-006",
        title="Emergency Shutdown Procedure for Press Line",
        author_role="Safety Officer",
        category="Safety",
        situation=(
            "An emergency on the press line such as a burst hose, smoke, or operator injury requires a "
            "uniform shutdown response so the line stops predictably and safely."
        ),
        experience=(
            "Past incidents showed crews pulled inconsistent levers, and the line sometimes kept "
            "cycling through stored hydraulic energy after the main stop was pressed."
        ),
        recommendation=(
            "Hit the emergency stop, close the hydraulic isolation valve, and vent residual pressure "
            "in the accumulator before anyone approaches the tooling, then call the shift lead."
        ),
        warnings=(
            "Never reach into the die area after a stop until the pressure gauge reads zero and the "
            "accumulator has been isolated."
        ),
        tags=["safety", "press-line", "emergency", "lockout"],
    ),
    Memory(
        id="mem-demo-007",
        title="Motor Bearing Noise Before Failure",
        author_role="Vibration Analyst",
        category="Maintenance",
        situation=(
            "A 30 kW drive motor on pump P-09 starts emitting a low rumble that slowly grows into a "
            "whine, with a slight temperature increase at the non-drive end."
        ),
        experience=(
            "Listeners caught these motors at the bearing-wear stage; once the whine appeared, bearing "
            "failure usually followed within days unless the motor was uncoupled and inspected."
        ),
        recommendation=(
            "Uncouple the motor, listen at the non-drive end, check for axial play, and compare "
            "vibration readings with the belt removed. Replace the bearing set if grease is darkened "
            "or metal debris is present."
        ),
        warnings=(
            "Do not run the motor under load for 'one more week' once the whine starts; a seized "
            "bearing can wreck the stator and cost a full motor replacement."
        ),
        tags=["motor", "bearing", "vibration", "pump", "p-09"],
    ),
    Memory(
        id="mem-demo-008",
        title="Welding Equipment Overheating",
        author_role="Welding Supervisor",
        category="Equipment",
        situation=(
            "Mig welding machines on the fabrication line overheat near the end of second shift, and "
            "the thermal cutout trips more often in summer."
        ),
        experience=(
            "Dust-clogged cooling fans and undersized supply cables were the repeated causes; machines "
            "ran noticeably hotter whenever the duty cycle limit was ignored."
        ),
        recommendation=(
            "Blow out the cooling fans and vents, verify the supply cable gauge, and rotate machines "
            "to respect the duty cycle at the rated amperage."
        ),
        warnings=(
            "Do not bypass the thermal overload switch to finish a weld; it masks real overheating and "
            "can melt the liner."
        ),
        tags=["welding", "mig", "overheating", "fabrication"],
    ),
    Memory(
        id="mem-demo-009",
        title="Temperature Sensor Failure Diagnosis",
        author_role="Instrumentation Technician",
        category="Troubleshooting",
        situation=(
            "A temperature reading on the extrusion line suddenly reads erratically or pins at a fixed "
            "value while the process itself looks normal."
        ),
        experience=(
            "Most 'bad temperature' calls were failed RTD probes caused by broken leads and moisture "
            "in the junction boxes, not real process temperature changes."
        ),
        recommendation=(
            "Compare the reading to a handheld probe, check the junction box for moisture, and measure "
            "RTD resistance at the transmitter terminals before replacing the sensor."
        ),
        warnings=(
            "Do not trust an erratic reading for alarms; isolate the sensor loop before calibrating so "
            "the control logic cannot take spurious action."
        ),
        tags=["temperature", "sensor", "rtd", "extrusion", "diagnosis"],
    ),
    Memory(
        id="mem-demo-010",
        title="Preventive Maintenance Lesson from Repeated Motor Failures",
        author_role="Reliability Engineer",
        category="Process",
        situation=(
            "The plant replaced the same drive motor on the dryer fan three times in two years, each "
            "time after a bearing failure, and treated it as bad luck."
        ),
        experience=(
            "Reviewing the history revealed a misaligned V-belt drive and overtightened belts rather "
            "than the motor itself; once alignment and tension routines were added, the failures stopped."
        ),
        recommendation=(
            "On every motor replacement, check sheave alignment and belt tension, record run hours, and "
            "add the motor to the vibration route before restarting."
        ),
        warnings=(
            "Do not reinstall a motor without confirming belt alignment; misalignment transfers load to "
            "the bearings and repeats the failure cycle."
        ),
        tags=["preventive-maintenance", "motor", "belt-alignment", "reliability", "dryer"],
    ),
    Memory(
        id="mem-demo-011",
        title="Quick Restart After H-204 Overheating",
        author_role="Shift Operator",
        category="Operations",
        situation=(
            "Press H-204 trips on high oil temperature every few days; the alarm clears by itself once "
            "the oil cools down."
        ),
        experience=(
            "During day-to-day shifts, waiting out the cooldown and restarting has kept the line moving; "
            "the press has run normally again each time without a full inspection."
        ),
        recommendation=(
            "After H-204 overheats and the alarm clears, restart the press as soon as the oil temperature "
            "drops below the alarm threshold so production can continue."
        ),
        warnings="Do not attempt a restart while the temperature is still climbing.",
        tags=["hydraulics", "h-204", "overheating", "restart", "operations"],
    ),
    Memory(
        id="mem-demo-012",
        title="Inspect Cooling Before Restarting H-204",
        author_role="Senior Maintenance Technician",
        category="Maintenance",
        situation=(
            "After press H-204 trips on high oil temperature, some crews restart it immediately and the "
            "press re-trips soon after, or the pump seals fail within a few weeks."
        ),
        experience=(
            "Every recurrence traced back to a clogged cooling filter or restricted hydraulic circulation; "
            "restarting before checking simply repeats the same overheating fault."
        ),
        recommendation=(
            "Do NOT restart H-204 immediately after an overheating trip. Inspect the cooling filter and "
            "hydraulic fluid circulation first, and only restart once flow is confirmed and temperature "
            "is stable."
        ),
        warnings=(
            "Never restart the press immediately after a high-temperature shutdown without first "
            "confirming cooling circulation."
        ),
        tags=["hydraulics", "h-204", "overheating", "restart", "inspection", "maintenance"],
    ),
    Memory(
        id="mem-demo-013",
        title="Hydraulic Oil and Filter Change Cycle for H-204",
        author_role="Maintenance Technician II",
        category="Maintenance",
        situation=(
            "H-204's hydraulic oil samples show rising particle counts between scheduled changes, and the "
            "filter bypass indicator trips early."
        ),
        experience=(
            "Changing the hydraulic filter before the full oil-change interval and keeping temperature "
            "records reduces the number of H-204 heat-related trips."
        ),
        recommendation=(
            "Track filter bypass hours, replace the H-204 hydraulic filter quarterly or when the bypass "
            "indicator trips, and log oil temperature readings weekly."
        ),
        warnings="Do not wait for the full oil change to replace a clogged filter on H-204.",
        tags=["hydraulics", "h-204", "filter", "oil", "preventive-maintenance", "hydraulics"],
    ),
    Memory(
        id="mem-demo-014",
        title="Verifying Overheating Alarms Before Acting",
        author_role="Instrumentation Technician",
        category="Troubleshooting",
        situation=(
            "Operators report H-204 overheating; the gauge shows high oil temperature, but the process "
            "looks normal."
        ),
        experience=(
            "A failing RTD probe caused a false overheating trip on H-204; the real temperature was fine, "
            "mirroring earlier sensor failures on the extrusion line."
        ),
        recommendation=(
            "Before reacting to an overheating alarm on H-204, compare the reading with a handheld probe "
            "and check the RTD junction box for moisture, exactly as with the extrusion-line probes."
        ),
        warnings="Do not restart-and-run on a gauge reading alone; verify the sensor before assuming the press is really overheating.",
        tags=["h-204", "temperature", "sensor", "rtd", "overheating", "hydraulics"],
    ),
]

DEMO_QUERIES = [
    ("A", "Machine H-204 is overheating after several hours. What should I check first?", "mem-demo-001"),
    ("B", "The conveyor is vibrating more than usual. What should maintenance inspect?", "mem-demo-002"),
    ("C", "The compressor keeps losing pressure during operation. What should we investigate?", "mem-demo-004"),
    ("D", "A motor has started making unusual bearing noise. What does our previous experience suggest?", "mem-demo-007"),
    ("E", "What should I know before dealing with a CNC calibration problem?", "mem-demo-003"),
    ("F", "H-204 just tripped on high oil temperature. Should we restart it right away?", "mem-demo-012"),
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed MemoryOS with 14 fictional demo manufacturing memories."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear the ChromaDB store before inserting the demo memories.",
    )
    args = parser.parse_args()

    service = get_service()
    before = service.store.count()
    if args.reset:
        service.store.clear()
        print(f"Cleared store ({before} memories removed).")

    print("Seeding demo memories...")
    for memory in DEMO_MEMORIES:
        captured = service.capture_memory(memory)
        print(f"  + {captured.id} | {captured.title}")

    after = service.store.count()
    print(
        f"\nDone. {len(DEMO_MEMORIES)} demo memories inserted/refreshed; "
        f"store now holds {after} memory(ies)."
    )
    print("Demo memory IDs are stable, so re-running this script never creates duplicates.")
    if not args.reset:
        print("Tip: pass --reset to clear the store back to exactly the demo memories.")

    print("\nExample demo queries (top expected memory):")
    for label, query, memory_id in DEMO_QUERIES:
        expected = next(m.title for m in DEMO_MEMORIES if m.id == memory_id)
        print(f"  [{label}] {query}\n          -> {expected}")


if __name__ == "__main__":
    main()