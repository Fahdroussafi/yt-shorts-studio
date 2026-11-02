import random
import os
import re
import json
import time
from typing import Optional, List, Dict

NICHE_PROFILES = {
    "dark_psychology": {
        "id": "dark_psychology",
        "name": "Dark Psychology & Human Behavior",
        "rpm_range": "$0.18 - $0.35",
        "retention_rate": "62% - 75%",
        "voice_recommended": "en-US-ChristopherNeural",
        "description": "Named psychological techniques, body language dominance, deception detection, cognitive biases, and non-verbal power dynamics.",
        "outro_phrase": "Follow {brand_name} for psychological rules that put you five steps ahead.",
        "forbidden_terms": [
            "skincare", "serum", "cream", "moisturizer", "makeup", "beauty", "cosmetics",
            "dermatologist", "wrinkles", "robot factory", "drone swarm", "quantum computer",
            "fallout vault", "hand puppets"
        ],
        "hook_formulas": [
            "If you experience a sudden emergency in front of a crowd, looking at the people around you makes you seven times more likely to die...",
            "If a stranger approaches you in an everyday location and uses the word 'we,' your physical safety is in immediate danger...",
            "When someone falsely accuses you in front of a group, answering their first question makes everyone believe you are one hundred percent guilty...",
            "If you think someone is lying to your face, watching their eyes makes you fifty percent more likely to get fooled...",
            "When someone insults you disguised as a joke in front of others, laughing along triggers a subconscious status drop you cannot reverse...",
            "If you collapse in front of a crowd of one hundred people, you are five times more likely to die than in front of a single stranger..."
        ],
        "angles": [
            "The Disaster Crowd Freeze (Normalcy bias & social proof contagion causing paralysis)",
            "Forced Teaming Defense (Gavin de Becker predatory grooming counter in public)",
            "The Presupposition False Accusation Trap (Refusing bait questions that manufacture guilt)",
            "The Reverse Chronology Lie Collapse (Cognitive load deception detection that breaks fakes)",
            "The Schrodinger's Joke Counter (Neutralizing public humiliation disguised as humor)",
            "The Bystander Collapse Paradox (Why crowds watch people die and the exact command to break it)",
            "The Door-in-the-Face Technique (Extreme request concession trap and the 3-second refusal)",
            "The Gray Rock Technique (Neutralizing emotional predators without giving ammunition)",
            "Non-Verbal Dominance Cues (Eye stillness, posture gravity, and breaking intimidation)",
            "The Gaslighting Documentation Counter (Neutralizing distorted reality with cold facts)",
            "The 4-Second Silence Rule (Breaking high-pressure interrogation traps)",
            "Micro-Expressions Leakage (Detecting the 0.2-second facial twitch of hidden deception)",
            "The Silent Treatment Neutralization (Depriving emotional vampires of their leverage)"
        ],
        "visual_bank": [
            "dark-crowd", "subway-station", "cctv-camera", "eye-contact", "silhouette", "dark-room",
            "whisper", "mirror", "walking-alone", "dark-street", "chess", "rain-window", "stare",
            "tunnel", "city-night", "smoke", "interrogation-room", "dramatic-lighting", "emergency-light"
        ]
    },
    "dark_history": {
        "id": "dark_history",
        "name": "Dark History & Forbidden Experiments",
        "rpm_range": "$0.16 - $0.28",
        "retention_rate": "60% - 72%",
        "voice_recommended": "en-US-ChristopherNeural",
        "description": "Disturbing historical experiments, forbidden psychological tests, classified archives, and ancient societal anomalies.",
        "outro_phrase": "Follow {brand_name} for dark historical breakthroughs that shape our world.",
        "forbidden_terms": ["skincare", "serum", "cream", "makeup", "robot factory", "quantum encryption", "drone swarm"],
        "hook_formulas": [
            "If a voice on a telephone orders a hospital nurse to inject you with a lethal dose of medicine, ninety-five percent of them will push the syringe into your arm...",
            "If you check into an institution completely sane and speak normally, doctors will record your sanity as a symptom of severe paranoia...",
            "The forbidden 1939 study where researchers deliberately turned 22 normal orphan children into stutterers...",
            "The terrifying truth about what happens to normal human minds the moment they put on a guard uniform..."
        ],
        "angles": [
            "The Hofling Hospital Lethal Overdose Paradox (Why 21 of 22 nurses obeyed a lethal phone order)",
            "The Rosenhan Psychiatric Trap (How completely sane people were permanently labeled insane)",
            "The 1939 Monster Study (The forbidden stuttering experiment on 22 orphans)",
            "The Stanford Guard Syndrome (How ordinary students turned sadistic in 6 days)",
            "The 1951 Asch Conformity Test (Why 75% of people deny what their own eyes see)",
            "Operation Midnight Climax (Classified mind-alteration safehouses)"
        ],
        "visual_bank": [
            "vintage", "laboratory", "classroom", "whisper", "hallway", "ancient-book",
            "archive", "old-photo", "document", "candle", "cold-light", "silhouette",
            "forest", "night-camp", "fire", "smoke", "shadows", "corridor", "institution"
        ]
    },
    "frontier_tech": {
        "id": "frontier_tech",
        "name": "Humanoid Robotics & AI Future",
        "rpm_range": "$0.25 - $0.45",
        "retention_rate": "60% - 72%",
        "voice_recommended": "en-US-ChristopherNeural",
        "description": "Bipedal robot factories, autonomous surveillance, neural implants, technological singularity.",
        "outro_phrase": "Follow {brand_name} for the unseen technologies reshaping our future.",
        "forbidden_terms": ["skincare", "makeup", "serum", "cream", "ancient history", "pratfall effect"],
        "hook_formulas": [
            "Right now, the first factories run 100% by humanoid robots have officially gone live...",
            "Intelligence agencies have begun preparing for the [Tech Event] threshold...",
            "In five years, this single machine will permanently replace millions of jobs..."
        ],
        "angles": [
            "Autonomous AI Drone Swarms That Hunt Without GPS",
            "Quantum Encryption Collapse: The Death of All Passwords",
            "Dark Factories: Bipedal Humanoids Working 24/7 Without Lights",
            "Brain-Computer Interfaces: Reading Sub-Vocal Thoughts in Real Time",
            "Synthetic Biology: Self-Replicating Micro-Robots in Medicine"
        ],
        "visual_bank": [
            "drone", "night-sky", "military", "technology", "artificial-intelligence",
            "server", "matrix", "binary", "cyberpunk", "robot", "factory", "laser",
            "microchip", "futuristic-city", "hologram", "code", "neon"
        ]
    },
    "skincare_science": {
        "id": "skincare_science",
        "name": "Skincare Science & Formulation Secrets",
        "rpm_range": "$0.22 - $0.38",
        "retention_rate": "55% - 68%",
        "voice_recommended": "en-US-JennyNeural",
        "description": "Lipid barrier biochemistry, active ingredients, cosmetic chemistry, and drugstore dupes.",
        "outro_phrase": "Follow {brand_name} for verified skincare chemistry secrets.",
        "forbidden_terms": ["dark psychology", "manipulation", "drone swarm", "vault 77", "tribal warfare"],
        "hook_formulas": [
            "If your skin barrier is damaged, stop using [Product] immediately...",
            "Before spending $300 on luxury face cream, look at this $14 pharmacy formulation...",
            "The 30-second facial geometry test that tells you your real visual weight..."
        ],
        "angles": [
            "High vs Low Visual Weight: The 30-Second Face Test",
            "The $14 French Pharmacy Cream That Beats $380 Luxury Jars",
            "Why Niacinamide and Pure Vitamin C Shouldn't Be Layered Incorrectly",
            "The Transepidermal Water Loss Trick Every Dermatologist Uses",
            "Ceramides vs Hyaluronic Acid: Why Dry Climates Make Hyaluronic Backfire"
        ],
        "visual_bank": [
            "mirror", "face", "makeup", "luxury", "aesthetic", "cream", "serum",
            "clean", "skincare", "water-drop", "glass-bottle", "dropper", "glow"
        ]
    },
    "gaming_lore": {
        "id": "gaming_lore",
        "name": "Dark Gaming Lore & Iceberg Mysteries",
        "rpm_range": "$0.14 - $0.22",
        "retention_rate": "65% - 78%",
        "voice_recommended": "en-US-GuyNeural",
        "description": "Disturbing game lore, unsolved easter eggs, terrifying cut content, and deep iceberg theories.",
        "outro_phrase": "Follow {brand_name} for dark gaming lore and iceberg mysteries.",
        "forbidden_terms": ["skincare", "serum", "moisturizer", "makeup", "corporate persuasion"],
        "hook_formulas": [
            "Inside the wasteland of [Game], developers hid an experiment so dark it was censored...",
            "This is the creepiest unsolved mystery in [Game Name]...",
            "Players spent ten years trying to find this secret room, and what they found shocked everyone..."
        ],
        "angles": [
            "The Darkest Vault in Fallout History: Vault 77",
            "The Lavender Town Audio Mystery: Frequencies That Disturbed Players",
            "The Mount Chiliad Mystery in GTA V: What Rockstar Never Explained",
            "PT Silent Hills: The Terrifying Phantom That Still Haunts Players",
            "Subnautica: The Dead Zone and Why Deep Ocean Horrors Break Sanity"
        ],
        "visual_bank": [
            "dark-room", "puppet", "shadows", "gaming", "neon", "cyberpunk",
            "console", "controller", "screen-glow", "mysterious-room", "fog", "arcade"
        ]
    }
}

