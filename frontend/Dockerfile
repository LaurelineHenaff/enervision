FROM node:24-slim

# Hôtes acceptés par le rendu SSR d'Angular (protection SSRF)
ENV NG_ALLOWED_HOSTS=localhost,127.0.0.1

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

RUN chown -R node:node /app
USER node

EXPOSE 4000

CMD ["npx", "ng", "serve", "--host", "0.0.0.0", "--port", "4000", "--poll", "1000"]
