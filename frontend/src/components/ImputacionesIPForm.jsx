// PATH: frontend/src/components/ImputacionesIPForm.jsx

import { Box, Button } from "@mui/material";
import FileUploadChecker from "./FileUploadChecker";

export default function ImputacionesIPForm({
  files,
  validations,
  setFile,
  validateFile,
  canGenerate,
  onGenerate,
  isUploading,
}) {
  return (
    <Box sx={{ mt: 4 }}>

      {/** Renderizamos 4 FileUploadChecker, uno para cada archivo */}
      <FileUploadChecker
        label="Archivo 1: WBS por clave"
        index={0}
        file={files[0]}
        validated={validations[0]}
        onFileChange={setFile}
        onValidate={validateFile}
      />

      <FileUploadChecker
        label="Archivo 2: Listado Usuarios"
        index={1}
        file={files[1]}
        validated={validations[1]}
        onFileChange={setFile}
        onValidate={validateFile}
      />

      <FileUploadChecker
        label="Archivo 3: Imputaciones programa informático"
        index={2}
        file={files[2]}
        validated={validations[2]}
        onFileChange={setFile}
        onValidate={validateFile}
      />

      <FileUploadChecker
        label="Archivo 4: Fichajes SAP"
        index={3}
        file={files[3]}
        validated={validations[3]}
        onFileChange={setFile}
        onValidate={validateFile}
      />

      <Box sx={{ mt: 4 }}>
        <Button
          variant="contained"
          color="primary"
          onClick={onGenerate}
          disabled={!canGenerate || isUploading}
        >
          Generar archivo
        </Button>
      </Box>
    </Box>
  );
}
