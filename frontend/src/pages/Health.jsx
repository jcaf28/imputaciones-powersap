// PATH: frontend/src/pages/Health.jsx

export const meta = {
  label: "Health", // nombre para el sidebar
  priority: 98,
  devOnly: true              // orden de aparición
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
