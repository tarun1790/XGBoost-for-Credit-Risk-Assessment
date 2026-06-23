FROM node:18-alpine

WORKDIR /app

# Copy packages and install
COPY package.json .
RUN npm install

# Copy source code
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
