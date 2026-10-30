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
            "If someone does [X], they are secretly trying to [Y]...",
            "Never look someone in the eye like this unless you want to [Z]...",
            "In behavioral psychology, this is known as [Named Effect]...",
            "When someone tries to disrespect you in public, use the [Rule Name]...",
            "The human brain has a dangerous glitch known as [Cognitive Phenomenon]..."
        ],
        "angles": [
            "The Ben Franklin Effect (cognitive dissonance favor hack)",
            "The Pratfall Effect (why minor blunders spike authority)",
            "The 4-Second Silence Rule (breaking intimidation non-verbally)",
            "The Door-in-the-Face Technique (extreme request concession trap)",
            "The Foot-in-the-Door Phenomenon (micro-agreements escalating to compliance)",
            "The Pygmalion Effect (subconscious performance shaping)",
            "The Baader-Meinhof Phenomenon (frequency illusion in persuasion)",
            "The Spotlight Effect (curing social anxiety with statistical reality)",
            "The Zeigarnik Effect (uncompleted tasks hijacking brain memory)",
            "The Decoy Effect (asymmetric dominance pricing and choice steering)",
            "The Halo Effect (how single physical traits blind critical judgment)",
            "The Bystander Effect (diffusion of responsibility and how to break it)",
            "The Scarcity Principle (artificial urgency triggering panic decisions)",
            "Mirroring & Matching (subconscious rapport synchronization)",
            "Triangulation Detection (how manipulators manufacture jealousy)",
            "The Gray Rock Technique (neutralizing toxic narcissism effortlessly)",
            "Gaslighting Counters (documenting reality without emotional reactivity)",
            "The Chameleon Effect (unconscious mimicry establishing social dominance)",
            "Anchoring Bias (how initial numbers permanently distort perception)",
            "The Sunk Cost Fallacy (why humans double down on disastrous choices)",
            "False Consensus Effect (overestimating how many people agree with you)",
            "Non-Verbal Dominance Cues (posture, eye stillness, and vocal gravity)",
            "The Framing Effect (how word choice reverses moral consensus)",
            "Reactance Theory (why forbidden things become irresistibly attractive)",
            "The Contrast Principle (altering valuation through extreme baselines)",
            "The Reciprocity Trap (unsolicited gifts creating subconscious debt)",
            "Silent Treatment Neutralization (depriving emotional validation vampires)",
            "Micro-Expressions (detecting the 0.2-second facial leakage of truth)",
            "The Hawthorne Effect (how awareness of observation changes human behavior)",
            "The Illusion of Control (why humans confuse luck with personal skill)",
            "Social Proof Cascade (how crowds convince individuals to ignore danger)",
            "The Dunning-Kruger Trap (why the least competent speak with the highest confidence)"
        ],
        "visual_bank": [
            "thinking", "shadows", "eye-contact", "silhouette", "dark-room", "crowd",
            "clock", "whisper", "mirror", "walking-alone", "dark-street", "handshake",
            "chess", "fog", "rain-window", "stare", "candle", "stairs", "tunnel",
            "city-night", "smoke", "clock-ticking", "meeting-room", "library", "glasses",
            "writing", "hourglass", "portrait", "deep-thought", "rain", "neon-shadows",
            "hands-typing", "door-opening", "corridor", "dramatic-lighting", "mysterious"
        ]
    },
    "dark_history": {
        "id": "dark_history",
        "name": "The Monster Study & Dark History",
        "rpm_range": "$0.16 - $0.28",
        "retention_rate": "60% - 72%",
        "voice_recommended": "en-US-ChristopherNeural",
        "description": "Disturbing historical experiments, forbidden psychological tests, classified archives, and ancient societal anomalies.",
        "outro_phrase": "Follow {brand_name} for dark historical breakthroughs that shape our world.",
        "forbidden_terms": ["skincare", "serum", "cream", "makeup", "robot factory", "quantum encryption", "drone swarm"],
        "hook_formulas": [
            "In [Year], a psychologist conducted an experiment so unethical it was hidden for decades...",
            "This is the horrifying true story of [Experiment Name]...",
            "The government officially classified this study until [Year]..."
        ],
        "angles": [
            "The 1951 Asch Conformity Test (why 75% deny their own eyes)",
            "The 1968 Blue Eyes Brown Eyes Experiment (manufacturing cruelty in 24 hours)",
            "The 1954 Robbers Cave Experiment (tribal warfare created in 7 days)",
            "The 1939 Monster Study (unethical stuttering experiment on orphans)",
            "The Milgram Experiment (shocking obedience to authority figures)",
            "The Stanford Prison Experiment (how rapid power corridors destroy empathy)",
            "The Pit of Despair (Harry Harlow's devastating maternal deprivation study)",
            "Operation Midnight Climax (CIA safehouses and mind-alteration research)"
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
            "title": "The Ben Franklin Effect: How to Make Anyone Like You #shorts #psychology",
            "script": (
                "If you want someone who dislikes you to become your ally, never do them a favor. Ask them to do one for you. "
                "In psychology, this is known as the Ben Franklin Effect. "
                "The human brain cannot tolerate cognitive dissonance. When someone does you a favor, their subconscious mind assumes: 'I must like this person, otherwise why would I help them?' "
                "To use this ethically, ask for something trivially small: borrow a pen, ask for the time, or request a quick opinion. "
                "Their brain will instantly justify the action by generating subconscious warmth toward you. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["thinking", "eye-contact", "notebook", "shadows", "meeting"],
            "description": "How asking for a small favor hacks cognitive dissonance.\n\nSubscribe to @ShadowMind.\n\n#darkpsychology #psychologyfacts #mindset #manipulation #shorts",
            "pinned_comment": "Have you ever tried the Ben Franklin Effect? Did it work? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The Pratfall Effect: Why Flaws Make You More Powerful #shorts #psychology",
            "script": (
                "Being completely flawless makes people secretly distrust and resent you. "
                "In behavioral psychology, this is known as the Pratfall Effect. "
                "When a highly competent person makes a minor, harmless blunder—like spilling a drop of coffee or dropping a pen—their perceived likability spikes by over forty percent. "
                "Perfection creates an intimidating wall of inferiority in others. A deliberate minor vulnerability humanizes you and instantly lowers everyone's defensive guard. "
                "Never pretend to be superhuman. Let them see your small flaws, and they will trust your immense strengths. "
                "Follow ShadowMind for human behavioral psychology."
            ),
            "keywords": ["coffee", "hands", "walking", "dark-room", "silhouette"],
            "description": "Why making small mistakes increases your authority.\n\nSubscribe to @ShadowMind.\n\n#pratfalleffect #darkpsychology #charisma #confidence #shorts",
            "pinned_comment": "Do you trust people who pretend to be perfect? Be honest. 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The 4-Second Silence Trick to Break Intimidation #shorts #psychology",
            "script": (
                "When someone tries to insult or intimidate you in public, never shout and never defend yourself. Use the four-second silence rule. "
                "Immediately stop speaking. Look directly into the center of their forehead with zero facial expression for exactly four seconds. "
                "In social psychology, silence in the face of aggression is perceived as absolute dominance, while rapid defense signals weakness. "
                "After four seconds of unbroken silence, simply ask: 'Are you okay?' "
                "This instantly shifts the social embarrassment off of you and leaves them exposed in front of the entire room. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["dark-street", "stare", "shadows", "crowd", "clock"],
            "description": "How 4 seconds of unbroken dead silence destroys disrespect.\n\nSubscribe to @ShadowMind.\n\n#stoicism #darkpsychology #bodylanguage #comeback #shorts",
            "pinned_comment": "Would you have the discipline to hold 4 seconds of silence? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The Door-in-the-Face Technique: The Ultimate Persuasion Hack #shorts #psychology",
            "script": (
                "If you want someone to agree to a favor, always demand something absurdly impossible first. "
                "This is the Door-in-the-Face Technique, one of the most powerful compliance triggers discovered in behavioral science. "
                "When you ask for a huge favor and get rejected, their subconscious experiences subtle social guilt. "
                "If you immediately follow up with your real, smaller request, their brain interprets it as a generous concession, making them three times more likely to say yes. "
                "Negotiators and master persuaders use this every day without anyone realizing. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["door", "business", "handshake", "night", "thinking"],
            "description": "Why asking for too much makes people agree to what you actually want.\n\nSubscribe to @ShadowMind.\n\n#persuasion #darkpsychology #negotiation #mindset #shorts",
            "pinned_comment": "Have you ever had this technique used against you? Comment below. 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The Foot-in-the-Door Phenomenon: How Small Yeses Create Total Control #shorts #psychology",
            "script": (
                "If you want someone to commit to a massive life-changing request, never ask for it immediately. Ask for something so small it is impossible to refuse. "
                "In behavioral psychology, this is known as the Foot-in-the-Door Phenomenon. "
                "Once a person agrees to a minor micro-commitment—like signing a simple petition or wearing a small lapel pin—their self-identity shifts. "
                "When you follow up days later with a massive request requiring immense effort, compliance rates skyrocket by over four hundred percent. "
                "Guard your small yeses. They are the gateway to your future decisions. "
                "Follow ShadowMind for psychological rules that put you five steps ahead."
            ),
            "keywords": ["handshake", "notebook", "walking", "shadows", "meeting-room"],
            "description": "How micro-agreements trap human psychology into massive compliance.\n\nSubscribe to @ShadowMind.\n\n#footinthedoor #darkpsychology #persuasion #manipulation #shorts",
            "pinned_comment": "Do you notice when people use micro-commitments on you? 👇",
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
