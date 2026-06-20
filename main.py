from __future__ import annotations

import html
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from pydantic import BaseModel


@dataclass(frozen=True)
class TemplateItem:
    prompt_template: str
    correct_answer: str
    choices: list[str] | None = None
    explanation: str = ""


# Compact question bank.
# Each tuple is: (prompt, correct_answer, choices, explanation)
RAW_BANK: dict[str, dict[str, list[tuple[str, str, list[str], str]]]] = {
    "science": {
        "easy": [
            ("Which gas do plants absorb from the air for photosynthesis?", "Carbon dioxide",
             ["Oxygen", "Carbon dioxide", "Nitrogen", "Hydrogen"], "Plants take in CO2 and release oxygen."),
            ("What is H2O commonly known as?", "Water",
             ["Salt", "Water", "Sugar", "Oxygen"], "H2O is the chemical formula for water."),
        ],
        "medium": [
            ("What is the powerhouse of the cell?", "Mitochondria",
             ["Nucleus", "Mitochondria", "Ribosome", "Golgi body"], "Mitochondria produce ATP energy."),
            ("What force keeps planets in orbit around the Sun?", "Gravity",
             ["Magnetism", "Gravity", "Friction", "Tension"], "Gravity provides the centripetal force."),
        ],
        "hard": [
            ("What is the pH of a neutral solution at 25C?", "7",
             ["0", "7", "14", "1"], "Neutral solutions have a pH of 7."),
            ("Who proposed evolution by natural selection?", "Charles Darwin",
             ["Isaac Newton", "Charles Darwin", "Albert Einstein", "Gregor Mendel"], "Darwin wrote On the Origin of Species."),
        ],
    },
    "physics": {
        "easy": [
            ("What is the SI unit of force?", "Newton",
             ["Joule", "Newton", "Watt", "Pascal"], "Force is measured in newtons (N)."),
            ("What energy does a moving object have?", "Kinetic energy",
             ["Potential energy", "Kinetic energy", "Chemical energy", "Nuclear energy"], "Motion gives kinetic energy."),
        ],
        "medium": [
            ("Acceleration due to gravity on Earth is about?", "9.8 m/s^2",
             ["1.6 m/s^2", "9.8 m/s^2", "20 m/s^2", "3.7 m/s^2"], "Earth's g is about 9.8 m/s^2."),
            ("Every action has an equal and opposite reaction is which law?", "Newton's third law",
             ["Newton's first law", "Newton's second law", "Newton's third law", "Ohm's law"], "That is Newton's third law."),
        ],
        "hard": [
            ("Speed of light in vacuum is about?", "300,000 km/s",
             ["150,000 km/s", "300,000 km/s", "30,000 km/s", "1,000 km/s"], "c is about 3x10^8 m/s."),
            ("Which particle carries a negative charge?", "Electron",
             ["Proton", "Neutron", "Electron", "Positron"], "Electrons carry negative charge."),
        ],
    },
    "chemistry": {
        "easy": [
            ("What is the chemical symbol for gold?", "Au",
             ["Gd", "Au", "Ag", "Go"], "Gold's symbol is Au."),
            ("What gas makes up most of Earth's atmosphere?", "Nitrogen",
             ["Oxygen", "Nitrogen", "Carbon dioxide", "Argon"], "About 78% is nitrogen."),
        ],
        "medium": [
            ("What is the most common state of matter in the universe?", "Plasma",
             ["Solid", "Liquid", "Gas", "Plasma"], "Stars are made of plasma."),
            ("A reaction that releases heat is called?", "Exothermic",
             ["Endothermic", "Exothermic", "Neutral", "Catalytic"], "Exothermic reactions release energy."),
        ],
        "hard": [
            ("What is the atomic number of carbon?", "6",
             ["4", "6", "8", "12"], "Carbon has 6 protons."),
            ("Which element has the symbol Fe?", "Iron",
             ["Fluorine", "Iron", "Lead", "Francium"], "Fe stands for iron (ferrum)."),
        ],
    },
    "biology": {
        "easy": [
            ("What organ pumps blood through the body?", "Heart",
             ["Lung", "Heart", "Liver", "Kidney"], "The heart pumps blood."),
            ("What do bees collect from flowers?", "Nectar",
             ["Water", "Nectar", "Soil", "Leaves"], "Bees collect nectar to make honey."),
        ],
        "medium": [
            ("What is the basic unit of life?", "Cell",
             ["Atom", "Cell", "Tissue", "Organ"], "Cells are life's basic unit."),
            ("Which blood cells fight infection?", "White blood cells",
             ["Red blood cells", "White blood cells", "Platelets", "Plasma"], "White blood cells defend the body."),
        ],
        "hard": [
            ("What molecule carries genetic information?", "DNA",
             ["RNA", "DNA", "ATP", "Protein"], "DNA stores the genetic code."),
            ("What process do plants use to make food?", "Photosynthesis",
             ["Respiration", "Photosynthesis", "Digestion", "Fermentation"], "Plants make glucose via photosynthesis."),
        ],
    },
    "health": {
        "easy": [
            ("Recommended sleep for most adults per night?", "7-9 hours",
             ["3-4 hours", "5-6 hours", "7-9 hours", "12+ hours"], "Adults typically need 7-9 hours."),
            ("Which vitamin does sunlight help your body produce?", "Vitamin D",
             ["Vitamin A", "Vitamin C", "Vitamin D", "Vitamin K"], "Sunlight triggers vitamin D synthesis."),
        ],
        "medium": [
            ("Body's main source of quick energy?", "Carbohydrates",
             ["Protein", "Carbohydrates", "Fat", "Fiber"], "Carbs are the main quick energy source."),
            ("Normal resting heart rate for adults (bpm)?", "60-100",
             ["20-40", "40-60", "60-100", "120-160"], "Normal resting HR is 60-100 bpm."),
        ],
        "hard": [
            ("Which organ produces insulin?", "Pancreas",
             ["Liver", "Pancreas", "Spleen", "Stomach"], "The pancreas produces insulin."),
            ("Which mineral is essential for healthy bones?", "Calcium",
             ["Iron", "Calcium", "Sodium", "Zinc"], "Calcium builds bones and teeth."),
        ],
    },
    "technology": {
        "easy": [
            ("What does CPU stand for?", "Central Processing Unit",
             ["Central Processing Unit", "Computer Power Unit", "Core Program Utility", "Control Panel Unit"], "CPU = Central Processing Unit."),
            ("What does 'WWW' stand for?", "World Wide Web",
             ["World Wide Web", "Web World Wide", "Wide World Web", "World Web Wide"], "WWW = World Wide Web."),
        ],
        "medium": [
            ("Which company develops Windows?", "Microsoft",
             ["Apple", "Microsoft", "Google", "IBM"], "Microsoft makes Windows."),
            ("What does HTTP primarily transfer?", "Web pages",
             ["Emails", "Web pages", "Files only", "Videos only"], "HTTP transfers hypertext/web content."),
        ],
        "hard": [
            ("Which data structure uses Last-In First-Out order?", "Stack",
             ["Queue", "Stack", "Array", "Tree"], "Stacks are LIFO."),
            ("Time complexity of binary search?", "O(log n)",
             ["O(n)", "O(log n)", "O(n^2)", "O(1)"], "Binary search halves the range each step."),
        ],
    },
    "ai": {
        "easy": [
            ("What does 'AI' stand for?", "Artificial Intelligence",
             ["Automated Input", "Artificial Intelligence", "Advanced Internet", "Applied Information"], "AI = Artificial Intelligence."),
            ("Which of these is a common AI chatbot core?", "Language model",
             ["Spreadsheet", "Language model", "Router", "Compiler"], "Chatbots use language models."),
        ],
        "medium": [
            ("What is training data used for?", "Teaching the model patterns",
             ["Cooling the computer", "Teaching the model patterns", "Storing passwords", "Drawing graphics"], "Models learn patterns from training data."),
            ("Field where computers learn from data?", "Machine learning",
             ["Cybersecurity", "Machine learning", "Networking", "Databases"], "Machine learning learns from data."),
        ],
        "hard": [
            ("A neural network loosely imitates what?", "The human brain",
             ["A car engine", "The human brain", "A calculator", "A database"], "Neural nets are inspired by brain neurons."),
            ("What does 'NLP' stand for in AI?", "Natural Language Processing",
             ["Neural Logic Programming", "Natural Language Processing", "Network Layer Protocol", "New Learning Path"], "NLP = Natural Language Processing."),
        ],
    },
    "mathematics": {
        "easy": [
            ("What is 7 x 8?", "56",
             ["54", "56", "48", "64"], "7 x 8 = 56."),
            ("Value of pi to two decimals?", "3.14",
             ["3.12", "3.14", "3.16", "3.41"], "Pi is about 3.14."),
        ],
        "medium": [
            ("A triangle with all sides equal is?", "Equilateral",
             ["Isosceles", "Scalene", "Equilateral", "Right"], "All equal sides = equilateral."),
            ("What is 15% of 200?", "30",
             ["15", "20", "30", "45"], "15% of 200 is 30."),
        ],
        "hard": [
            ("Square root of 144?", "12",
             ["10", "12", "14", "16"], "12 x 12 = 144."),
            ("Next prime number after 7?", "11",
             ["8", "9", "10", "11"], "11 is the next prime."),
        ],
    },
    "history": {
        "easy": [
            ("First President of the United States?", "George Washington",
             ["Abraham Lincoln", "George Washington", "Thomas Jefferson", "John Adams"], "Washington was the first U.S. president."),
            ("The Great Pyramids are located in?", "Egypt",
             ["Mexico", "Egypt", "Greece", "Iraq"], "The Giza pyramids are in Egypt."),
        ],
        "medium": [
            ("In which year did World War II end?", "1945",
             ["1918", "1939", "1945", "1950"], "WWII ended in 1945."),
            ("Who formulated the law of gravity?", "Isaac Newton",
             ["Galileo", "Isaac Newton", "Einstein", "Copernicus"], "Newton formulated gravity."),
        ],
        "hard": [
            ("Which empire built the Colosseum?", "Roman Empire",
             ["Greek Empire", "Roman Empire", "Ottoman Empire", "Persian Empire"], "Romans built the Colosseum."),
            ("Who co-wrote the Communist Manifesto?", "Karl Marx",
             ["Lenin", "Karl Marx", "Stalin", "Adam Smith"], "Marx and Engels wrote it."),
        ],
    },
    "geography": {
        "easy": [
            ("Largest ocean on Earth?", "Pacific Ocean",
             ["Atlantic Ocean", "Pacific Ocean", "Indian Ocean", "Arctic Ocean"], "The Pacific is the largest ocean."),
            ("Which continent is the Sahara Desert in?", "Africa",
             ["Asia", "Africa", "Australia", "Europe"], "The Sahara is in Africa."),
        ],
        "medium": [
            ("Capital of Japan?", "Tokyo",
             ["Kyoto", "Tokyo", "Osaka", "Seoul"], "Tokyo is Japan's capital."),
            ("Longest river in the world?", "Nile",
             ["Amazon", "Nile", "Yangtze", "Mississippi"], "The Nile is commonly cited as longest."),
        ],
        "hard": [
            ("Mount Everest borders Nepal and?", "China",
             ["India", "China", "Bhutan", "Pakistan"], "Everest borders Nepal and China (Tibet)."),
            ("Most populous country today?", "India",
             ["China", "India", "USA", "Indonesia"], "India is now the most populous."),
        ],
    },
    "space": {
        "easy": [
            ("Which planet is closest to the Sun?", "Mercury",
             ["Venus", "Mercury", "Earth", "Mars"], "Mercury is closest."),
            ("A natural satellite of a planet is a?", "Moon",
             ["Star", "Moon", "Comet", "Asteroid"], "Natural satellites are moons."),
        ],
        "medium": [
            ("Which galaxy is Earth in?", "Milky Way",
             ["Andromeda", "Milky Way", "Whirlpool", "Sombrero"], "We live in the Milky Way."),
            ("Largest planet in our solar system?", "Jupiter",
             ["Saturn", "Jupiter", "Neptune", "Earth"], "Jupiter is the largest planet."),
        ],
        "hard": [
            ("Name of the first artificial satellite?", "Sputnik 1",
             ["Apollo 11", "Sputnik 1", "Voyager 1", "Hubble"], "Sputnik 1 launched in 1957."),
            ("Star at the center of our solar system?", "The Sun",
             ["Sirius", "The Sun", "Polaris", "Betelgeuse"], "The Sun is our star."),
        ],
    },
    "literature": {
        "easy": [
            ("Who wrote 'Romeo and Juliet'?", "William Shakespeare",
             ["Charles Dickens", "William Shakespeare", "Mark Twain", "Jane Austen"], "Shakespeare wrote it."),
            ("A person who writes books is an?", "Author",
             ["Actor", "Author", "Editor", "Painter"], "A book writer is an author."),
        ],
        "medium": [
            ("Who wrote 'Pride and Prejudice'?", "Jane Austen",
             ["Emily Bronte", "Jane Austen", "Mary Shelley", "Virginia Woolf"], "Austen wrote it."),
            ("A short story with a moral is a?", "Fable",
             ["Novel", "Fable", "Biography", "Memoir"], "Fables teach morals."),
        ],
        "hard": [
            ("Who wrote 'War and Peace'?", "Leo Tolstoy",
             ["Dostoevsky", "Leo Tolstoy", "Chekhov", "Gogol"], "Tolstoy wrote War and Peace."),
            ("A comparison using 'like' or 'as' is a?", "Simile",
             ["Metaphor", "Simile", "Hyperbole", "Irony"], "Similes use like/as."),
        ],
    },
    "music": {
        "easy": [
            ("How many strings on a standard guitar?", "6",
             ["4", "5", "6", "7"], "Standard guitars have 6 strings."),
            ("Which instrument has black and white keys?", "Piano",
             ["Violin", "Piano", "Drum", "Flute"], "The piano has keys."),
        ],
        "medium": [
            ("Notes in a standard musical octave?", "8",
             ["5", "7", "8", "12"], "An octave spans 8 notes."),
            ("What does 'forte' mean in music?", "Loud",
             ["Soft", "Loud", "Fast", "Slow"], "Forte means loud."),
        ],
        "hard": [
            ("Who composed the Ninth Symphony?", "Beethoven",
             ["Mozart", "Beethoven", "Bach", "Chopin"], "Beethoven composed the 9th."),
            ("Italian term for gradually getting louder?", "Crescendo",
             ["Diminuendo", "Crescendo", "Staccato", "Legato"], "Crescendo = getting louder."),
        ],
    },
    "sports": {
        "easy": [
            ("Players on a soccer team on the field?", "11",
             ["9", "10", "11", "12"], "Soccer teams field 11 players."),
            ("Sport using a racket and shuttlecock?", "Badminton",
             ["Tennis", "Badminton", "Squash", "Cricket"], "Badminton uses a shuttlecock."),
        ],
        "medium": [
            ("How often are the Summer Olympics held?", "Every 4 years",
             ["Every year", "Every 2 years", "Every 4 years", "Every 5 years"], "Olympics are every 4 years."),
            ("Points for a basketball free throw?", "1",
             ["1", "2", "3", "4"], "A free throw is 1 point."),
        ],
        "hard": [
            ("Country with the most FIFA World Cups?", "Brazil",
             ["Germany", "Brazil", "Italy", "Argentina"], "Brazil has 5 titles."),
            ("In tennis, a score of zero is called?", "Love",
             ["Nil", "Love", "Deuce", "Zero"], "Zero is 'love' in tennis."),
        ],
    },
    "art": {
        "easy": [
            ("Who painted the Mona Lisa?", "Leonardo da Vinci",
             ["Picasso", "Leonardo da Vinci", "Van Gogh", "Michelangelo"], "Da Vinci painted the Mona Lisa."),
            ("The three primary colors are?", "Red, blue, yellow",
             ["Red, green, blue", "Red, blue, yellow", "Black, white, gray", "Orange, green, purple"], "Primary colors: red, blue, yellow."),
        ],
        "medium": [
            ("Which artist cut off part of his own ear?", "Vincent van Gogh",
             ["Monet", "Vincent van Gogh", "Dali", "Rembrandt"], "Van Gogh famously did so."),
            ("Salvador Dali is associated with?", "Surrealism",
             ["Cubism", "Surrealism", "Impressionism", "Realism"], "Dali was a surrealist."),
        ],
        "hard": [
            ("Who painted the Sistine Chapel ceiling?", "Michelangelo",
             ["Raphael", "Michelangelo", "Donatello", "Caravaggio"], "Michelangelo painted it."),
            ("Technique using tiny dots to form an image?", "Pointillism",
             ["Cubism", "Pointillism", "Fresco", "Collage"], "Pointillism uses dots."),
        ],
    },
    "economics": {
        "easy": [
            ("Money earned from a job is called?", "Income",
             ["Debt", "Income", "Tax", "Loan"], "Earnings are income."),
            ("When prices rise over time, it is?", "Inflation",
             ["Deflation", "Inflation", "Recession", "Tax"], "Rising prices = inflation."),
        ],
        "medium": [
            ("What does GDP stand for?", "Gross Domestic Product",
             ["Gross Domestic Product", "General Data Plan", "Global Demand Price", "Gross Debt Payment"], "GDP = Gross Domestic Product."),
            ("Which law relates price to quantity demanded?", "Law of demand",
             ["Law of gravity", "Law of demand", "Law of motion", "Law of returns"], "Higher price usually lowers demand."),
        ],
        "hard": [
            ("Who wrote 'The Wealth of Nations'?", "Adam Smith",
             ["Karl Marx", "Adam Smith", "Keynes", "Ricardo"], "Adam Smith wrote it."),
            ("A period of economic decline is a?", "Recession",
             ["Expansion", "Recession", "Surplus", "Boom"], "Decline = recession."),
        ],
    },
    "general": {
        "easy": [
            ("How many days are in a leap year?", "366",
             ["364", "365", "366", "367"], "Leap years have 366 days."),
            ("Freezing point of water in Celsius?", "0",
             ["0", "10", "32", "100"], "Water freezes at 0C."),
        ],
        "medium": [
            ("How many continents are on Earth?", "7",
             ["5", "6", "7", "8"], "There are 7 continents."),
            ("Largest mammal on Earth?", "Blue whale",
             ["Elephant", "Blue whale", "Giraffe", "Shark"], "The blue whale is the largest mammal."),
        ],
        "hard": [
            ("How many bones are in the adult human body?", "206",
             ["186", "206", "226", "250"], "Adults have 206 bones."),
            ("Hardest natural substance on Earth?", "Diamond",
             ["Gold", "Diamond", "Iron", "Quartz"], "Diamond is the hardest."),
        ],
    },
}


