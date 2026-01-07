import React, { useState } from 'react';
import './App.css';

// Default data from video_url.json provided in prompt
const DEFAULT_DATA = {
  "a_roll": {
    "url": "",
    "metadata": ""
  },
  "b_rolls": [
    {
      "id": "broll_1",
      "metadata": "",
      "url": ""
    }
  ]
};

function App() {
  const [data, setData] = useState(JSON.stringify(DEFAULT_DATA, null, 2));
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [videoPath, setVideoPath] = useState(null);
  const [error, setError] = useState(null);

  const handleGeneratePlan = async () => {
    setLoading(true);
    setError(null);
    try {
      const parsedData = JSON.parse(data);
      const response = await fetch('http://localhost:8000/generate-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsedData)
      });

      if (!response.ok) throw new Error(await response.text());
      const result = await response.json();
      setPlan(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRender = async () => {
    if (!plan || !plan.insertions) return;
    setRendering(true);
    try {
      const parsedData = JSON.parse(data);
      const payload = {
        a_roll_url: parsedData.a_roll.url,
        b_rolls: parsedData.b_rolls,
        insertions: plan.insertions
      };

      const response = await fetch('http://localhost:8000/render-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error(await response.text());
      const result = await response.json();
      setVideoPath(result.video_path);
    } catch (err) {
      setError(err.message);
    } finally {
      setRendering(false);
    }
  };

  return (
    <div className="container">
      <header>
        <h1>Flona AI Assignment</h1>
        <p>Broll Insertion System</p>
      </header>

      <div className="main-content">
        <section className="input-section">
          <h2>Input Data (JSON)</h2>
          <textarea
            value={data}
            onChange={(e) => setData(e.target.value)}
            rows={10}
          />
          <button onClick={handleGeneratePlan} disabled={loading}>
            {loading ? 'Analyzing & Planning...' : 'Generate Plan'}
          </button>
        </section>

        {error && <div className="error">{error}</div>}

        {plan && (
          <section className="plan-section">
            <h2>Generated Plan</h2>
            <div className="stats">
              <div className="stat">
                <span className="label">A-Roll Duration</span>
                <span className="value">{plan.a_roll_duration.toFixed(2)}s</span>
              </div>
              <div className="stat">
                <span className="label">Num Insertions</span>
                <span className="value">{plan.insertions.length}</span>
              </div>
            </div>

            <div className="transcript-section">
              <h3>Transcript</h3>
              <div className="transcript-list">
                {plan.transcript_segments.map((seg, idx) => (
                  <div key={idx} className="transcript-item">
                    <span className="time">[{seg.start.toFixed(1)}s - {seg.end.toFixed(1)}s]</span>
                    <span className="text">{seg.text}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="timeline">
              <h3>Insertion Plan</h3>
              {plan.insertions.map((ins, idx) => (
                <div key={idx} className="timeline-item">
                  <div className="time-marker">
                    {ins.start_sec.toFixed(1)}s - {(ins.start_sec + ins.duration_sec).toFixed(1)}s
                  </div>
                  <div className="content">
                    <h3>{ins.broll_id}</h3>
                    <p>{ins.reason}</p>
                    <div className="meta">
                      Confidence: {(ins.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <button className="render-btn" onClick={handleRender} disabled={rendering}>
              {rendering ? 'Rendering with FFmpeg...' : 'Render Final Video'}
            </button>

            {videoPath && (
              <div className="video-result">
                <h3>Render Complete!</h3>
                <p>Saved to: {videoPath}</p>
                {/* 
                  To play this, we'd need to serve the static file from backend.
                  For scope, we just confirm generation. 
                */}
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}

export default App;
