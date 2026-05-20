"""
Build docs/data/events.json from:
  - Hardcoded keynote speakers (24 talks across 6 sessions, Tue–Thu)
  - Hardcoded panel sessions (6 panels, Tue–Thu)
  - Scraped workshops / tutorials (BeautifulSoup from the workshops table)

Usage:
    cd scrape && uv run python scrape_events.py
"""

# /// script
# requires-python = ">=3.11"
# dependencies = ["requests>=2.31", "beautifulsoup4>=4.12", "lxml>=5.0"]
# ///

import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# ── Hardcoded Keynote Data ────────────────────────────────────────────────────
# Source: https://2026.ieee-icra.org/program/keynote-sessions/
# All sessions in Hall A1 (Plenary)

KEYNOTES = [
    # ── Session 1: Tuesday 11:00-12:30 — Autonomous Vehicles & Navigation ──
    {
        "name": "Johannes Betz", "affiliation": "Technical University of Munich",
        "title": "Learning to Handle Autonomous Vehicles at the Limits – Lessons Learned from Real-World Autonomous Motorsport",
        "abstract": "Can an autonomous car drive faster than a human racecar driver? In this talk, we answer this question by presenting the methods and algorithms that enable an autonomous vehicle to operate at the physical limits of vehicle dynamics. Emphasis is placed on learning-based motion planning control strategies that enable robust decision-making under uncertainty and rapidly changing conditions. We display case studies from autonomous racing competitions, such as the Abu Dhabi Racing League, that illustrate how these approaches push vehicles to their performance boundaries while ensuring safety and reliability.",
        "session": 1,
    },
    {
        "name": "Michael Milford", "affiliation": "QUT Centre for Robotics",
        "title": "From Neuroscience to Autonomous Vehicle Navigation",
        "abstract": "For roboticists, nature is an amazing inspiration: animals, insects and even humans are capable of amazing feats that are currently far beyond the capabilities of robots. Over two decades, our research group has drawn inspiration from nature's best navigation systems to create high performance navigation systems for robots like autonomous vehicles. Our inspiration is twofold: we work with neuroscientists who study the neural mechanisms underpinning navigation in the brain, but also look at navigation behaviours, whether it be an ant moving over a sand dune or a Monarch butterfly travelling the globe.",
        "session": 1,
    },
    {
        "name": "Aniket Bera", "affiliation": "Purdue University",
        "title": "Toward Behaviorally-Intelligent Robots: Safe Navigation in Unstructured and Human-Centered Environments",
        "abstract": "Robots are increasingly expected to operate beyond structured settings and enter dynamic, uncertain, physically unstructured environments shaped by continuous human activity. In such settings, safe navigation is not merely a path-planning problem. It requires robots to perceive complex scenes, reason under uncertainty, anticipate human behavior, and adapt their actions in real time while maintaining reliability and safety. This talk presents a vision for behaviorally intelligent robots: embodied systems that do not simply react to obstacles but instead build computational models of motion, interaction, and risk to navigate effectively in unstructured and human-centered environments.",
        "session": 1,
    },
    {
        "name": "Hesheng Wang", "affiliation": "Global College, Shanghai Jiao Tong University",
        "title": "Learning to Navigate: From Scene Understanding to Decision Making",
        "abstract": "Robot navigation spans a range of interconnected problems, from static to dynamic environments, rigid to deformable modeling, reconstruction to generation, and perception to decision making. This talk provides a unified perspective on these components and outlines a forward-looking framework for next-generation navigation systems. We begin with a new paradigm for scene understanding that encompasses semantic mapping and end-to-end reconstruction, where large vision models and learned representations of the physical world enable scalable, high-fidelity, and generalizable scene representation.",
        "session": 1,
    },
    # ── Session 2: Tuesday 16:45-18:15 — Medical & Healthcare Robotics ──
    {
        "name": "Eric Diller", "affiliation": "Robotics Institute, University of Toronto",
        "title": "Using Magnetic Fields to Control Tiny Robots in the Gut and Brain",
        "abstract": "Millimeter-scale robots can enter small spaces in the body in a versatile and non-invasive manner, and promise medical applications in surgery, sensing, and intervention. Realizing functional machines at this scale requires a unique approach to robotic power, control, and sensing. In this talk, I will show how we use multiple tiny magnets embedded within the body of our robots to enable multiple-degree-of-freedom actuation, control and sensing without any physical connection, onboard power or computation.",
        "session": 2,
    },
    {
        "name": "Fanny Ficuciello", "affiliation": "University of Naples Federico II",
        "title": "From Bioinspired Design to Safe Control: Emerging Challenges in Medical Robotics",
        "abstract": "Healthcare is undergoing a profound transformation, driven by rapid technological advances. The convergence of artificial intelligence and robotics with medicine is opening new frontiers in patient care and treatment. The use of innovative materials and bio-inspired designs will underpin the next generation of robots. On the other hand, the use of soft and deformable structures complicates system modelling and control. Supervised autonomy aims to blend human expert knowledge with the precision of robotic systems.",
        "session": 2,
    },
    {
        "name": "Tiantian Xu", "affiliation": "Shenzhen Institutes of Advanced Technology (SIAT)",
        "title": "Magnetically Actuated Microrobots for Precision Medicine",
        "abstract": "Magnetically actuated microrobots can be remotely and wirelessly controlled via magnetic fields, enabling them to navigate complex and confined spaces that are otherwise inaccessible in the human body. This technology holds great promise for precision biomedical applications. The speaker will present a comprehensive research framework spanning from microscale to human-scale systems, including a human-scale magnetic actuation system enabling applications from targeted drug delivery at the micro/nanoscale to remote control of continuum interventional robots.",
        "session": 2,
    },
    {
        "name": "Haoyong Yu", "affiliation": "National University of Singapore (NUS)",
        "title": "Towards Wearable Robotics with better Portability, Safety, and Comfort",
        "abstract": "With the rapid population aging in many developed countries, wearable robotics, commonly known as exoskeleton robots, are believed to have wide applications in both industry and Healthcare. At NUS Biorobotics Lab, we are developing a series of wearable robotics for rehabilitation and worker assistance using a modular approach based on compliant actuation, cable drive mechanisms, wearable sensors and learning-based movement detection algorithms.",
        "session": 2,
    },
    # ── Session 3: Wednesday 11:00-12:30 — Robot Perception & Spatial AI ──
    {
        "name": "Ayoung Kim", "affiliation": "Seoul National University (SNU)",
        "title": "The Underdog Sensors: Are Robots Using Thermal and Radar Right?",
        "abstract": "Thermal cameras and radar are routinely dismissed in robotics as noisy, low-contrast, and hard to integrate. But the real bottleneck is methodology, not the sensors. This talk addresses thermal infrared head-on: we show that sensor-appropriate calibration, proper 14-bit tone mapping, and VLM-driven RGB-to-thermal translation collectively close the gap that has kept thermal out of mainstream perception pipelines. We then turn to radar, where direct Doppler velocity measurement offers underexploited advantages for state estimation.",
        "session": 3,
    },
    {
        "name": "Luca Carlone", "affiliation": "Massachusetts Institute of Technology (MIT)",
        "title": "Maps, Memory, and Tasks: Toward Spatial AI for the Next Generation of Robots",
        "abstract": "Robotics is at an inflection point. For decades, we have built systems that reconstruct the world with increasing geometric precision—yet true autonomy requires more than maps. In this talk, I will highlight three emerging directions that are reshaping how robots perceive, remember, and act: geometric foundation models, persistent memory systems, and task-driven perception. Together, these trends point toward a new paradigm: spatial AI systems that move beyond mapping to provide actionable understanding of the environment.",
        "session": 3,
    },
    {
        "name": "Maren Bennewitz", "affiliation": "University of Bonn",
        "title": "Advancing Service Robots Through Active Perception: Mapping and Object Search Under Occlusion",
        "abstract": "Active perception enables service robots to intelligently gather information about their environment by choosing promising viewpoints and performing targeted manipulation actions to cover the scene and remove occlusions. This talk presents active perception strategies for household and agricultural scenarios, including methods that enable robots to efficiently perceive objects in cluttered environments, map confined spaces with severe occlusions, and use temporal priors to enable more efficient perception.",
        "session": 3,
    },
    {
        "name": "Timothy Barfoot", "affiliation": "University of Toronto",
        "title": "Why Field Robotics Research Still Matters",
        "abstract": "Field robotics aims to tackle dull, dirty, and dangerous jobs in mining, agriculture, environmental monitoring, defence, industrial mobility, transportation, space exploration, and so on. What makes field robotics hard is that the operating environment can be extreme in terms of weather, lighting, and terrain; unstructured and unknown; and constraining in terms of mass, power, compute, and communications. Today, all eyes are on artificial intelligence and its hopeful transformation of robotics into 'physical AI', but field robotics research remains critical.",
        "session": 3,
    },
    # ── Session 4: Wednesday 16:45-18:15 — Manipulation, Humanoids, Embodied Design ──
    {
        "name": "Jeannette Bohg", "affiliation": "Stanford University",
        "title": "Do We Still Need Dexterous Hands?",
        "abstract": "With increasingly capable grippers and large-scale imitation learning, the case for dexterous manipulation is worth remaking. I will argue that multi-fingered hands remain essential, not as a technical curiosity, but as the foundation of versatile, high-throughput manipulation that grippers fundamentally cannot deliver. Recent advances in hardware and sim-to-real RL have brought us to a point where a single policy can perform zero-shot tool use across diverse objects and tasks without teleoperation or task-specific engineering.",
        "session": 4,
    },
    {
        "name": "Kento Kawaharazuka", "affiliation": "The University of Tokyo",
        "title": "At the Intersection of Biology and Machines: From Musculoskeletal to Wire-driven Robots",
        "abstract": "Recent advances in robotics have enabled a wide range of designs that span biological inspiration and machine-oriented principles. This keynote presents research on exploring this design space at the intersection of biology and machines, focusing on systems ranging from musculoskeletal humanoids to wire-driven robots. We have developed a series of musculoskeletal humanoids that replicate key aspects of human anatomy, including tendon-driven actuation and distributed compliance.",
        "session": 4,
    },
    {
        "name": "Nikos Tsagarakis", "affiliation": "Istituto Italiano di Tecnologia (IIT)",
        "title": "Modular Bodies and Recovery Capabilities: Building Robots for Unstructured Environments",
        "abstract": "Robots deployed in unstructured environments must operate under uncertainty, support interoperability across diverse tasks, and remain functional despite faults, impacts, and unpredictable conditions. This keynote presents the robot-development approach pursued by the Humanoids and Human-Centered Mechatronics Lab at IIT toward resilient and adaptable robotic systems. The central idea is that the robot body itself should not be seen only as a mechanical carrier of sensors and actuators, but as an active source of capability, robustness, and recovery.",
        "session": 4,
    },
    {
        "name": "Yuke Zhu", "affiliation": "UT-Austin",
        "title": "Building Generalist Humanoid Robots",
        "abstract": "In an era of rapid AI progress, leveraging accelerated computing and big data has unlocked new possibilities to develop generalist AI models. As AI systems like ChatGPT showcase remarkable performance in the digital realm, we are compelled to ask: Can we achieve similar breakthroughs in the physical world — to create generalist humanoid robots capable of performing everyday tasks? This talk presents data-centric research principles and approaches for building general-purpose robot autonomy in the open world.",
        "session": 4,
    },
    # ── Session 5: Thursday 11:00-12:30 — Robot Learning, Planning & Foundation Models ──
    {
        "name": "David Hsu", "affiliation": "National University of Singapore",
        "title": "Scalable Robot Decision Making in the Open World: Planning and Plan Prediction with LLMs",
        "abstract": "A hallmark of intelligence is the ability to do the right thing in myriad unfamiliar situations. Data-driven robot foundation models, with their vast common-sense knowledge, have blurred the boundary between the known and unknown world, dramatically expanding robot capabilities. In this talk, I will argue that the long-term goal of scalable, robust robot intelligence necessitates an integration of model-based planning and data-driven plan prediction, illustrated with work on robots generating and verifying hypotheses on the fly.",
        "session": 5,
    },
    {
        "name": "Stefanie Tellex", "affiliation": "Brown University",
        "title": "Towards Complex Language in Partially Observed Environments",
        "abstract": "Robots can act as a force multiplier for people, whether a robot assisting an astronaut with a repair on the ISS, a UAV taking flight over cities, or an autonomous vehicle driving through streets. Existing approaches use action-based representations that do not capture the goal-based meaning of a language expression and do not generalize to partially observed environments. This research creates autonomous robots that understand complex goal-based commands and execute them in partially observed, dynamic environments.",
        "session": 5,
    },
    {
        "name": "Noémie Jaquier", "affiliation": "KTH Royal Institute of Technology",
        "title": "Traveling the Robot Learning Manifold: A Tale of Geometries and Inductive Biases",
        "abstract": "Robot motions are fundamentally governed by non-Euclidean geometries. Robot state spaces are non-linear manifolds, various robotic variables exhibit distinct geometric characteristics, and data often resides in curved spaces. This talk explores how differential geometry — arising from data structure, physics, and prior knowledge — provides a rigorous framework to construct representations and learning algorithms that respect and exploit these natural geometries.",
        "session": 5,
    },
    {
        "name": "Paolo Robuffo Giordano", "affiliation": "IRISA Rennes",
        "title": "Intrinsic Robustness: A Journey from Control-Aware Planning to Robust Robot Learning",
        "abstract": "As robots transition from controlled labs to unpredictable environments, achieving reliable autonomy in spite of sensor noise, model inaccuracies, and disturbances remains a formidable challenge. This talk explores computationally tractable methods for real-world robustness using sensitivity-based metrics, starting with mobile robots (UAVs) and manipulator arms, extending to legged locomotion and multi-robot missions, and culminating in embedding robustness metrics directly into policy learning algorithms.",
        "session": 5,
    },
    # ── Session 6: Thursday 16:45-18:15 — Human-Robot Interaction ──
    {
        "name": "Julie A. Adams", "affiliation": "Oregon State University",
        "title": "Challenges in Adaptive Robot Teaming: Understanding Human Teammate Performance",
        "abstract": "Human teammates conducting tasks in complex harsh environments train together and adaptively respond to each other's performance, often based on subtle indirect cues. Future teaming with humans requires robots to be as seamless at understanding their teammates, which requires robots to assess their human teammate's performance to adapt appropriately. This talk focuses on developing robot intelligence to understand human's inherent performance factors based on human worn sensors amenable to physically challenging teaming domains.",
        "session": 6,
    },
    {
        "name": "Marcia O'Malley", "affiliation": "Rice University",
        "title": "Guiding with Touch: Wearable Haptics for Shaping Human–Robot Interaction",
        "abstract": "Despite major advances in sensing and autonomy, most robotic systems interacting with humans remain limited in how they influence human movement and learning. This work examines how wearable haptic interfaces enable physically embodied interaction, allowing robots to guide human motor behavior through touch. Body-conformal, multimodal wearable haptic systems encode information about movement quality, strategy, and performance, providing expressive, low-latency cues that shape motor adaptation without increasing cognitive load.",
        "session": 6,
    },
    {
        "name": "Tetsunari Inamura", "affiliation": "Tamagawa University",
        "title": "Engineering Human Agency and Self-Efficacy: The Next Frontier of Human-Robot Symbiosis",
        "abstract": "As assistive robotics transitions from laboratories to daily life, a critical paradox emerges: excessive robotic intervention often diminishes Human Agency — the fundamental sense of being the initiator of one's own actions. To achieve true symbiosis, robots must do more than compensate for physical deficits; they must be engineered to foster and maintain the user's self-efficacy. This talk traces a research trajectory from physical assistance to meta-cognitive empowerment.",
        "session": 6,
    },
    {
        "name": "Berk Calli", "affiliation": "Worcester Polytechnic Institute (WPI)",
        "title": "Overcoming Manipulation Challenges in Environmental Robotics through AI-based Solutions and Human-Robot Partnership",
        "abstract": "Robots have the potential to play a critical role in addressing pressing environmental and climate challenges by enabling new solutions and scaling existing ones. Most environmental robotics applications require operation in highly unstructured and demanding conditions, where variability, uncertainty, and complexity pose significant challenges. This talk presents practical robotic systems for environmental applications through robotic manipulation techniques, efficiently generating AI models, and leveraging human–robot partnership, focusing on robotic shipbreaking and waste sorting.",
        "session": 6,
    },
]

