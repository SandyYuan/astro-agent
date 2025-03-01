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
            "Characterizing exoplanet atmospheres with JWST and ground-based facilities",
            "Understanding formation and evolution of diverse planetary systems",
            "Detecting potential biosignatures in rocky planet atmospheres",
            "Advancing direct imaging techniques for close-in exoplanets"
        ],
        required_skills=[
            "Data analysis", "Signal processing", "Spectroscopy", 
            "Statistical methods", "Programming (Python)"
        ],
        related_fields=["Planetary science", "Astrobiology", "Stellar astronomy", "Atmospheric physics"]
    ),
    AstronomySubfield(
        name="Galaxy Formation and Evolution",
        description="Study of how galaxies form, evolve, and interact across cosmic time.",
        current_challenges=[
            "Understanding the role of dark matter in galaxy formation",
            "Reconstructing galaxy merger histories",
            "Explaining galactic morphology diversity",
            "Connecting star formation to galactic environment",
            "Resolving the 'missing satellite' and 'too-big-to-fail' problems",
            "Understanding galaxy-AGN co-evolution"
        ],
        required_skills=[
            "Computational modeling", "Observational techniques", 
            "Data analysis", "Programming", "Statistics"
        ],
        related_fields=["Cosmology", "Stellar astrophysics", "Computational physics", "High-energy astrophysics"]
    ),
    AstronomySubfield(
        name="Stellar Astrophysics",
        description="Study of the physics, formation, and evolution of stars.",
        current_challenges=[
            "Modeling complex stellar interiors",
            "Understanding stellar magnetic fields and activity cycles",
            "Explaining stellar mass loss mechanisms",
            "Characterizing stellar populations in different environments",
            "Modeling binary star evolution and common envelope physics",
            "Understanding stellar rotation and mixing processes"
        ],
        required_skills=[
            "Nuclear physics", "Fluid dynamics", "Spectroscopy", 
            "Computational modeling", "Data analysis"
        ],
        related_fields=["Nuclear physics", "Plasma physics", "Galactic astronomy", "Stellar evolution"]
    ),
    AstronomySubfield(
        name="Observational Cosmology",
        description="Study of the large-scale structure, evolution, and fate of the universe through observations.",
        current_challenges=[
            "Resolving the Hubble tension and S8 tension",
            "Mapping dark energy properties using BAO and weak lensing",
            "Understanding cosmic reionization processes",
            "Constraining inflation models and primordial gravitational waves",
            "Measuring non-Gaussianity in the CMB",
            "Mapping the cosmic web's gas content with Lyman-alpha forest observations"
        ],
        required_skills=[
            "Statistical analysis", "Survey techniques", "Image processing", 
            "Spectroscopy", "Programming", "Theoretical modeling"
        ],
        related_fields=["Theoretical cosmology", "Particle physics", "Galaxy evolution", "CMB studies"]
    ),
    AstronomySubfield(
        name="Multi-messenger Astronomy",
        description="Integration of information from different astronomical messengers: electromagnetic radiation, gravitational waves, neutrinos, and cosmic rays.",
        current_challenges=[
            "Rapid follow-up of transient events",
            "Correlating signals from different messengers",
            "Understanding extreme astrophysical environments",
            "Building comprehensive models from diverse data types",
            "Identifying sources of high-energy neutrinos",
            "Detecting continuous gravitational waves from neutron stars"
        ],
        required_skills=[
            "Signal processing", "Real-time data analysis", "Programming", 
            "Statistics", "Knowledge of multiple detector physics"
        ],
        related_fields=["High-energy astrophysics", "Gravitational physics", "Neutrino physics", "Time-domain astronomy"]
    ),
    AstronomySubfield(
        name="Astronomical Instrumentation",
        description="Development and improvement of instruments and techniques for astronomical observations.",
        current_challenges=[
            "Building more sensitive detectors across the electromagnetic spectrum",
            "Developing adaptive optics for ground-based telescopes",
            "Creating more efficient spectrographs",
            "Advancing data processing pipelines for large surveys",
            "Implementing quantum sensors for ultra-sensitive measurements",
            "Developing AI/ML for instrument control and calibration"
        ],
        required_skills=[
            "Optics", "Electronics", "Signal processing", "Programming", 
            "Mechanical engineering", "Cryogenics"
        ],
        related_fields=["Engineering", "Computer science", "Optics", "Data science"]
    ),
    AstronomySubfield(
        name="Astrobiology",
        description="Study of the origin, evolution, and distribution of life in the universe.",
        current_challenges=[
            "Defining biosignatures for remote detection",
            "Understanding extremophile adaptations",
            "Modeling habitable environments beyond Earth",
            "Developing techniques to detect microbial life remotely",
            "Characterizing the origins of organic molecules in space",
            "Assessing the prevalence of habitable worlds"
        ],
        required_skills=[
            "Biology", "Chemistry", "Geology", "Spectroscopy", 
            "Data analysis", "Interdisciplinary thinking"
        ],
        related_fields=["Exoplanet science", "Biochemistry", "Planetary science", "Evolutionary biology"]
    ),
    AstronomySubfield(
        name="Solar Physics",
        description="Study of the Sun, its structure, dynamics, and impact on the solar system.",
        current_challenges=[
            "Understanding the solar dynamo and activity cycle",
            "Predicting solar flares and coronal mass ejections",
            "Explaining coronal heating",
            "Modeling solar wind-planetary interactions",
            "Characterizing the Sun's interior with helioseismology",
            "Understanding magnetic reconnection processes"
        ],
        required_skills=[
            "Plasma physics", "Magnetohydrodynamics", "Image processing", 
            "Time series analysis", "Programming"
        ],
        related_fields=["Plasma physics", "Space weather", "Stellar astrophysics", "Heliophysics"]
    ),
    AstronomySubfield(
        name="High-Energy Astrophysics",
        description="Study of extremely energetic processes and objects in the universe, including black holes, neutron stars, and active galactic nuclei.",
        current_challenges=[
            "Testing general relativity in strong-field regimes",
            "Understanding accretion physics around compact objects",
            "Characterizing the population of intermediate-mass black holes",
            "Explaining the physics of relativistic jets",
            "Modeling supernova explosions and their remnants",
            "Understanding gamma-ray burst mechanisms"
        ],
        required_skills=[
            "Relativistic physics", "X-ray and gamma-ray astronomy techniques", 
            "Computational modeling", "Data analysis", "Programming"
        ],
        related_fields=["Theoretical physics", "Particle physics", "Cosmology", "Multi-messenger astronomy"]
    ),
    AstronomySubfield(
        name="Planetary Science (Solar System)",
        description="Study of planets, moons, asteroids, comets, and other bodies in our solar system, their compositions, dynamics, and histories.",
        current_challenges=[
            "Characterizing ocean worlds (Europa, Enceladus) for potential habitability",
            "Understanding atmospheric dynamics of gas giants",
            "Determining the composition and structure of Kuiper Belt objects",
            "Mapping the distribution of volatiles on Mars and the Moon",
            "Reconstructing the early dynamical history of the solar system",
            "Understanding the processes that shape planetary surfaces"
        ],
        required_skills=[
            "Geology", "Atmospheric science", "Remote sensing", 
            "Spectroscopy", "Orbital dynamics", "GIS techniques"
        ],
        related_fields=["Geology", "Atmospheric science", "Astrobiology", "Space exploration"]
    ),
    AstronomySubfield(
        name="Interstellar Medium and Star Formation",
        description="Study of the gas and dust between stars and the processes by which this material collapses to form new stars and planetary systems.",
        current_challenges=[
            "Understanding molecular cloud collapse mechanisms",
            "Characterizing magnetic field structures in star-forming regions",
            "Modeling turbulence in the interstellar medium",
            "Tracing the evolution from prestellar cores to protostars",
            "Understanding the role of feedback in regulating star formation",
            "Characterizing the chemical evolution of star-forming regions"
        ],
        required_skills=[
            "Radio astronomy", "Infrared astronomy", "Magnetohydrodynamics", 
            "Computational modeling", "Molecular spectroscopy", "Data analysis"
        ],
        related_fields=["Stellar astrophysics", "Astrochemistry", "Galaxy evolution", "Molecular physics"]
    ),
    AstronomySubfield(
        name="Time-Domain Astronomy",
        description="Study of astronomical objects that change or vary with time, including transients, variables, and moving objects.",
        current_challenges=[
            "Rapid classification of transient events",
            "Understanding unusual transient classes (e.g., fast radio bursts)",
            "Coordinating multi-facility follow-up campaigns",
            "Developing efficient methods to process the coming flood of time-domain data",
            "Characterizing stellar variability across different populations",
            "Detecting and tracking potentially hazardous near-Earth objects"
        ],
        required_skills=[
            "Time series analysis", "Machine learning", "Real-time data processing", 
            "Observational techniques", "Programming", "Statistical methods"
        ],
        related_fields=["Multi-messenger astronomy", "Stellar astrophysics", "Survey science", "Data science"]
    )
]
