# PATH: frontend/Dockerfile

# ========================
# STAGE 1: Desarrollo
# ========================
FROM node:20-alpine AS dev

WORKDIR /app
# Copiamos package.json y package-lock.json para instalar dependencias de forma reproducible
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

# Exponemos el puerto de Vite para desarrollo
EXPOSE 5173
CMD ["npm", "run", "dev"]

# ========================
# STAGE 2: Build de producción
# ========================
FROM node:20-alpine AS build

WORKDIR /app
# Copiamos solo los archivos necesarios
COPY package.json package-lock.json ./
# Instalamos solo las dependencias de producción
RUN npm ci
COPY . .
RUN npm run build

# ========================
# STAGE 3: Imagen final con Nginx
# ========================
FROM nginx:alpine AS prod

# Copiar config custom de Nginx (si es que la usas)
COPY default.conf /etc/nginx/conf.d/default.conf

# Copiar la carpeta compilada (dist) de la etapa de build
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
