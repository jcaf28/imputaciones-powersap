// PATH: frontend/src/pages/Get.jsx

import { useState } from 'react';
import { getTiposOrdenes } from '../services/tiposOrdenesService';

export const meta = {
  label: "Get",
  priority: 6
};

export default function ObtenerFeedback() {
  const [registros, setRegistros] = useState([]);
  const [error, setError] = useState(null);

  async function handleClick() {
    try {
      const data = await getTiposOrdenes();
      setRegistros(data);
      setError(null);
    } catch (e) {
      setError(e.message);
      setRegistros([]);
    }
  }

  return (
    <div>
      <h1>Listado TiposOrdenes</h1>
      <button onClick={handleClick}>
        Cargar TiposOrdenes
      </button>

      {registros.map((item) => (
        <div key={item.TipoOrden}>
          {item.TipoOrden} - {item.Nombre} - Grupo: {item.Grupo}
        </div>
      ))}

      {error && <div style={{ color: 'red' }}>{error}</div>}
    </div>
  );
}
