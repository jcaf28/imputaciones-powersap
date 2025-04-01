// PATH: frontend/src/hooks/useSSE.js

// Este hook se encarga de manejar los eventos de Server-Sent Events (SSE) de una forma más sencilla.
// Se encarga de abrir la conexión, manejar los eventos y cerrar la conexión cuando sea necesario.

import { useEffect, useRef, useState } from "react";

export default function useSSE(url) {
  const [events, setEvents] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    if (!url) return;

    const es = new EventSource(url);
    eventSourceRef.current = es;
    setIsOpen(true);

    es.onopen = () => {
      console.log("SSE connection opened");
    };

    es.onmessage = (e) => {
      // Por defecto, 'onmessage' es para event-type 'message' sin nombre.
      // Podrías almacenarlo en tu estado
      setEvents(prev => [...prev, { type: "message", data: e.data }]);
    };

    es.addEventListener("completed", (e) => {
      setEvents(prev => [...prev, { type: "completed", data: e.data }]);
      es.close();
      setIsOpen(false);
    });

    es.addEventListener("cancelled", (e) => {
      setEvents(prev => [...prev, { type: "cancelled", data: e.data }]);
      es.close();
      setIsOpen(false);
    });

    es.addEventListener("error", (e) => {
      setEvents(prev => [...prev, { type: "error", data: e.data }]);
      es.close();
      setIsOpen(false);
    });

    return () => {
      es.close();
      setIsOpen(false);
    };
  }, [url]);

  return { events, isOpen };
}