KEYNOTE_SESSION_META = {
    1: {"day": "Tuesday",   "time": "11:00-12:30", "theme": "Autonomous Vehicles & Navigation"},
    2: {"day": "Tuesday",   "time": "16:45-18:15", "theme": "Medical & Healthcare Robotics"},
    3: {"day": "Wednesday", "time": "11:00-12:30", "theme": "Robot Perception & Spatial AI"},
    4: {"day": "Wednesday", "time": "16:45-18:15", "theme": "Manipulation, Humanoids & Embodied Design"},
    5: {"day": "Thursday",  "time": "11:00-12:30", "theme": "Robot Learning, Planning & Foundation Models"},
    6: {"day": "Thursday",  "time": "16:45-18:15", "theme": "Human-Robot Interaction"},
}


def build_keynote_events() -> list[dict]:
    events = []
    session_counters: dict[int, int] = {}
    for spk in KEYNOTES:
        s = spk["session"]
        session_counters[s] = session_counters.get(s, 0) + 1
        meta = KEYNOTE_SESSION_META[s]
        events.append({
            "id": f"keynote-{s}-{session_counters[s]}",
            "type": "keynote",
            "title": spk["title"],
            "authors": [{"name": spk["name"], "affiliation": spk["affiliation"]}],
            "keywords": [],
            "abstract": spk["abstract"],
            "day": meta["day"],
            "time": meta["time"],
            "room": "Hall A1",
            "session_type": "Keynote Session",
            "session_id": f"keynote-sess-{s}",
            "session_title": meta["theme"],
        })
    return events


