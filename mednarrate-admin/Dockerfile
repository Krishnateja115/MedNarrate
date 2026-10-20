# MedNarrate admin portal (Next.js). Built for production: the API address is
# baked into the build and must be an HTTPS origin (see next.config.ts).
FROM node:22-slim

ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG MEDNARRATE_API_PROXY_URL
ENV MEDNARRATE_API_PROXY_URL=${MEDNARRATE_API_PROXY_URL}
RUN test -n "$MEDNARRATE_API_PROXY_URL" || (echo "MEDNARRATE_API_PROXY_URL build arg is required" && exit 1)
RUN npm run build

ENV NODE_ENV=production
RUN chown -R node:node /app/.next
USER node
EXPOSE 3000
CMD ["npx", "next", "start", "-p", "3000", "-H", "0.0.0.0"]
