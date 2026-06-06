FROM node:22-alpine

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
ARG NEXT_PUBLIC_KB_API_KEY=change-this-secret

ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_KB_API_KEY=$NEXT_PUBLIC_KB_API_KEY

WORKDIR /app

COPY frontend/package.json /app/package.json

RUN npm install

COPY frontend /app

RUN npm run build

CMD ["npm", "run", "start"]
