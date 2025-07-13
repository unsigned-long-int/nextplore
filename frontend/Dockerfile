FROM node:20 AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-slim

WORKDIR /app
COPY --from=builder /app ./

RUN npm install -g serve

EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "5173"]
