// PATH: frontend/src/components/ProcessLogger.jsx

import { Box, Typography, useTheme } from "@mui/material";
import PropTypes from "prop-types";

export default function ProcessLogger({ logs = [], title = "Proceso" }) {
  const theme = useTheme();

  return (
    <Box
      sx={{
        backgroundColor: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        padding: 2,
        borderRadius: 2,
        fontFamily: "monospace",
        fontSize: "0.9rem",
        maxHeight: 300,
        overflowY: "auto",
        whiteSpace: "pre-wrap"
      }}
    >
      <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
        {title}
      </Typography>
      {logs.length > 0 ? (
        logs.map((line, index) => (
          <Typography
            key={index}
            variant="body2"
            component="div"
            sx={{ color: theme.palette.text.primary }}
          >
            {line}
          </Typography>
        ))
      ) : (
        <Typography variant="body2" color="text.secondary">
          Sin mensajes aún...
        </Typography>
      )}
    </Box>
  );
}

ProcessLogger.propTypes = {
  logs: PropTypes.arrayOf(PropTypes.string),
  title: PropTypes.string
};
