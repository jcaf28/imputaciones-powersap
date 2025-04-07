// PATH: frontend/src/pages/ObtenerFeedback.jsx

export const meta = {
  label: "Obtener Feedback", // nombre para el sidebar
  priority: 5                // orden de aparición
};

import { useState } from 'react';
import { getHealth } from '../services/healthService';

export default function ObtenerFeedback() {
  const [respuesta, setRespuesta] = useState(null);
  const [error, setError] = useState(null);

  async function handleClick() {
    try {
      const data = await getHealth();
      console.log('Respuesta:', data);
      setRespuesta(data);
      setError(null);
    } catch (e) {
      console.error(e);
      setRespuesta(null);
      setError(e.message);
    }
  }

  return (
    <div>
      <h1>Hola soy la página LoQueSea</h1>
      <button onClick={handleClick}>
        Obtener Health
      </button>

      {respuesta && (
        <div style={{ marginTop: '1rem', color: 'green' }}>
          <strong>Respuesta del backend:</strong> {JSON.stringify(respuesta)}
        </div>
      )}

      {error && (
        <div style={{ marginTop: '1rem', color: 'red' }}>
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
}