# ── Hardcoded Panel Data ──────────────────────────────────────────────────────
# Source: https://2026.ieee-icra.org/program/panels/  +  individual event pages
# All sessions in Hall A1

PANELS = [
    {
        "id": "panel-1",
        "title": "From Humanoid Robotics Research to Startup Creation: The Role of Public Funding",
        "day": "Tuesday", "time": "09:00-10:30",
        "abstract": "This panel examines how long-term, excellence-driven robotics research can translate into impactful industrial innovation, using the iCub project and its spinoff Generative Bionics, alongside Neura Robotics, as case studies comparing public funding versus venture capital models.",
        "authors": [
            {"name": "Giorgio Metta",        "affiliation": "Italian Institute of Technology"},
            {"name": "Cecile Huet",          "affiliation": "European Commission"},
            {"name": "Alin Albu-Schäffer",   "affiliation": "Technical University of Munich (TUM) / DLR"},
            {"name": "Marco Hutter",         "affiliation": "ETH Zurich"},
            {"name": "Anna Valente",         "affiliation": "SUPSI"},
            {"name": "Daniele Pucci",        "affiliation": "Generative Bionics"},
            {"name": "Serena Ivaldi",        "affiliation": "Inria"},
            {"name": "David Reger",          "affiliation": "Neura Robotics"},
        ],
    },
    {
        "id": "panel-2",
        "title": "Advancing Sustainability in Robotics: From Green Design to Real-World Impact",
        "day": "Tuesday", "time": "15:00-16:30",
        "abstract": "This panel discusses sustainable design principles and environmental impact considerations in robotics, covering topics from energy-efficient actuators to end-of-life robot disposal and the broader ecological footprint of robotic systems.",
        "authors": [],
    },
    {
        "id": "panel-3",
        "title": "Building Sustainable and Trustworthy AI for Automation",
        "day": "Wednesday", "time": "09:00-10:30",
        "abstract": "This panel brings together researchers and industry leaders to discuss the development of AI systems for automation that are both sustainable (in terms of energy and resource use) and trustworthy (in terms of safety, reliability, and transparency).",
        "authors": [],
    },
    {
        "id": "panel-4",
        "title": "Publish or Perish: Surviving the Paper Deluge – Is Peer Review Broken?",
        "day": "Wednesday", "time": "15:00-16:30",
        "abstract": "With the explosive growth in paper submissions to robotics venues, this panel addresses the challenges facing peer review: quality control, reviewer burden, the role of LLMs in reviewing, and whether the current system is sustainable for the robotics community.",
        "authors": [],
    },
    {
        "id": "panel-5",
        "title": "\"Robots for All\" in a Fragmented World: Competing Visions for Global Robotics",
        "day": "Thursday", "time": "09:00-10:30",
        "abstract": "This panel examines the geopolitical, economic, and ethical dimensions of making robotics globally accessible, discussing how competing national agendas, supply chain fragmentation, and differing regulatory frameworks shape the vision of universal robotic assistance.",
        "authors": [],
    },
    {
        "id": "panel-6",
        "title": "Return on Humanoid Investment",
        "day": "Thursday", "time": "15:00-16:30",
        "abstract": "With billions invested in humanoid robotics startups, this panel assesses the realistic timeline for commercial returns, discusses which applications are closest to deployment, and examines what technical and non-technical barriers remain.",
        "authors": [],
    },
]


