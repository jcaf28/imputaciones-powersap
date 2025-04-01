// PATH: frontend/src/services/uploadEscaneosService.js

export async function startEscaneoProcess(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${import.meta.env.VITE_API_BASE_URL}/seguimiento-escaneos/start`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error("Error al iniciar el proceso de escaneos");
  }

  const data = await response.json();
  return data; // { process_id: "..." }
}

export async function cancelEscaneoProcess(processId) {
  const response = await fetch(
    `${import.meta.env.VITE_API_BASE_URL}/seguimiento-escaneos/cancel/${processId}`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    throw new Error("Error al cancelar el proceso de escaneos");
  }

  return await response.json(); // { message: "Proceso cancelado" }
}
