FROM node:alpine as build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

RUN npm run build

FROM nginxinc/nginx-unprivileged as serve
WORKDIR /app
COPY --from=build /app/dist /app/
COPY nginx.conf /etc/nginx
EXPOSE 5173