def build_panel_events() -> list[dict]:
    return [
        {
            "id": p["id"],
            "type": "panel",
            "title": p["title"],
            "authors": p["authors"],
            "keywords": [],
            "abstract": p["abstract"],
            "day": p["day"],
            "time": p["time"],
            "room": "Hall A1",
            "session_type": "Panel",
            "session_id": p["id"],
            "session_title": p["title"],
        }
        for p in PANELS
    ]


# ── Workshops & Tutorials (scraped from table) ────────────────────────────────
BASE = "https://2026.ieee-icra.org"
_SLOT_MAP = {"MORNING": "09:00-12:30", "AFTERNOON": "14:00-17:30",
             "FULL DAY": "09:00-17:30", "FULL": "09:00-17:30"}


def scrape_workshops() -> list[dict]:
    url = BASE + "/workshops-and-tutorials/"
    print(f"  Fetching workshops … {url}")
    resp = requests.get(url, timeout=30, headers={"User-Agent": "ICRA26-digest/1.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    events: list[dict] = []
    counter = 0
    for table in soup.find_all("table", class_=re.compile(r"tablepress")):
        header = table.find("tr", class_="row-1")
        day = "Monday"
        if header:
            cols = header.find_all(["th", "td"])
            if len(cols) >= 4 and ("Friday" in cols[3].get_text() or "June 5" in cols[3].get_text()):
                day = "Friday"

        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 4:
                continue
            category = tds[0].get_text(strip=True)
            a_tag    = tds[1].find("a")
            title    = (a_tag or tds[1]).get_text(strip=True)
            ext_url  = a_tag.get("href", "") if a_tag else ""
            slot_raw = tds[3].get_text(strip=True).upper()
            time     = _SLOT_MAP.get(slot_raw, "09:00-17:30")
            room     = tds[4].get_text(strip=True) if len(tds) > 4 else ""
            if not title:
                continue
            counter += 1
            events.append({
                "id": f"ws-{day[:2].lower()}-{counter}",
                "type": "tutorial" if "tutorial" in category.lower() else "workshop",
                "title": title,
                "authors": [],
                "keywords": [],
                "abstract": "",
                "url": ext_url,
                "day": day,
                "time": time,
                "room": room,
                "session_type": f"{category.capitalize()} Session",
                "session_id": f"ws-{day[:2].lower()}-{counter}",
                "session_title": title,
            })
    return events


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    all_events: list[dict] = []

    print("Building keynote events (hardcoded)…")
    keynotes = build_keynote_events()
    print(f"  → {len(keynotes)} keynote talks")
    all_events.extend(keynotes)

    print("Building panel events (hardcoded)…")
    panels = build_panel_events()
    print(f"  → {len(panels)} panels")
    all_events.extend(panels)

    print("Scraping workshops & tutorials…")
    workshops = scrape_workshops()
    print(f"  → {len(workshops)} workshops/tutorials")
    all_events.extend(workshops)

    out_path = Path(__file__).parent.parent / "docs" / "data" / "events.json"
    out_path.write_text(json.dumps(all_events, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {len(all_events)} events → {out_path}")


if __name__ == "__main__":
    main()
