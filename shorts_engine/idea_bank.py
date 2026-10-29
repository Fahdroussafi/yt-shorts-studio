import random
import os
import re

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
                "Follow ShadowMind to master non-verbal power dynamics."
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
                "Follow ShadowMind to see through everyday psychological tactics."
            ),
            "keywords": ["door", "business", "handshake", "night", "thinking"],
            "description": "Why asking for too much makes people agree to what you actually want.\n\nSubscribe to @ShadowMind.\n\n#persuasion #darkpsychology #negotiation #mindset #shorts",
            "pinned_comment": "Have you ever had this technique used against you? Comment below. 👇",
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
                "Follow ShadowMind for dark historical reality."
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
                "Follow ShadowMind for historical truths that shape our world."
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
                "Follow ShadowMind for human psychology and dark historical breakthroughs."
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
                "Follow ShadowMind for the hidden realities shaping tomorrow."
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
                "Follow ShadowMind for beauty science and facial geometry breakdowns."
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
    import os
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