TEMPLATES: dict[str, dict[str, list[TemplateItem]]] = {
    subject: {
        difficulty: [TemplateItem(*item) for item in items]
        for difficulty, items in difficulties.items()
    }
    for subject, difficulties in RAW_BANK.items()
}


# True/False statements asked directly as a claim the user judges.
# Each tuple is: (statement, is_true, explanation)
TF_RAW: dict[str, list[tuple[str, bool, str]]] = {
    "science": [
        ("Water is essential for human survival.", True, "Humans need water to live."),
        ("The Sun revolves around the Earth.", False, "The Earth revolves around the Sun."),
        ("Plants release oxygen during photosynthesis.", True, "Photosynthesis produces oxygen."),
    ],
    "physics": [
        ("Light travels faster than sound.", True, "Light is far faster than sound."),
        ("Energy can be created out of nothing.", False, "Energy is conserved, not created."),
        ("In a vacuum, a feather and a hammer fall at the same rate.", True, "With no air resistance they fall together."),
    ],
    "chemistry": [
        ("Water is made of hydrogen and oxygen.", True, "Water is H2O."),
        ("Gold is a chemical compound.", False, "Gold is a pure element."),
        ("Acids have a pH below 7.", True, "Acids are below pH 7."),
    ],
    "biology": [
        ("The heart pumps blood around the body.", True, "That is the heart's job."),
        ("Humans can survive indefinitely without oxygen.", False, "We need oxygen constantly."),
        ("DNA carries genetic information.", True, "DNA stores the genetic code."),
    ],
    "health": [
        ("Regular exercise is good for the heart.", True, "Exercise strengthens the heart."),
        ("Smoking improves lung health.", False, "Smoking damages the lungs."),
        ("Drinking enough water helps the body function well.", True, "Hydration supports body functions."),
    ],
    "technology": [
        ("A CPU is often called the brain of the computer.", True, "The CPU processes instructions."),
        ("HTTPS is less secure than HTTP.", False, "HTTPS is the secure version."),
        ("RAM is a type of computer memory.", True, "RAM is volatile working memory."),
    ],
    "ai": [
        ("AI models can learn patterns from data.", True, "Machine learning learns from data."),
        ("Artificial intelligence truly feels human emotions.", False, "AI does not actually feel emotions."),
        ("Neural networks are loosely inspired by the human brain.", True, "They mimic neurons loosely."),
    ],
    "mathematics": [
        ("The number 2 is a prime number.", True, "2 is the only even prime."),
        ("Pi is exactly equal to 3.", False, "Pi is about 3.14159."),
        ("A right angle measures 90 degrees.", True, "Right angles are 90 degrees."),
    ],
    "history": [
        ("World War II ended in 1945.", True, "WWII ended in 1945."),
        ("The Great Wall of China is located in Egypt.", False, "It is in China."),
        ("George Washington was the first U.S. president.", True, "He was the first president."),
    ],
    "geography": [
        ("The Pacific is the largest ocean on Earth.", True, "It is the largest ocean."),
        ("Africa is a country.", False, "Africa is a continent."),
        ("Tokyo is the capital of Japan.", True, "Tokyo is Japan's capital."),
    ],
    "space": [
        ("The Sun is a star.", True, "The Sun is our star."),
        ("The Moon produces its own light.", False, "The Moon reflects sunlight."),
        ("Jupiter is the largest planet in our solar system.", True, "Jupiter is the largest planet."),
    ],
    "literature": [
        ("Shakespeare wrote Romeo and Juliet.", True, "He wrote it."),
        ("A biography is a story about imaginary creatures.", False, "A biography is about a real person's life."),
        ("A simile compares things using 'like' or 'as'.", True, "That defines a simile."),
    ],
    "music": [
        ("A standard guitar has six strings.", True, "Standard guitars have 6 strings."),
        ("In music, 'forte' means to play softly.", False, "Forte means loud."),
        ("A piano is a keyboard instrument.", True, "It is played with keys."),
    ],
    "sports": [
        ("A soccer team has eleven players on the field.", True, "Each side fields 11 players."),
        ("A marathon is shorter than 100 meters.", False, "A marathon is about 42 km."),
        ("Basketball is played by shooting a ball through a hoop.", True, "That describes basketball."),
    ],
    "art": [
        ("Leonardo da Vinci painted the Mona Lisa.", True, "He painted it."),
        ("Sculptors mainly work with sound.", False, "Sculptors shape materials like stone or metal."),
        ("Red, blue, and yellow are primary colors.", True, "Those are the primary colors."),
    ],
    "economics": [
        ("Inflation means prices are generally rising.", True, "Inflation is rising prices."),
        ("Saving money means spending all of it immediately.", False, "Saving means keeping money for later."),
        ("GDP measures a country's economic output.", True, "GDP measures output."),
    ],
    "general": [
        ("A leap year has 366 days.", True, "Leap years have 366 days."),
        ("There are 5 continents on Earth.", False, "There are 7 continents."),
        ("Water boils at 100 degrees Celsius at sea level.", True, "Boiling point is 100C at sea level."),
    ],
}


