ARG PYTHON_VERSION=3.10.4
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# RUN apt update && apt upgrade -y
# RUN apt install systemd
# RUN echo "vm.overcommit_memory=1" | tee -a /etc/sysctl.conf
# RUN systemctl vm.overcommit_memory=1

COPY . .
