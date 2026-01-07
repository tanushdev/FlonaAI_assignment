FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 5173

# Run vite dev server accessible from outside
CMD ["npm", "run", "dev", "--", "--host"]