@dataclass(frozen=True)
class TFItem:
    statement: str
    answer: str
    explanation: str


TF_BANK: dict[str, list[TFItem]] = {
    subject: [TFItem(stmt, "True" if is_true else "False", expl) for stmt, is_true, expl in items]
    for subject, items in TF_RAW.items()
}


DISPLAY_NAMES: dict[str, str] = {
    "ai": "Artificial Intelligence",
    "general": "General Knowledge",
}


def subject_label(key: str) -> str:
    return DISPLAY_NAMES.get(key, key.replace("_", " ").title())


DIFFICULTY_LEVELS = ["easy", "medium", "hard", "advanced"]

# "advanced" reuses the hardest authored content pool.
CONTENT_DIFFICULTY: dict[str, str] = {
    "easy": "easy",
    "medium": "medium",
    "hard": "hard",
    "advanced": "hard",
}

# Max 1 minute per question on easy, shrinking as difficulty rises.
SECONDS_PER_DIFFICULTY: dict[str, int] = {
    "easy": 60,
    "medium": 45,
    "hard": 35,
    "advanced": 25,
}

# Maps our topics to Open Trivia Database category ids (https://opentdb.com).
# This gives a very large, non-repeating pool of live questions.
OPENTDB_CATEGORY: dict[str, int] = {
    "science": 17,      # Science & Nature
    "physics": 17,
    "chemistry": 17,
    "biology": 17,
    "health": 17,
    "space": 17,
    "technology": 18,   # Science: Computers
    "ai": 18,
    "mathematics": 19,  # Science: Mathematics
    "history": 23,      # History
    "geography": 22,    # Geography
    "literature": 10,   # Entertainment: Books
    "music": 12,        # Entertainment: Music
    "sports": 21,       # Sports
    "art": 25,          # Art
    "economics": 24,    # Politics (closest available)
    "general": 9,       # General Knowledge
}

