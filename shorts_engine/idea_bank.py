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
    "body_language": {
        "id": "body_language",
        "name": "Body Language & Non-Verbal Dominance",
        "rpm_range": "$0.20 - $0.36",
        "retention_rate": "65% - 78%",
        "voice_recommended": "en-US-ChristopherNeural",
        "description": "Subconscious physical tells, eye stillness, baseline micro-expressions, posture gravity, and non-verbal intimidation counters.",
        "outro_phrase": "Follow {brand_name} for non-verbal cues that expose what people hide.",
        "forbidden_terms": ["skincare", "serum", "cream", "makeup", "robot factory", "quantum", "gaming", "loot box"],
        "hook_formulas": [
            "If someone blinks more than fifty times in a single minute while talking to you, their autonomic nervous system is hiding something...",
            "When walking into an unfamiliar room, the first spot your eyes land determines whether people view you as prey or authority...",
            "If someone crosses their legs while talking to you, the direction their top foot points reveals their unspoken true intention...",
            "The three-second eye triangle rule that causes people to feel subconscious intimidation without you uttering a single word..."
        ],
        "angles": [
            "The Eye Stillness Trap (Why blinking less than 12 times a minute triggers predator freeze in adversaries)",
            "The Feet Direction Tell (The subconscious biological compass that reveals who someone really cares about)",
            "The Suprasternal Notch Cover (The primal throat-clasp reflex that exposes hidden panic)",
            "The Asymmetrical Smirk (Spotting contempt: the only universal facial expression that predicts betrayal)",
            "The Hand Gravity Anchor (How holding your hands below chest level projects unshakeable authority)",
            "The 4-Second Gaze Break Rule (How looking sideways vs looking down determines your social status)"
        ],
        "visual_bank": [
            "eye-contact", "stare", "silhouette", "interrogation-room", "dark-room", "shadows",
            "walking-alone", "cctv-camera", "mirror", "whisper", "handshake", "crowd"
        ]
    },
    "power_dynamics": {
        "id": "power_dynamics",
        "name": "Machiavellian Power & Frame Control",
        "rpm_range": "$0.22 - $0.40",
        "retention_rate": "64% - 76%",
        "voice_recommended": "en-US-ChristopherNeural",
        "description": "48 Laws of Power analysis, stoic emotional detachment, boundary defense, public insult counters, and corporate political leverage.",
        "outro_phrase": "Follow {brand_name} for cold strategic power laws that keep you untouchable.",
        "forbidden_terms": ["skincare", "serum", "cream", "makeup", "robot factory", "quantum", "gaming", "dupes"],
        "hook_formulas": [
            "When a superior or rival attempts to embarrass you publicly, reacting with anger transfers one hundred percent of the power into their hands...",
            "If someone offers you an unsolicited favor before asking for something, accepting it instantly puts your psychological boundaries into debt...",
            "The most dangerous conversational trap is when someone repeats your exact words back to you with a slight distortion...",
            "Never explain yourself when someone intentionally misunderstands you. Do this five-word counter instead..."
        ],
        "angles": [
            "The Cold Mirror Insult Neutralizer (How asking 'Are you okay?' disarms aggressive public humiliations)",
            "Law 4: Always Say Less Than Necessary (Why silence creates psychological paranoia in opponents)",
            "The Manufactured Urgency Refusal (Breaking forced concession tactics by introducing arbitrary friction)",
            "Frame Control: Never Defend Their Premise (Why defending accusations validates the attacker's territory)",
            "The Strategic Vulnerability Trap (How adversaries bait personal confessions to weaponize them later)",
            "The Benign Violation Defense (Neutralizing backhanded compliments with absolute literal agreement)"
        ],
        "visual_bank": [
            "chess", "interrogation-room", "dramatic-lighting", "silhouette", "dark-room",
            "boardroom", "whisper", "smoke", "corridor", "tunnel", "rain-window"
        ]
    },
    "dark_profiling": {
        "id": "dark_profiling",
        "name": "Dark Personality Profiling & Deception",
        "rpm_range": "$0.20 - $0.38",
        "retention_rate": "66% - 80%",
        "voice_recommended": "en-US-ChristopherNeural",
        "description": "Dark Triad traits, covert narcissist identification, boundary testing cycles, emotional vampire neutralization, and deception forensics.",
        "outro_phrase": "Follow {brand_name} to decode covert predators before they get close.",
        "forbidden_terms": ["skincare", "serum", "cream", "makeup", "robot", "quantum", "gaming", "minecraft"],
        "hook_formulas": [
            "A covert narcissist will never insult your intelligence directly. Instead, they will test your boundaries using this subtle three-phase cycle...",
            "If someone shares an intensely intimate trauma with you within the first twenty minutes of meeting, you are not bonding, you are being mapped...",
            "The single question that causes a pathological liar to freeze and contradict their own backstory within twenty seconds...",
            "How to recognize the predatory grooming technique known as 'artificial commonality' before you let your guard down..."
        ],
        "angles": [
            "The Premature Vulnerability Trap (Why predatory manipulators share fast secrets to extract yours)",
            "The 3-Phase Covert Narcissist Cycle (Idealize, devalue, discard: spotting the exact inflection point)",
            "The Triangulation Strategy (How manipulators manufacture jealousy using invisible third parties)",
            "The Pity Play Defense (Recognizing weaponized helplessness designed to bypass emotional defense)",
            "Micro-Testing Boundaries (Why small infractions are deliberate probes for future exploitation)",
            "The Cognitive Overload Interview (Asking questions out of chronological sequence to shatter alibis)"
        ],
        "visual_bank": [
            "mirror", "silhouette", "dark-room", "interrogation-room", "shadows",
            "whisper", "cctv-camera", "eye-contact", "stare", "dark-street", "rain-window"
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
    "body_language": [
        {
            "title": "The 3-Second Eye Stillness Trick That Terrifies Liars #shorts #darkpsychology",
            "script": (
                "If you suspect someone is lying or attempting to intimidate you, never look away or blink rapidly. Do this non-verbal move instead. "
                "Lock your gaze directly on the bridge between their eyebrows, relax your facial muscles, and reduce your blink rate to zero for three full seconds. "
                "In human evolutionary biology, unblinking predatory stillness signals absolute zero fear and overwhelming status dominance. "
                "Their autonomic nervous system will perceive an unpredictable threat, triggering an immediate spike in cortisol and cognitive collapse. "
                "Within four seconds, they will break eye contact downward and nervously touch their neck. "
                "Follow ShadowMind for non-verbal cues that expose what people hide."
            ),
            "keywords": ["eye-contact", "stare", "interrogation-room", "silhouette", "dark-room"],
            "description": "How unblinking eye stillness shatters psychological intimidation.\n\nSubscribe to @ShadowMind.\n\n#bodylanguage #darkpsychology #mindset #manipulation #shorts",
            "pinned_comment": "Have you ever held eye contact long enough to make someone nervous? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "The Feet Direction Tell: What Their Body Really Wants #shorts #psychology",
            "script": (
                "While people can easily fake their facial smiles and words, their feet are controlled by the limbic survival brain and almost never lie. "
                "When you are having a conversation with someone, glance briefly at where their feet are pointing. "
                "If their torso is facing you but their feet are angled toward the door or another person, their subconscious mind has already left the conversation. "
                "Never force the conversation when you spot this physical cue. Stop talking, take one step backward, and let the silence create tension. "
                "Follow ShadowMind for non-verbal cues that expose what people hide."
            ),
            "keywords": ["walking-alone", "shadows", "meeting", "silhouette", "whisper"],
            "description": "Why feet position reveals true subconscious intent before words do.\n\nSubscribe to @ShadowMind.\n\n#bodylanguage #psychologyfacts #humanbehavior #mindhacks #shorts",
            "pinned_comment": "Check where people point their feet today. What did you notice? 👇",
            "voice": "en-US-ChristopherNeural"
        }
    ],
    "power_dynamics": [
        {
            "title": "How to Silence Someone Who Insults You in Public #shorts #darkpsychology",
            "script": (
                "When someone drops a sly, humiliating insult disguised as a joke in front of a group, getting angry or firing back instantly makes you look defensive. Do this cold counter instead. "
                "Look them dead in the eyes with zero expression, pause for two seconds, and say calmly: 'Are you okay?' "
                "This single psychological maneuver completely reframes the entire dynamic in the room. "
                "You shift the attention from their witty jab to their emotional stability, making them appear unhinged and desperate. "
                "Follow ShadowMind for cold strategic power laws that keep you untouchable."
            ),
            "keywords": ["chess", "interrogation-room", "dark-room", "dramatic-lighting", "silhouette"],
            "description": "The cold 3-word phrase that completely disarms public disrespect.\n\nSubscribe to @ShadowMind.\n\n#powerdynamics #48lawsofpower #darkpsychology #stoicism #shorts",
            "pinned_comment": "How do you handle disrespect in front of other people? Drop your rule below. 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "Law 4: Why Always Saying Less Than Necessary Terrifies Opponents #shorts #power",
            "script": (
                "When you try to impress people with words, the more you say, the more common you appear and the less in control you feel. "
                "Powerful people impress and intimidate by saying less. "
                "The human brain despises silence; in any negotiation or heated exchange, awkward silence creates unbearable psychological pressure. "
                "When asked a probing or demanding question, give a brief, one-sentence answer and stay silent while holding eye contact. "
                "The other person will scramble to fill the void, rambling nervously and accidentally surrendering critical leverage. "
                "Follow ShadowMind for cold strategic power laws that keep you untouchable."
            ),
            "keywords": ["boardroom", "silhouette", "whisper", "smoke", "interrogation-room"],
            "description": "Why silence in conversation forces rivals to surrender control.\n\nSubscribe to @ShadowMind.\n\n#48lawsofpower #machiavelli #influence #mindset #shorts",
            "pinned_comment": "Do you speak first or wait for others to reveal their hand? Let us know below. 👇",
            "voice": "en-US-ChristopherNeural"
        }
    ],
    "dark_profiling": [
        {
            "title": "The Premature Vulnerability Trap Used by Covert Predators #shorts #psychology",
            "script": (
                "If someone you just met shares a deeply traumatic, highly personal secret with you within the first thirty minutes, beware. "
                "You are not experiencing a rare, magical connection; you are being profiled. "
                "Covert manipulators use premature vulnerability to trigger the psychological rule of reciprocity. "
                "By giving you an intimate confession first, they manufacture artificial trust and obligate you to reveal your own vulnerabilities. "
                "Once you hand over your insecurities, they catalogue them to exploit months later when you least expect it. "
                "Follow ShadowMind to decode covert predators before they get close."
            ),
            "keywords": ["mirror", "silhouette", "whisper", "interrogation-room", "shadows"],
            "description": "Why fast emotional confessions are the #1 red flag of manipulative grooming.\n\nSubscribe to @ShadowMind.\n\n#darktriad #covertnarcissist #manipulation #psychology #shorts",
            "pinned_comment": "Have you ever met someone who trauma-dumped immediately? What happened? 👇",
            "voice": "en-US-ChristopherNeural"
        },
        {
            "title": "How to Shatter a Deceptive Alibi with Reverse Chronology #shorts #darkpsychology",
            "script": (
                "When someone rehearses a fabricated story, they always practice it in strict chronological order: this happened, then that happened, then I went home. "
                "Here is the interrogation technique federal agents use to expose the truth in thirty seconds. "
                "Do not challenge their facts directly. Instead, ask them: 'Before you left the building, what was the exact conversation you had right before that?' "
                "Fabricating a lie burns massive cognitive load. Forcing a liar to recount events backwards causes an immediate neurological bottleneck. "
                "Watch their speech rhythm falter, their eyes freeze, and their details contradict. "
                "Follow ShadowMind to decode covert predators before they get close."
            ),
            "keywords": ["cctv-camera", "interrogation-room", "stare", "dark-street", "silhouette"],
            "description": "How the reverse timeline test instantly exposes rehearsed deception.\n\nSubscribe to @ShadowMind.\n\n#liebehavior #deception #interrogation #darkpsychology #shorts",
            "pinned_comment": "Spotting a lie: What is your #1 giveaway tell? Tell us below. 👇",
            "voice": "en-US-ChristopherNeural"
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



