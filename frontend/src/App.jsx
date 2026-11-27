import { useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";
const THRESHOLD = 2;

const skills = [
  "Python",
  "AI",
  "Cybersecurity",
  "Web",
  "Databases",
  "Java",
  "JavaScript",
  "Machine Learning",
  "Cloud Computing",
  "Networking",
  "Embedded Systems",
  "UI/UX Design",
];

function App() {
  const [role, setRole] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [sessionInput, setSessionInput] = useState("");
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  function toggleSkill(skill) {
    setSelectedSkills((current) =>
      current.includes(skill)
        ? current.filter((item) => item !== skill)
        : [...current, skill]
    );
  }

  async function createSession() {
    setLoading(true);
    setMessage("");
    setResult(null);

    try {
      const response = await fetch(`${API}/sessions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          threshold: THRESHOLD,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not create session");
      }

      setSessionId(data.session_id);
      setRole("student-a");
      setMessage(
        `Session created. Share this code with Student B: ${data.session_id}`
      );
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  function joinSession() {
    if (!sessionInput.trim()) {
      setMessage("Enter the session code first.");
      return;
    }

    setSessionId(sessionInput.trim());
    setMessage(`Joined session: ${sessionInput.trim()}`);
  }

  async function submitSkills() {
    if (!sessionId) {
      setMessage("Create or join a session first.");
      return;
    }

    if (selectedSkills.length === 0) {
      setMessage("Select at least one skill.");
      return;
    }

    setLoading(true);
    setMessage("");
    setResult(null);

    try {
      const response = await fetch(
        `${API}/sessions/${sessionId}/${role}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            skills: selectedSkills,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not submit skills");
      }

      if (data.status === "ready") {
        setMessage("Both students submitted their skills.");
      } else {
        setMessage("Your skills were submitted. Waiting for the other student.");
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function checkResult() {
    if (!sessionId) {
      setMessage("Create or join a session first.");
      return;
    }

    setLoading(true);
    setMessage("");
    setResult(null);

    try {
      const response = await fetch(
        `${API}/sessions/${sessionId}/result`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "The result is not ready yet.");
      }

      setResult(data);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <h1>
          Privacy Preserving
          <br />
          <span className="gradient-text">Skill Matching</span>
        </h1>

        <p className="subtitle">
          Find shared skills without revealing them before the threshold is
          satisfied.
        </p>

        <div className="panel">
          <h2>1. Choose your role</h2>

          <div className="role-buttons">
            <button
              className={role === "student-a" ? "active" : ""}
              onClick={() => {
                setRole("student-a");
                setMessage("");
              }}
            >
              Student A
            </button>

            <button
              className={role === "student-b" ? "active" : ""}
              onClick={() => {
                setRole("student-b");
                setMessage("");
              }}
            >
              Student B
            </button>
          </div>

          <p className="threshold-info">
            Matching threshold is <strong>2 skills</strong>.
          </p>

          {role === "student-a" && !sessionId && (
            <button
              className="primary-button"
              onClick={createSession}
              disabled={loading}
            >
              Create matching session
            </button>
          )}

          {role === "student-b" && !sessionId && (
            <div className="join-box">
              <input
                type="text"
                placeholder="Enter Student A's session code"
                value={sessionInput}
                onChange={(event) => setSessionInput(event.target.value)}
              />

              <button
                className="primary-button"
                onClick={joinSession}
                disabled={loading}
              >
                Join session
              </button>
            </div>
          )}

          {sessionId && (
            <div className="session-info">
              <p>
                Session code: <strong>{sessionId}</strong>
              </p>

              <p>
                Role:{" "}
                <strong>
                  {role === "student-a" ? "Student A" : "Student B"}
                </strong>
              </p>
            </div>
          )}
        </div>

        {role && sessionId && (
          <div className="panel">
            <h2>2. Select your skills</h2>

            <div className="skills-grid">
              {skills.map((skill) => (
                <button
                  key={skill}
                  className={
                    selectedSkills.includes(skill)
                      ? "skill selected"
                      : "skill"
                  }
                  onClick={() => toggleSkill(skill)}
                >
                  {selectedSkills.includes(skill) ? "✓ " : "+ "}
                  {skill}
                </button>
              ))}
            </div>

            <p>
              Selected skills: <strong>{selectedSkills.length}</strong>
            </p>

            <button
              className="primary-button"
              onClick={submitSkills}
              disabled={loading}
            >
              Submit my skills
            </button>

            <button
              className="secondary-button"
              onClick={checkResult}
              disabled={loading}
            >
              Check matching result
            </button>
          </div>
        )}

        {message && <div className="message">{message}</div>}

        {result && (
          <div className="result-panel">
            <h2>Matching result</h2>

            <p>
              Threshold satisfied:{" "}
              <strong>
                {result.threshold_satisfied ? "Yes" : "No"}
              </strong>
            </p>

            {result.threshold_satisfied ? (
              <>
                <p>Common skills:</p>

                <ul>
                  {result.common_skills.map((skill) => (
                    <li key={skill}>{skill}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p>
                Threshold was not satisfied. No common skills were revealed.
              </p>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
export default App;
