# PATH: frontend/Dockerfile

# ========================
# STAGE 1: Desarrollo
# ========================
FROM node:20-alpine AS dev
ARG SERVICE_NAME
ARG FRONTEND_PORT
ARG BACKEND_PORT

# Para que Vite lea import.meta.env.VITE_SERVICE_NAME, etc.
ENV VITE_SERVICE_NAME=$SERVICE_NAME
ENV VITE_FRONTEND_PORT=$FRONTEND_PORT
ENV VITE_BACKEND_PORT=$BACKEND_PORT

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# Exponemos el puerto de Vite (en Docker Compose lo mapeamos al host)
EXPOSE $FRONTEND_PORT
CMD ["npm", "run", "dev"]

# ========================
# STAGE 2: Build de producción
# ========================
FROM node:20-alpine AS build
ARG SERVICE_NAME
ARG FRONTEND_PORT

ENV VITE_SERVICE_NAME=$SERVICE_NAME
ENV VITE_FRONTEND_PORT=$FRONTEND_PORT
ENV VITE_BACKEND_PORT=$BACKEND_PORT

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ========================
# STAGE 3: Imagen final con Nginx
# ========================
FROM nginx:alpine AS prod

# Copiamos la plantilla de config con variables ${SERVICE_NAME}
COPY default.conf.template /etc/nginx/templates/default.conf.template

# Recogemos el mismo SERVICE_NAME en la etapa final para envsubst
ARG SERVICE_NAME
ENV SERVICE_NAME=$SERVICE_NAME

# Copiamos la carpeta compilada (dist) desde la etapa build
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
RUN echo "Contenido de plantilla default.conf.template:" && cat /etc/nginx/templates/default.conf.template
CMD ["sh", "-c", "envsubst < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && cat /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]