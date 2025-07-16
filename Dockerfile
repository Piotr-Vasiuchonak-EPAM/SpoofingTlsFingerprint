# syntax=docker/dockerfile:1
FROM golang:1.22-alpine AS build

WORKDIR /app

# Install git and required tools
RUN apk add --no-cache git

# Copy go modules and download dependencies
COPY ./go.mod ./
COPY ./go.sum ./
RUN go mod download

# Copy the rest of the code
COPY . .

# Build binary
RUN go build -o spoofing-tls main.go

# --- Runtime image ---
FROM alpine:latest

WORKDIR /app

# CA certificates for HTTPS requests
RUN apk add --no-cache ca-certificates

# Copy binary from builder
COPY --from=build /app/spoofing-tls .

# Expose default port
EXPOSE 8000

# Command with default port, can be overridden
CMD ["./spoofing-tls", "8000"]
