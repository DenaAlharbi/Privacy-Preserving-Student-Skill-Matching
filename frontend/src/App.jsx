
import { useState } from "react";
import "./App.css";

const purposes = [
  {
    id: "course",
    icon: "🎓",
    title: "Course Project",
    description: "Find the right teammate for your next academic project.",
  },
  {
    id: "hackathon",
    icon: "💻",
    title: "Hackathon",
    description: "Connect with people ready to build something exciting.",
  },
  {
    id: "collaboration",
    icon: "🤝",
    title: "General Collaboration",
    description: "Discover people who share your interests and ideas.",
  },
  {
    id: "study",
    icon: "📚",
    title: "Study Group",
    description: "Find peers to learn, practice, and grow with.",
  },
];

const availableSkills = [
  "Python",
  "Java",
  "C++",
  "JavaScript",
  "AI",
  "Machine Learning",
  "Cybersecurity",
  "Web Development",
  "Mobile Development",
  "Databases",
  "Embedded Systems",
  "Cloud Computing",
  "Networking",
  "UI/UX Design",
  "Data Analysis",
  "Project Management",
];

function App() {
  const [selectedPurpose, setSelectedPurpose] = useState("course");
  const [continued, setContinued] = useState(false);

  const [selectedSkills, setSelectedSkills] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [threshold, setThreshold] = useState(2);
  const toggleSkill = (skill) => {
  setSelectedSkills((current) =>
    current.includes(skill)
      ? current.filter((item) => item !== skill)
      : [...current, skill]
  );
};

  const filteredSkills = availableSkills.filter((skill) =>
    skill.toLowerCase().includes(searchQuery.toLowerCase())
  );
  const selected = purposes.find(
    (purpose) => purpose.id === selectedPurpose
  );

  return (
    <main className="app-shell">

      <section className="hero">

        <h1>
          Great things start
          <br />
          <span className="gradient-text">together.</span>
        </h1>

        <p className="subtitle">
          Find your next teammate through shared skills and interests,
          without sharing your entire profile.
        </p>

        {!continued ? (
          <div className="selection-section">
            <div className="section-heading">
              <h2>What are you looking for?</h2>
              <p> </p>
            </div>

            <div className="purpose-grid">
              {purposes.map((purpose) => (
                <button
                  key={purpose.id}
                  type="button"
                  className={`purpose-card ${
                    selectedPurpose === purpose.id ? "selected" : ""
                  }`}
                  onClick={() => setSelectedPurpose(purpose.id)}
                  aria-pressed={selectedPurpose === purpose.id}
                >
                  <span className="purpose-icon">{purpose.icon}</span>
                  <span className="purpose-title">{purpose.title}</span>
                  <span className="purpose-description">
                    {purpose.description}
                  </span>

                  {selectedPurpose === purpose.id && (
                    <span className="selected-check">✓</span>
                  )}
                </button>
              ))}
            </div>

            <button
              className="continue-button"
              onClick={() => setContinued(true)}
            >
              Continue
            </button>

            <p className="footer-note">
              Your skills stay yours. Only permitted matches are revealed.
            </p>
          </div>
        ) : (
          
<div className="skills-screen">
  <button
    className="back-button"
    onClick={() => setContinued(false)}
  >
    Back
  </button>

  <div className="skills-header">
    <h2>What are your skills?</h2>
    <p>Select the skills and interests you'd like to match on.</p>
  </div>

  <div className="selected-purpose">
    <span>{selected.icon}</span>
    <div>
      <strong>{selected.title}</strong>
      <p>Your selected collaboration goal</p>
    </div>
  </div>

  <div className="skills-panel">
    <div className="skills-panel-heading">
      <h3>Select your skills</h3>
      <span>{selectedSkills.length} selected</span>
    </div>

    <input
      className="skill-search"
      type="text"
      placeholder="Search skills..."
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
    />

    <div className="skills-grid">
      {filteredSkills.map((skill) => (
        <button
          key={skill}
          type="button"
          className={`skill-chip ${
            selectedSkills.includes(skill) ? "active" : ""
          }`}
          onClick={() => toggleSkill(skill)}
          aria-pressed={selectedSkills.includes(skill)}
        >
          {selectedSkills.includes(skill) ? "✓ " : "+ "}
          {skill}
        </button>
      ))}
    </div>

    {filteredSkills.length === 0 && (
      <p className="empty-search">No matching skills found.</p>
    )}
  </div>

  <div className="threshold-panel">
    <div className="threshold-heading">
      <div>
        <h3>Minimum shared skills</h3>
        <p>How many skills should match?</p>
      </div>
      <span className="threshold-number">{threshold}</span>
    </div>

    <input
      type="range"
      min="1"
      max="5"
      value={threshold}
      onChange={(e) => setThreshold(Number(e.target.value))}
      className="threshold-slider"
    />

    <div className="slider-labels">
      <span>1 skill</span>
      <span>5 skills</span>
    </div>
  </div>

  <button
    className="continue-button"
    disabled={selectedSkills.length === 0}
    onClick={() =>
      alert(
        `Purpose: ${selected.title}\n` +
        `Skills: ${selectedSkills.join(", ")}\n` +
        `Threshold: ${threshold}`
      )
    }
      >
        Continue to Matching 
      </button>
    </div>

        )}
      </section>
    </main>
  );
}

export default App;
