// PATH: frontend/src/pages/ObtenerFeedback.jsx

export const meta = {
  label: "Obtener Feedback", // nombre para el sidebar
  priority: 5                // orden de aparición
};

import { getHealth } from '../services/healthService';

export default function LoQueSea() {
  async function handleClick() {
    try {
      const data = await getHealth();
      console.log('Respuesta:', data);
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div>
      <h1>Hola soy la página LoQueSea</h1>
      <button onClick={handleClick}>
        Obtener Health
      </button>
    </div>
  );
}