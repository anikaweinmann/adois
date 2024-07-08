FROM python:3.8-slim-bullseye

RUN mkdir /adois

ARG ADOIS_VERSION="v0_0"

COPY requirements.txt /adois

RUN python -m pip install -r /adois/requirements.txt --ignore-installed --no-warn-script-location --upgrade
RUN python -m pip install huggingface_hub[cli]==0.20.3

COPY . /adois
WORKDIR /adois

ENV PYTHONPATH "${PYTHONPATH}:/adois"
ENV PYTHONUNBUFFERED=1

RUN huggingface-cli download geospaitial-lab/adois "models/adois_${ADOIS_VERSION}.onnx" --local-dir data && \
    mv data/models/adois_${ADOIS_VERSION}.onnx data/model/model.onnx

ENTRYPOINT ["python", "/adois/src/main.py", "/config.yaml"]
