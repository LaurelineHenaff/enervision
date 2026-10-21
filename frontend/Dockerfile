# Étapes :
# - dev   : serveur de développement Angular, utilisé par docker-compose.yml (target: dev)
# - build : compilation de production
# - prod  : nginx qui sert l'application compilée et transmet /api/ à l'API (variable API_UPSTREAM,
#           lue au lancement). Image publiée par la CI : la même pour le staging et la production
#           (étape par défaut)

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

FROM nginxinc/nginx-unprivileged:1.28-alpine AS prod

# Adresse de l'API vers laquelle nginx transmet /api/ (aucune adresse d'environnement n'est
# fixée à la construction)
ENV API_UPSTREAM=http://api:8000

COPY --from=build /app/dist/enervision/browser /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 8080