CONCEPTS_DATABASE = {
    "dark_psychology": [
        {
            "title": "The Disturbing Cognitive Glitch That Forces People to Obey You #shorts #darkpsychology",
            "script": (
                "If you suspect someone secretly despises you, never try to be nice to them. Do this instead. "
                "Ask them for something trivially small: borrow a pen, ask for the time, or request a quick opinion. "
                "In psychology, this triggers the Ben Franklin Effect. "
                "The human brain cannot tolerate cognitive dissonance. Once someone helps you, their subconscious is forced to rationalize: 'I must like this person, otherwise why would I do them a favor?' "
                "Without realizing it, their brain rewires their attitude and begins treating you like a trusted ally. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["thinking", "eye-contact", "notebook", "shadows", "meeting"],
            "description": "How asking for a small favor hacks subconscious compliance.\n\nSubscribe to @ShadowMind.\n\n#darkpsychology #psychologyfacts #mindset #manipulation #shorts",
            "pinned_comment": "Have you ever seen this compliance trigger work on someone? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "Why Flawless People Are Secretly Feared and Disliked #shorts #darkpsychology",
            "script": (
                "If you try to appear completely flawless, people will secretly resent and distrust you. "
                "In behavioral psychology, this is known as the Pratfall Effect. "
                "When an authority figure makes a minor, harmless blunder—like spilling a drop of coffee or dropping a pen—their perceived likability spikes by over forty percent. "
                "Perfection creates an intimidating wall of inferiority. A deliberate, controlled vulnerability humanizes you and instantly disarms their defenses. "
                "Never pretend to be superhuman. Show a minor flaw, and they will surrender their trust to you completely. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["coffee", "hands", "walking", "dark-room", "silhouette"],
            "description": "Why small tactical flaws spike your influence and disarm enemies.\n\nSubscribe to @ShadowMind.\n\n#pratfalleffect #darkpsychology #charisma #confidence #shorts",
            "pinned_comment": "Do you trust people who pretend to have zero flaws? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The 4-Second Silence Rule That Destroys Disrespect #shorts #darkpsychology",
            "script": (
                "When someone tries to humiliate or intimidate you in public, never shout and never defend yourself. Use the four-second silence rule. "
                "Immediately freeze your face. Look directly into the center of their forehead with zero emotion for exactly four seconds. "
                "In social psychology, rapid defense signals weakness, while dead unbroken silence signals absolute dominance. "
                "After four seconds pass, quietly ask: 'Are you okay?' "
                "This instantly shifts the social embarrassment onto them and exposes their insecurity to the entire room. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["dark-street", "stare", "shadows", "crowd", "clock"],
            "description": "How 4 seconds of unbroken dead silence destroys disrespect.\n\nSubscribe to @ShadowMind.\n\n#stoicism #darkpsychology #bodylanguage #comeback #shorts",
            "pinned_comment": "Would you have the discipline to hold 4 seconds of silence? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The Door-in-the-Face Trap: How Manipulators Force Compliance #shorts #darkpsychology",
            "script": (
                "If someone asks you for an absurdly massive favor and then immediately lowers their request, watch out. You are being manipulated. "
                "This is the Door-in-the-Face Technique, one of the most dangerous compliance traps in behavioral science. "
                "When you reject their initial extreme demand, your brain experiences subconscious social guilt. "
                "When they immediately offer a smaller concession, your brain falsely interprets it as a gift, making you three times more likely to say yes to what they actually wanted all along. "
                "Master negotiators use this daily to control high-stakes decisions. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["door", "business", "handshake", "night", "thinking"],
            "description": "Why reject-then-retreat hacks your subconscious guilt.\n\nSubscribe to @ShadowMind.\n\n#persuasion #darkpsychology #negotiation #mindset #shorts",
            "pinned_comment": "Has anyone ever pulled this trick on you? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The Micro-Agreement Trap: How Cults and Manipulators Trap You #shorts #darkpsychology",
            "script": (
                "If someone gets you to agree to a tiny, meaningless favor, you are already walking into their trap. "
                "In psychology, this is the Foot-in-the-Door Phenomenon, used by interrogators and cult recruiters. "
                "Once you say yes to a trivial micro-action—like signing a simple petition or wearing a pin—your self-image shifts into someone who complies. "
                "Days later, when they hit you with a massive, life-altering demand, your brain complies simply to remain consistent with your past actions. "
                "Guard your small yeses, or someone else will dictate your big decisions. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["signature", "hands", "crowd", "shadows", "document"],
            "description": "How tiny micro-commitments lead to total behavioral control.\n\nSubscribe to @ShadowMind.\n\n#footinthedoor #darkpsychology #compliance #shorts",
            "pinned_comment": "Have you noticed yourself saying yes just to be agreeable? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The Spotlight Effect: The Truth About What People Think of You #shorts #psychology",
            "script": (
                "You spend your entire life worrying about what other people are thinking of your mistakes, clothes, and awkward words. The psychological reality is: they aren't thinking of you at all. "
                "In cognitive science, this is known as the Spotlight Effect. "
                "In rigorous laboratory experiments, participants were forced to wear painfully embarrassing t-shirts into crowded rooms. "
                "The wearers believed at least fifty percent of people noticed. The reality? Less than twenty-three percent ever glanced up. "
                "Everyone is trapped inside their own mental spotlight, obsessing over themselves. You are free. Act like it. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["crowd", "mirror", "walking-alone", "dark-street", "city-night"],
            "description": "Why nobody is watching you as closely as you think.\n\nSubscribe to @ShadowMind.\n\n#spotlighteffect #socialanxiety #confidence #mindset #shorts",
            "pinned_comment": "Has the fear of being watched ever held you back from a bold move? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The Zeigarnik Effect: How Incomplete Tasks Torture Your Brain #shorts #psychology",
            "script": (
                "Have you ever wondered why you can forget a completed project instantly, but an unfinished chore keeps you awake at three in the morning? "
                "This is the Zeigarnik Effect. "
                "In 1927, a psychologist observed that waiters remembered complex unpaid orders with flawless precision, but wiped their memory clean the second the bill was settled. "
                "Your subconscious mind allocates continuous cognitive tension to unclosed loops until they are finished. "
                "To conquer debilitating procrastination, don't try to finish a massive task. Simply start it for two minutes. Once the loop is open, your brain will compel you to close it. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["clock", "hourglass", "writing", "thinking", "candle"],
            "description": "Why unfinished tasks haunt your subconscious mind and how to weaponize it.\n\nSubscribe to @ShadowMind.\n\n#zeigarnikeffect #productivity #focus #psychology #shorts",
            "pinned_comment": "What open loop is keeping your brain awake tonight? Comment below. 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The Decoy Effect: How Menus and Companies Force Your Choices #shorts #psychology",
            "script": (
                "When you look at a menu with small, medium, and large popcorn, the medium option is not meant to be sold. It is an intentional trap designed to extract your money. "
                "In behavioral economics, this is known as Asymmetric Dominance or the Decoy Effect. "
                "If small is three dollars and large is seven, most buyers choose small. "
                "But when a decoy medium is introduced at six dollars and fifty cents, buying large feels like an irresistible bargain, and large sales surge by over sixty percent. "
                "Whenever an option exists that seems irrationally priced, you are not choosing. You are being steered. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["chess", "meeting-room", "handshake", "thinking", "silhouette"],
            "description": "How the Decoy Effect forces you to buy what companies want.\n\nSubscribe to @ShadowMind.\n\n#decoyeffect #behavioraleconomics #mindset #persuasion #shorts",
            "pinned_comment": "Do you always fall for the largest size? Be honest. 👇",
            "voice": "en-US-ChristopherNeural"
        }
    ],
    "dark_history": [
        {
            "title": "The 1951 Asch Conformity Test: How Truth Is Crushed #shorts #darkhistory",
            "script": (
                "In 1951, a psychologist proved that seventy-five percent of human beings will openly lie about what their own eyes see just to fit into a group. "
                "This was the Asch Conformity Experiment. "
                "A participant was placed in a room with seven actors. They were shown two cards with lines of visibly different lengths. "
                "One by one, every actor confidently gave an obviously incorrect answer. "
                "Over three-quarters of normal people abandoned their own senses and agreed with the lie rather than risk standing alone. "
                "Never assume the majority is right. The human fear of exclusion is stronger than the pursuit of truth. "
                "Follow ShadowMind for dark historical breakthroughs that shape our world."
            ),
            "keywords": ["vintage", "laboratory", "classroom", "shadows", "crowd"],
            "description": "The terrifying 1951 study proving most people will deny reality to fit in.\n\nSubscribe to @ShadowMind.\n\n#darkhistory #conformity #psychologyexperiments #mindset #shorts",
            "pinned_comment": "Would you speak the truth if 7 people before you lied? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The 1968 Blue Eyes Brown Eyes Experiment #shorts #darkhistory",
            "script": (
                "In 1968, an elementary school teacher divided her classroom into two groups: children with blue eyes and children with brown eyes. "
                "She announced that blue-eyed children were scientifically superior, granting them extra privileges while labeling brown-eyed children as lazy and unintelligent. "
                "Within a single morning, sweet third-graders transformed into vicious, arrogant bullies, while the brown-eyed children scored lower on tests and wept in distress. "
                "The next day, she reversed the labels, and the exact same cruelty occurred in reverse. "
                "Cruelty is not born in human nature. It is programmed by artificial division. "
                "Follow ShadowMind for dark historical breakthroughs that shape our world."
            ),
            "keywords": ["classroom", "children", "vintage", "whisper", "hallway"],
            "description": "How a teacher turned third graders into ruthless bullies in 24 hours.\n\nSubscribe to @ShadowMind.\n\n#darkhistory #psychology #historyfacts #humanbehavior #shorts",
            "pinned_comment": "How quickly do you think modern society could be divided like this? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The Robbers Cave Experiment: Manufacturing Tribal Warfare #shorts #darkhistory",
            "script": (
                "In 1954, researchers took twenty-two ordinary eleven-year-old boys to a summer camp and created a private civil war in less than one week. "
                "They called it the Robbers Cave Experiment. "
                "The boys were split into two teams, unaware of each other's existence. Once groups formed their own identities, researchers introduced competitive tournaments with prizes. "
                "Within forty-eight hours, the boys burned each other's team flags, raided cabins with weapons, and refused to eat in the same hall. "
                "Conflict between humans doesn't require deep hatred. It only requires competition and a name. "
                "Follow ShadowMind for dark historical breakthroughs that shape our world."
            ),
            "keywords": ["forest", "night-camp", "fire", "smoke", "silhouette"],
            "description": "The disturbing 1954 study that created real tribal warfare in 7 days.\n\nSubscribe to @ShadowMind.\n\n#darkhistory #robberscave #psychologyexperiments #humanbehavior #shorts",
            "pinned_comment": "Is tribalism hardwired into human DNA? Comment below. 👇",
            "voice": "en-US-ChristopherNeural"
        }
    ],
    "frontier_tech": [
        {
            "title": "The Autonomous AI Drone Swarms That Hunt Without GPS #shorts #technology",
            "script": (
                "Military contractors have officially deployed autonomous drone swarms that operate without satellite signals or human pilots. "
                "Equipped with decentralized edge AI vision, hundreds of miniature quadcopters communicate with each other like a school of piranhas. "
                "If fifty drones are shot down, the remaining machines automatically recalculate attack trajectories and divide target coordinates in real-time. "
                "Because they rely on localized optical landmarks rather than GPS, electronic jamming frequencies are completely useless against them. "
                "The era of human soldiers deciding the front line has quietly come to an end. "
                "Follow ShadowMind for the unseen technologies reshaping our future."
            ),
            "keywords": ["drone", "night-sky", "military", "technology", "artificial-intelligence"],
            "description": "Decentralized drone flocks that hunt autonomously with zero GPS.\n\nSubscribe to @ShadowMind.\n\n#drones #ai #futuretech #militarytech #robotics #shorts",
            "pinned_comment": "Can human laws keep up with autonomous warfare? Drop your thoughts. 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "Quantum Encryption Collapse: The Death of All Passwords #shorts #technology",
            "script": (
                "Right now, intelligence agencies around the world are intercepting and storing millions of terabytes of encrypted civilian data. "
                "They call this strategy 'Harvest Now, Decrypt Later.' "
                "Even though modern 256-bit encryption would take a standard supercomputer trillions of years to break, quantum computers will dissolve these algorithms in less than four minutes. "
                "Every banking password, medical history record, and private conversation you have ever sent is already archived, waiting for the quantum threshold. "
                "When the key turns, privacy as humanity knows it permanently vanishes. "
                "Follow ShadowMind for the unseen technologies reshaping our future."
            ),
            "keywords": ["server", "matrix", "binary", "cyberpunk", "lock"],
            "description": "Why intelligence agencies are saving encrypted data today for quantum computers.\n\nSubscribe to @ShadowMind.\n\n#quantum #cybersecurity #darkweb #futuretech #shorts",
            "pinned_comment": "Do you believe any digital data is truly private? Comment below. 👇",
            "voice": "en-US-ChristopherNeural"
        }
    ],
    "skincare_science": [
        {
            "title": "High vs Low Visual Weight: The 30-Second Face Test #shorts #beauty",
            "script": (
                "If your makeup always looks cakey or overpowering, you might be wearing the complete wrong visual weight for your facial structure. "
                "To find your visual weight, look in the mirror. High visual weight faces have prominent, defined bone structure, large eyes, or intense lip borders. "
                "Low visual weight faces have softer, delicate, and evenly dispersed facial contours. "
                "If you have high visual weight, bold winged eyeliner and deep lip colors harmonize your proportions. "
                "If you have low visual weight, heavy glam overpowers you, and soft watercolor tints make you look ethereal. "
                "Follow ShadowMind for verified skincare chemistry secrets."
            ),
            "keywords": ["mirror", "face", "makeup", "luxury", "aesthetic"],
            "description": "Find your visual weight in 30 seconds to never look over-done again.\n\n#visualweight #beautyhacks #glowup #makeuptips #shorts",
            "pinned_comment": "Are you high visual weight or low visual weight? Comment below! 👇",
            "voice": "en-US-JennyNeural"
        },
        {
            "title": "The $14 French Pharmacy Cream That Beats $380 Luxury Jars #shorts #beauty",
            "script": (
                "Before spending three hundred dollars on luxury face crèmes with gold leaf packaging, you need to understand cosmetic formulation. "
                "Most prestige moisturizers spend eighty percent of their budget on bespoke jars, celebrity endorsements, and fragrance additives. "
                "Behind the counter in French pharmacies, dermatologist-grade barrier creams containing pure beeswax, soy protein, and shea butter cost less than fourteen dollars. "
                "Celebrity makeup artists keep tubes of Embryolisse and Biafine in their kits because they prep skin without pill-forming silicone barriers. "
                "Stop paying for marketing luxury. Pay for lipid barrier science. "
                "Follow ShadowMind for verified skincare chemistry secrets."
            ),
            "keywords": ["cream", "serum", "clean", "skincare", "luxury"],
            "description": "Why runway makeup artists use $14 French pharmacy creams instead of luxury jars.\n\n#skincare #dupes #beautysecrets #frenchpharmacy #shorts",
            "pinned_comment": "What is your holy grail skincare budget product? Tell us below. 👇",
            "voice": "en-US-JennyNeural"
        }
    ],
    "gaming_lore": [
        {
            "title": "The Darkest Vault in Fallout History: Vault 77 #shorts #gaming",
            "script": (
                "Inside the radioactive wasteland of Fallout, Vault-Tec designed dozens of inhumane social experiments, but none were as disturbing as Vault 77. "
                "While other vaults held hundreds of residents, Vault 77 was sealed with only one single man and a crate full of hand puppets. "
                "For months, the solitary inhabitant slowly descended into severe psychosis, speaking through the puppets to preserve his sanity. "
                "Eventually, the man came to believe the puppet on his hand was an autonomous living demon demanding blood sacrifices. "
                "When the vault finally unsealed, the Puppet Man wandered into the wastes as one of the most feared legends in lore. "
                "Follow ShadowMind for dark gaming lore and iceberg mysteries."
            ),
            "keywords": ["dark-room", "puppet", "shadows", "gaming", "neon"],
            "description": "The terrifying story of Vault 77: One man and a crate of puppets.\n\nSubscribe to @ShadowMind.\n\n#fallout #gaminglore #creepygaming #iceberg #shorts",
            "pinned_comment": "What is the creepiest vault experiment in Fallout history? Comment below. 👇",
            "voice": "en-US-GuyNeural"
        }
    ]
}

def load_topic_history(history_file: Optional[str]) -> List[dict]:
    if not history_file or not os.path.exists(history_file):
        return []
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def record_topic_history(history_file: Optional[str], title: str, niche: str, angle: str = ""):
    if not history_file:
        return
    try:
        history = load_topic_history(history_file)
        history.insert(0, {
            "title": title,
            "niche": niche,
            "angle": angle,
            "timestamp": time.time()
        })
        history = history[:200]
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Failed to save topic history: {e}")

def get_random_niche_angle(niche: str, history_file: Optional[str] = None) -> str:
    profile = NICHE_PROFILES.get(niche, NICHE_PROFILES["dark_psychology"])
    angles = profile.get("angles", [])
    if not angles:
        return "psychological rules of human behavior"

    history = load_topic_history(history_file)
    recent_titles = " ".join([h.get("title", "").lower() + " " + h.get("angle", "").lower() for h in history[:30]])

    # Filter out recently used angles
    fresh_angles = [a for a in angles if not any(w in recent_titles for w in re.findall(r'\b[a-zA-Z]{5,}\b', a.lower())[:3])]
    if fresh_angles:
        return random.choice(fresh_angles)
    return random.choice(angles)

def pick_concept_without_repeats(niche: str, history_file: Optional[str] = None, brand_name: str = "ShadowMind", brand_handle: Optional[str] = None) -> dict:
    pool = CONCEPTS_DATABASE.get(niche, CONCEPTS_DATABASE["dark_psychology"])
    history = load_topic_history(history_file)
    recent_titles = [h.get("title", "").lower() for h in history[:30]]

    unused = [c for c in pool if c["title"].lower() not in recent_titles]
    chosen = random.choice(unused if unused else pool).copy()
    return customize_concept_for_brand(chosen, brand_name, brand_handle)

def customize_concept_for_brand(concept: dict, brand_name: str = "ShadowMind", brand_handle: str = None) -> dict:
    if not brand_handle:
        brand_handle = f"@{brand_name}" if not brand_name.startswith("@") else brand_name
    c = concept.copy()
    if brand_name.lower() != "shadowmind":
        for k in ["title", "script", "description", "pinned_comment"]:
            if k in c and isinstance(c[k], str):
                val = c[k]
                val = re.sub(r'(?i)\btheshadowmindhq(?:-hub)?\b', brand_handle.lstrip("@"), val)
                val = re.sub(r'(?i)@ShadowMind\b', brand_handle, val)
                val = re.sub(r'(?i)\bShadowMind\b', brand_name, val)
                c[k] = val
    return c

def get_next_short_id(videos_dir: str) -> str:
    """Scans videos folder and finds the next short_XX id automatically."""
    if not os.path.exists(videos_dir):
        return "short_01"
    folders = os.listdir(videos_dir)
    max_num = 0
    for f in folders:
        m = re.match(r"short_0*(\d+)", f.lower())
        if m:
            max_num = max(max_num, int(m.group(1)))
    next_num = max_num + 1
    return f"short_{next_num:02d}"
