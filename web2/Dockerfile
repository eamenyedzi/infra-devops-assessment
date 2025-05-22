FROM nginx:alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY *.html /usr/share/nginx/html/
COPY *.css /usr/share/nginx/html/

# Fix all permission-sensitive dirs
RUN mkdir -p /run && \
    chown -R appuser:appgroup /run /var/cache/nginx /var/run /etc/nginx /usr/share/nginx/html

USER appuser

EXPOSE 80

# Only override daemon mode
CMD ["nginx", "-g", "daemon off;"]

