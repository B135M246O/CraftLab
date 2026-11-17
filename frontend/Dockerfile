FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --legacy-peer-deps --no-audit --no-fund
COPY . ./
RUN npm run build
CMD ["sh", "-c", "cp -r build/. /result/"]