OPENTDB_URL = "https://opentdb.com/api.php"
OPENTDB_COUNT_URL = "https://opentdb.com/api_count.php"


class QuestionPayload(BaseModel):
    id: int
    difficulty: str
    question_type: str
    prompt: str
    choices: list[str] | None = None
    answer: str
    explanation: str


def normalize_answer(text: str) -> str:
    return " ".join(text.strip().lower().split())


def suggest_difficulty(score_percent: float) -> str:
    if score_percent >= 90:
        return "advanced"
    if score_percent >= 70:
        return "hard"
    if score_percent >= 45:
        return "medium"
    return "easy"


def selected_types_from_flags(include_mc: bool, include_short: bool, include_tf: bool) -> list[str]:
    available: list[str] = []
    if include_mc:
        available.append("multiple_choice")
    if include_short:
        available.append("short_answer")
    if include_tf:
        available.append("true_false")
    return available


def build_type_sequence(selected_types: list[str], count: int) -> list[str]:
    """Guarantee a balanced mix of every selected type, then shuffle the order."""
    sequence: list[str] = []
    i = 0
    while len(sequence) < count:
        sequence.append(selected_types[i % len(selected_types)])
        i += 1
    random.shuffle(sequence)
    return sequence


def build_choice_question(
    item: TemplateItem,
    question_id: int,
    difficulty: str,
    question_type: str,
) -> QuestionPayload:
    answer = item.correct_answer
    choices: list[str] | None = None

    if question_type == "multiple_choice":
        base_choices = list(item.choices or [item.correct_answer, "Option B", "Option C", "Option D"])
        if answer not in base_choices:
            base_choices.append(answer)
        random.shuffle(base_choices)
        choices = base_choices[:4]

    return QuestionPayload(
        id=question_id,
        difficulty=difficulty,
        question_type=question_type,
        prompt=item.prompt_template,
        choices=choices,
        answer=answer,
        explanation=item.explanation or "Review this concept and try again.",
    )


