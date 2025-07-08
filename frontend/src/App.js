import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [eventTime, setEventTime] = useState('');
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const res = await axios.post('/api/recommend', {
      origin,
      destination,
      event_time: eventTime,
    });
    setResult(res.data);
  };

  return (
    <div style={{ maxWidth: 500, margin: '2rem auto', padding: 16, border: '1px solid #ccc', borderRadius: 8 }}>
      <h2>Kitsap Commute Helper</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Origin: <input value={origin} onChange={e => setOrigin(e.target.value)} required /></label>
        </div>
        <div>
          <label>Destination: <input value={destination} onChange={e => setDestination(e.target.value)} required /></label>
        </div>
        <div>
          <label>Event Time: <input type="datetime-local" value={eventTime} onChange={e => setEventTime(e.target.value)} required /></label>
        </div>
        <button type="submit">Get Recommendation</button>
      </form>
      {result && (
        <div style={{ marginTop: 24 }}>
          <h3>Recommendation</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
