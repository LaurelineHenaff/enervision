# Étapes :
# - dev   : serveur de développement Angular, utilisé par docker-compose.yml (target: dev)
# - build : compilation de production
# - prod  : serveur SSR Node, image publiée par la CI pour le staging et la production (étape par défaut)

FROM node:24-slim AS base

# Hôtes acceptés par le rendu SSR d'Angular (protection SSRF)
ENV NG_ALLOWED_HOSTS=localhost,127.0.0.1

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

FROM base AS dev

RUN chown -R node:node /app
USER node

EXPOSE 4000

CMD ["npx", "ng", "serve", "--host", "0.0.0.0", "--port", "4000", "--poll", "1000"]

FROM base AS build

RUN npm run build

FROM node:24-slim AS prod

# NG_ALLOWED_HOSTS doit lister le nom ou l'IP de la VM en staging et en production
ENV NODE_ENV=production \
    NG_ALLOWED_HOSTS=localhost,127.0.0.1 \
    PORT=4000

WORKDIR /app

COPY --from=build --chown=node:node /app/dist ./dist

USER node

EXPOSE 4000

CMD ["node", "dist/enervision/server/server.mjs"]