def build_true_false_question(
    tf_item: TFItem,
    question_id: int,
    difficulty: str,
) -> QuestionPayload:
    return QuestionPayload(
        id=question_id,
        difficulty=difficulty,
        question_type="true_false",
        prompt=tf_item.statement,
        choices=["True", "False"],
        answer=tf_item.answer,
        explanation=tf_item.explanation,
    )


def fetch_opentdb(category_id: int, difficulty: str, amount: int, qtype: str | None = None) -> list[dict[str, Any]]:
    """Fetch a batch of unique questions from Open Trivia DB. Returns [] on any failure."""
    if amount <= 0:
        return []
    params: dict[str, Any] = {
        "amount": min(amount, 50),
        "category": category_id,
        "difficulty": difficulty,
        "encode": "url3986",
    }
    if qtype:
        params["type"] = qtype
    url = f"{OPENTDB_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "QuestGen/1.0"})

    # response_code 5 = rate limited (1 request / 5s per IP). Retry once after waiting.
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            return []

        code = data.get("response_code")
        if code == 0:
            return data.get("results", [])
        if code == 5 and attempt == 0:
            time.sleep(5.2)
            continue
        return []
    return []


def opentdb_available(category_id: int, content_difficulty: str) -> int:
    """How many questions exist for a category+difficulty. Avoids requesting more
    than available (which would make Open Trivia DB return an empty result)."""
    url = f"{OPENTDB_COUNT_URL}?{urllib.parse.urlencode({'category': category_id})}"
    request = urllib.request.Request(url, headers={"User-Agent": "QuestGen/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
        counts = data.get("category_question_count", {})
        return int(counts.get(f"total_{content_difficulty}_question_count", 0))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError, TypeError):
        return 0


def decode(text: str) -> str:
    """Open Trivia DB returns url3986 encoded text; decode and unescape it."""
    return html.unescape(urllib.parse.unquote(text))


def focus_tokens(focus: str) -> list[str]:
    """Meaningful keywords from a focus phrase (e.g. 'linear algebra' -> ['linear', 'algebra'])."""
    return [token for token in normalize_answer(focus).split() if len(token) >= 3]


def result_matches_focus(result: dict[str, Any], tokens: list[str]) -> bool:
    parts = [result.get("question", ""), result.get("category", ""), result.get("correct_answer", "")]
    parts.extend(result.get("incorrect_answers", []))
    haystack = normalize_answer(decode(" ".join(parts)))
    return any(token in haystack for token in tokens)


def api_choice_question(
    result: dict[str, Any],
    question_id: int,
    difficulty: str,
    question_type: str,
) -> QuestionPayload:
    correct = decode(result["correct_answer"])
    prompt = decode(result["question"])
    choices: list[str] | None = None

    if question_type == "multiple_choice":
        options = [decode(x) for x in result.get("incorrect_answers", [])]
        options.append(correct)
        random.shuffle(options)
        choices = options

    return QuestionPayload(
        id=question_id,
        difficulty=difficulty,
        question_type=question_type,
        prompt=prompt,
        choices=choices,
        answer=correct,
        explanation=f"The correct answer is: {correct}.",
    )


def api_true_false_question(
    result: dict[str, Any],
    question_id: int,
    difficulty: str,
) -> QuestionPayload:
    statement = decode(result["question"])
    answer = decode(result["correct_answer"])
    return QuestionPayload(
        id=question_id,
        difficulty=difficulty,
        question_type="true_false",
        prompt=statement,
        choices=["True", "False"],
        answer=answer,
        explanation=f"The statement is {answer}.",
    )


def generate_quiz(
    subject_key: str,
    total_questions: int,
    difficulty: str,
    focus_topic: str,
    selected_types: list[str],
) -> dict[str, Any]:
    content_difficulty = CONTENT_DIFFICULTY[difficulty]
    type_sequence = build_type_sequence(selected_types, total_questions)

    category_id = OPENTDB_CATEGORY.get(subject_key)
    tokens = focus_tokens(focus_topic)
    use_focus = bool(tokens) and category_id is not None

    multiple_pool: list[dict[str, Any]] = []
    boolean_pool: list[dict[str, Any]] = []
    matched_prompts: set[str] = set()

    if category_id is not None:
        # Never request more than exists, or the API returns an empty batch and we
        # would fall back to the small local bank (causing repeated questions).
        available = opentdb_available(category_id, content_difficulty)
        fallback_amount = min(50, max(total_questions * 2, 10))
        amount = min(50, available) if available > 0 else fallback_amount

        # One untyped request: it can never overshoot a per-type count (which would
        # return an empty batch), maximizes unique questions, and dodges the rate limit.
        raw = fetch_opentdb(category_id, content_difficulty, amount)
        if use_focus:
            matched = [r for r in raw if result_matches_focus(r, tokens)]
            others = [r for r in raw if r not in matched]
            matched_prompts = {decode(r["question"]) for r in matched}
            ordered = matched + others
        else:
            ordered = raw
        for result in ordered:
            if result.get("type") == "boolean":
                boolean_pool.append(result)
            else:
                multiple_pool.append(result)

    questions: list[QuestionPayload] = []
    mi = 0
    bi = 0
    for i, q_type in enumerate(type_sequence):
        qid = i + 1
        if q_type == "true_false":
            if bi < len(boolean_pool):
                questions.append(api_true_false_question(boolean_pool[bi], qid, difficulty))
                bi += 1
            else:
                tf_item = random.choice(TF_BANK[subject_key])
                questions.append(build_true_false_question(tf_item, qid, difficulty))
        else:
            if mi < len(multiple_pool):
                questions.append(api_choice_question(multiple_pool[mi], qid, difficulty, q_type))
                mi += 1
            else:
                template_item = random.choice(TEMPLATES[subject_key][content_difficulty])
                questions.append(build_choice_question(template_item, qid, difficulty, q_type))

    focus_matched = sum(1 for q in questions if q.prompt in matched_prompts)
    recommended_seconds = min(SECONDS_PER_DIFFICULTY[difficulty] * total_questions, 3600)

    return {
        "questions": questions,
        "recommended_seconds": recommended_seconds,
        "focus_matched": focus_matched,
        "subject_label": subject_label(subject_key),
        "adjusted_difficulty": difficulty,
    }


def grade_quiz(questions: list[QuestionPayload], answers: list[str]) -> dict[str, Any]:
    feedback: list[dict[str, Any]] = []
    correct_count = 0
    for question, user_answer in zip(questions, answers):
        is_correct = normalize_answer(question.answer) == normalize_answer(user_answer)
        if is_correct:
            correct_count += 1
        feedback.append(
            {
                "id": question.id,
                "question": question.prompt,
                "question_type": question.question_type,
                "difficulty": question.difficulty,
                "expected_answer": question.answer,
                "your_answer": user_answer,
                "is_correct": is_correct,
                "explanation": question.explanation,
            }
        )

    total = len(questions)
    score_percent = round((correct_count / total) * 100.0, 2) if total else 0.0
    return {
        "score_percent": score_percent,
        "correct_count": correct_count,
        "total": total,
        "next_difficulty": suggest_difficulty(score_percent),
        "feedback": feedback,
    }


def format_seconds(total_seconds: int) -> str:
    minutes, seconds = divmod(max(0, int(total_seconds)), 60)
    return f"{minutes:02d}:{seconds:02d}"


def serialize_questions(questions: list[QuestionPayload]) -> str:
    return json.dumps([q.model_dump() for q in questions])


def deserialize_questions(raw: str) -> list[QuestionPayload]:
    try:
        data = json.loads(raw) if raw else []
        return [QuestionPayload(**item) for item in data]
    except (ValueError, TypeError):
        return []


def parse_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        return max(low, min(high, int(str(value))))
    except (ValueError, TypeError):
        return default


def latin1(text: str) -> str:
    """fpdf core fonts use latin-1; drop characters it cannot encode."""
    return str(text).encode("latin-1", "replace").decode("latin-1")


def build_quiz_csv(questions: list[QuestionPayload]) -> str:
    header = ["id", "type", "difficulty", "prompt", "choices", "answer"]
    rows = [",".join(header)]
    for q in questions:
        cells = [
            str(q.id),
            q.question_type,
            q.difficulty,
            q.prompt.replace('"', '""'),
            " | ".join(q.choices or []).replace('"', '""'),
            q.answer.replace('"', '""'),
        ]
        rows.append(",".join(f'"{cell}"' for cell in cells))
    return "\n".join(rows)


def build_result_pdf(meta: dict[str, Any], result: dict[str, Any]) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def line(text: str, height: float = 6.0) -> None:
        pdf.multi_cell(0, height, latin1(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(26, 31, 54)
    line("QuestGen - Result Sheet", 10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(110, 115, 144)
    line("Built by Rejoice Akosua Dzanku")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(26, 31, 54)
    for info_line in [
        f"Topic: {meta['subject_label']}",
        f"Difficulty: {meta['adjusted_difficulty']}",
        f"Score: {result['score_percent']}%  ({result['correct_count']}/{result['total']} correct)",
        f"Suggested next level: {result['next_difficulty']}",
        f"Time taken: {meta['time_taken']} (limit {meta['time_limit']})",
    ]:
        line(info_line)
    pdf.ln(3)

    for item in result["feedback"]:
        pdf.set_font("Helvetica", "B", 11)
        if item["is_correct"]:
            pdf.set_text_color(22, 163, 74)
            verdict = "[CORRECT]"
        else:
            pdf.set_text_color(220, 38, 38)
            verdict = "[WRONG]"
        line(f"Q{item['id']} {verdict}  {item['question']}")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(26, 31, 54)
        line(f"Your answer: {item['your_answer'] or '(no answer)'}", 5)
        if not item["is_correct"]:
            line(f"Correct answer: {item['expected_answer']}", 5)
        pdf.ln(3)

    return bytes(pdf.output())


app = FastAPI(title="Smart Question Generator")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def category_options() -> list[dict[str, str]]:
    return [{"value": key, "label": subject_label(key)} for key in sorted(TEMPLATES.keys(), key=subject_label)]


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "categories": category_options(),
            "difficulty_levels": DIFFICULTY_LEVELS,
            "error": None,
        },
    )


@app.post("/quiz", response_class=HTMLResponse)
async def quiz(request: Request) -> HTMLResponse:
    form = await request.form()

    subject_key = str(form.get("subject", "")).strip().lower()
    if subject_key not in TEMPLATES:
        subject_key = "general"

    difficulty = str(form.get("difficulty", "medium")).strip().lower()
    if difficulty not in DIFFICULTY_LEVELS:
        difficulty = "medium"

    total_questions = parse_int(form.get("total_questions"), default=8, low=1, high=30)
    focus_topic = str(form.get("focus_topic", "")).strip()

    selected_types = selected_types_from_flags(
        include_mc=form.get("multiple_choice") is not None,
        include_short=form.get("short_answer") is not None,
        include_tf=form.get("true_false") is not None,
    )
    if not selected_types:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "categories": category_options(),
                "difficulty_levels": DIFFICULTY_LEVELS,
                "error": "Please select at least one question type.",
            },
        )

    data = generate_quiz(subject_key, total_questions, difficulty, focus_topic, selected_types)

    return templates.TemplateResponse(
        request,
        "quiz.html",
        {
            "questions": data["questions"],
            "questions_json": serialize_questions(data["questions"]),
            "recommended_seconds": data["recommended_seconds"],
            "time_label": format_seconds(data["recommended_seconds"]),
            "subject_label": data["subject_label"],
            "difficulty": difficulty,
            "focus_topic": focus_topic,
            "focus_matched": data["focus_matched"],
            "start_ts": time.time(),
        },
    )


