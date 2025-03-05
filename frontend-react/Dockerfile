FROM node:20-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of your React app code
COPY . .

# Expose port 3000 for the React dev server
EXPOSE 3000

# Start the development server
CMD ["npm", "start"]
