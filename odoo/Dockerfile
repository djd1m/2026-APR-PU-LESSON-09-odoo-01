FROM odoo:19

USER root

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Copy custom addons
COPY addons/ /mnt/extra-addons/

# Copy Odoo configuration
COPY config/ /etc/odoo/

# Copy and set up startup validation script
COPY scripts/validate-startup.py /usr/local/bin/validate-startup.py
RUN chmod +x /usr/local/bin/validate-startup.py

# Ensure correct ownership
RUN chown -R odoo:odoo /mnt/extra-addons /etc/odoo

USER odoo

# Validate environment before starting Odoo
ENTRYPOINT ["/bin/bash", "-c", "python3 /usr/local/bin/validate-startup.py && exec /entrypoint.sh \"$@\"", "--"]
CMD ["odoo"]

EXPOSE 8069 8072

HEALTHCHECK --interval=15s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8069/web/health || exit 1