@app.post("/result", response_class=HTMLResponse)
async def result(request: Request) -> HTMLResponse:
    form = await request.form()
    questions = deserialize_questions(str(form.get("questions", "")))
    answers = [str(form.get(f"answer_{q.id}", "")) for q in questions]

    graded = grade_quiz(questions, answers)

    recommended_seconds = parse_int(form.get("recommended_seconds"), default=0, low=0, high=3600)
    try:
        elapsed = max(0, int(time.time() - float(form.get("start_ts", 0))))
    except (ValueError, TypeError):
        elapsed = 0
    if recommended_seconds:
        elapsed = min(elapsed, recommended_seconds)

    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "result": graded,
            "subject_label": str(form.get("subject_label", "")),
            "difficulty": str(form.get("difficulty", "")),
            "time_taken": format_seconds(elapsed),
            "time_limit": format_seconds(recommended_seconds),
            "over_time": bool(recommended_seconds) and elapsed >= recommended_seconds,
            "questions_json": str(form.get("questions", "")),
            "answers_json": json.dumps(answers),
        },
    )


@app.post("/export/json")
async def export_json(request: Request) -> Response:
    form = await request.form()
    questions = deserialize_questions(str(form.get("questions", "")))
    content = json.dumps([q.model_dump() for q in questions], indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=questgen-questions.json"},
    )


@app.post("/export/csv")
async def export_csv(request: Request) -> Response:
    form = await request.form()
    questions = deserialize_questions(str(form.get("questions", "")))
    return Response(
        content=build_quiz_csv(questions),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=questgen-questions.csv"},
    )


@app.post("/export/pdf")
async def export_pdf(request: Request) -> Response:
    form = await request.form()
    questions = deserialize_questions(str(form.get("questions", "")))
    try:
        answers = json.loads(str(form.get("answers", "[]")))
    except ValueError:
        answers = []
    graded = grade_quiz(questions, [str(a) for a in answers])

    meta = {
        "subject_label": str(form.get("subject_label", "")),
        "adjusted_difficulty": str(form.get("difficulty", "")),
        "time_taken": str(form.get("time_taken", "00:00")),
        "time_limit": str(form.get("time_limit", "00:00")),
    }
    pdf_bytes = build_result_pdf(meta, graded)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=questgen-result-sheet.pdf"},
    )
