from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class AstronomySubfield:
    name: str
    description: str
    current_challenges: List[str]
    required_skills: List[str]
    related_fields: List[str]

# Database of astronomy subfields
ASTRONOMY_SUBFIELDS = [
    AstronomySubfield(
        name="Exoplanet Detection and Characterization",
        description="Study of planets orbiting stars outside our solar system, including detection methods, atmospheric composition, and habitability factors.",
        current_challenges=[
            "Detecting Earth-like planets in habitable zones",
            "Characterizing exoplanet atmospheres with current instruments",
            "Understanding formation and evolution of diverse planetary systems",
            "Developing new detection methods for smaller planets"
        ],
        required_skills=[
            "Data analysis", "Signal processing", "Spectroscopy", 
            "Statistical methods", "Programming (Python)"
        ],
        related_fields=["Planetary science", "Astrobiology", "Stellar astronomy"]
    ),
    AstronomySubfield(
        name="Galaxy Formation and Evolution",
        description="Study of how galaxies form, evolve, and interact across cosmic time.",
        current_challenges=[
            "Understanding the role of dark matter in galaxy formation",
            "Reconstructing galaxy merger histories",
            "Explaining galactic morphology diversity",
            "Connecting star formation to galactic environment"
        ],
        required_skills=[
            "Computational modeling", "Observational techniques", 
            "Data analysis", "Programming", "Statistics"
        ],
        related_fields=["Cosmology", "Stellar astrophysics", "Computational physics"]
    ),
    AstronomySubfield(
        name="Stellar Astrophysics",
        description="Study of the physics, formation, and evolution of stars.",
        current_challenges=[
            "Modeling complex stellar interiors",
            "Understanding stellar magnetic fields and activity cycles",
            "Explaining stellar mass loss mechanisms",
            "Characterizing stellar populations in different environments"
        ],
        required_skills=[
            "Nuclear physics", "Fluid dynamics", "Spectroscopy", 
            "Computational modeling", "Data analysis"
        ],
        related_fields=["Nuclear physics", "Plasma physics", "Galactic astronomy"]
    ),
    AstronomySubfield(
        name="Observational Cosmology",
        description="Study of the large-scale structure, evolution, and fate of the universe through observations.",
        current_challenges=[
            "Resolving the Hubble tension",
            "Mapping dark energy properties across cosmic time",
            "Understanding cosmic reionization",
            "Detecting gravitational waves from the early universe"
        ],
        required_skills=[
            "Statistical analysis", "Survey techniques", "Image processing", 
            "Spectroscopy", "Programming", "Theoretical modeling"
        ],
        related_fields=["Theoretical cosmology", "Particle physics", "Galaxy evolution"]
    ),
    AstronomySubfield(
        name="Multi-messenger Astronomy",
        description="Integration of information from different astronomical messengers: electromagnetic radiation, gravitational waves, neutrinos, and cosmic rays.",
        current_challenges=[
            "Rapid follow-up of transient events",
            "Correlating signals from different messengers",
            "Understanding extreme astrophysical environments",
            "Building comprehensive models from diverse data types"
        ],
        required_skills=[
            "Signal processing", "Real-time data analysis", "Programming", 
            "Statistics", "Knowledge of multiple detector physics"
        ],
        related_fields=["High-energy astrophysics", "Gravitational physics", "Neutrino physics"]
    ),
    AstronomySubfield(
        name="Astronomical Instrumentation",
        description="Development and improvement of instruments and techniques for astronomical observations.",
        current_challenges=[
            "Building more sensitive detectors across the electromagnetic spectrum",
            "Developing adaptive optics for ground-based telescopes",
            "Creating more efficient spectrographs",
            "Advancing data processing pipelines for large surveys"
        ],
        required_skills=[
            "Optics", "Electronics", "Signal processing", "Programming", 
            "Mechanical engineering", "Cryogenics"
        ],
        related_fields=["Engineering", "Computer science", "Optics"]
    ),
    AstronomySubfield(
        name="Astrobiology",
        description="Study of the origin, evolution, and distribution of life in the universe.",
        current_challenges=[
            "Defining biosignatures for remote detection",
            "Understanding extremophile adaptations",
            "Modeling habitable environments beyond Earth",
            "Developing techniques to detect microbial life remotely"
        ],
        required_skills=[
            "Biology", "Chemistry", "Geology", "Spectroscopy", 
            "Data analysis", "Interdisciplinary thinking"
        ],
        related_fields=["Exoplanet science", "Biochemistry", "Planetary science"]
    ),
    AstronomySubfield(
        name="Solar Physics",
        description="Study of the Sun, its structure, dynamics, and impact on the solar system.",
        current_challenges=[
            "Understanding the solar dynamo and activity cycle",
            "Predicting solar flares and coronal mass ejections",
            "Explaining coronal heating",
            "Modeling solar wind-planetary interactions"
        ],
        required_skills=[
            "Plasma physics", "Magnetohydrodynamics", "Image processing", 
            "Time series analysis", "Programming"
        ],
        related_fields=["Plasma physics", "Space weather", "Stellar astrophysics"]
    )
]
